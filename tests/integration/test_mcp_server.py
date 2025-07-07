"""Integration tests for MCP server."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.trapper_keeper.mcp.server import (
    TrapperKeeperMCP,
    organize_documentation,
    extract_content,
    create_reference,
    validate_structure,
    analyze_document,
)
from src.trapper_keeper.core.types import TrapperKeeperConfig


@pytest.fixture
async def mcp_server():
    """Create a test MCP server instance."""
    config = TrapperKeeperConfig(
        organization={"output_dir": Path("test_output")}
    )
    server = TrapperKeeperMCP(config)
    await server.initialize()
    yield server
    await server.shutdown()


@pytest.fixture
def sample_claude_md(tmp_path):
    """Create a sample CLAUDE.md file for testing."""
    content = """# Claude Code Configuration

## Architecture

This is the system architecture section.
It contains important design decisions.

## Security

Critical security configurations:
- Authentication setup
- Authorization rules
- Encryption requirements

## API Endpoints

### REST API
- GET /api/users
- POST /api/users
- PUT /api/users/:id

### GraphQL API
```graphql
type User {
  id: ID!
  name: String!
  email: String!
}
```

## Testing

Test configuration and strategies.

### Unit Tests
Run with: `npm test`

### Integration Tests
Run with: `npm run test:integration`

## Dependencies

- express: ^4.18.0
- graphql: ^16.0.0
- jest: ^29.0.0
"""
    
    file_path = tmp_path / "CLAUDE.md"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def test_output_dir(tmp_path):
    """Create a test output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestOrganizeDocumentation:
    """Test organize_documentation tool."""
    
    @pytest.mark.asyncio
    async def test_organize_dry_run(self, mcp_server, sample_claude_md, test_output_dir):
        """Test organize documentation in dry run mode."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await organize_documentation(
                file_path=str(sample_claude_md),
                dry_run=True,
                output_dir=str(test_output_dir)
            )
            
        assert result["success"]
        assert result["dry_run"]
        assert len(result["suggestions"]) > 0
        assert result["extracted_count"] == 0  # Nothing extracted in dry run
        assert len(result["categories_found"]) > 0
        
        # Check suggestions
        categories = {s["category"] for s in result["suggestions"]}
        assert "🏗️ Architecture" in categories
        assert "🔐 Security" in categories
        
    @pytest.mark.asyncio
    async def test_organize_with_extraction(self, mcp_server, sample_claude_md, test_output_dir):
        """Test organize documentation with actual extraction."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await organize_documentation(
                file_path=str(sample_claude_md),
                dry_run=False,
                output_dir=str(test_output_dir),
                min_importance=0.3
            )
            
        assert result["success"]
        assert not result["dry_run"]
        assert result["extracted_count"] > 0
        assert len(result["output_files"]) > 0
        
    @pytest.mark.asyncio
    async def test_organize_specific_categories(self, mcp_server, sample_claude_md, test_output_dir):
        """Test organizing specific categories only."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await organize_documentation(
                file_path=str(sample_claude_md),
                dry_run=True,
                categories=["🔐 Security", "🌐 API"]
            )
            
        assert result["success"]
        suggestions = result["suggestions"]
        
        # All suggestions should be from requested categories
        for suggestion in suggestions:
            assert suggestion["category"] in ["🔐 Security", "🌐 API"]


class TestExtractContent:
    """Test extract_content tool."""
    
    @pytest.mark.asyncio
    async def test_extract_by_pattern(self, mcp_server, sample_claude_md, test_output_dir):
        """Test extracting content by regex pattern."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await extract_content(
                file_path=str(sample_claude_md),
                patterns=["security", "auth"],
                dry_run=True
            )
            
        assert result["success"]
        assert result["dry_run"]
        assert result["total_extracted"] > 0
        
        # Check extracted sections contain security content
        for section in result["extracted_sections"]:
            content_lower = section["content"].lower()
            assert "security" in content_lower or "auth" in content_lower
            
    @pytest.mark.asyncio
    async def test_extract_with_context(self, mcp_server, sample_claude_md):
        """Test extracting content with surrounding context."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await extract_content(
                file_path=str(sample_claude_md),
                patterns=["API"],
                preserve_context=True,
                dry_run=True
            )
            
        assert result["success"]
        
        # Check that context is preserved
        for section in result["extracted_sections"]:
            if section.get("context_before") or section.get("context_after"):
                assert True
                break
        else:
            pytest.fail("No context found in extracted sections")


class TestCreateReference:
    """Test create_reference tool."""
    
    @pytest.mark.asyncio
    async def test_create_markdown_references(self, mcp_server, sample_claude_md, test_output_dir):
        """Test creating markdown references."""
        # Create some extracted files
        extracted_files = []
        for i in range(3):
            file_path = test_output_dir / f"extracted_{i}.md"
            file_path.write_text(f"# Extracted Content {i}\n\nCategory: Testing")
            extracted_files.append(str(file_path))
            
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await create_reference(
                source_file=str(sample_claude_md),
                extracted_files=extracted_files,
                reference_format="markdown",
                create_backlinks=True
            )
            
        assert result["success"]
        assert result["total_references"] == 3
        assert len(result["references_created"]) == 3
        
        # Check reference format
        for ref in result["references_created"]:
            assert ref["link_format"].startswith("\n> **Extracted**:")
            
    @pytest.mark.asyncio
    async def test_create_index_references(self, mcp_server, sample_claude_md, test_output_dir):
        """Test creating index-style references."""
        extracted_file = test_output_dir / "extracted.md"
        extracted_file.write_text("# Security Config\n\nCategory: Security")
        
        index_file = test_output_dir / "index.md"
        
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await create_reference(
                source_file=str(sample_claude_md),
                extracted_files=[str(extracted_file)],
                reference_format="index",
                index_file=str(index_file),
                update_source=False
            )
            
        assert result["success"]
        assert not result["source_updated"]  # We disabled source update
        assert result["index_updated"] or not index_file.exists()  # May not create if no refs


class TestValidateStructure:
    """Test validate_structure tool."""
    
    @pytest.mark.asyncio
    async def test_validate_clean_structure(self, mcp_server, test_output_dir):
        """Test validating a clean documentation structure."""
        # Create a simple structure
        doc1 = test_output_dir / "doc1.md"
        doc1.write_text("# Doc 1\n\nContent here.")
        
        doc2 = test_output_dir / "doc2.md"
        doc2.write_text("# Doc 2\n\nLink to [Doc 1](doc1.md)")
        
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await validate_structure(
                root_dir=str(test_output_dir),
                check_references=True,
                check_orphans=True
            )
            
        assert result["success"]
        assert result["total_files_checked"] == 2
        assert result["valid_files"] == 2
        assert len(result["broken_references"]) == 0
        
    @pytest.mark.asyncio
    async def test_validate_broken_references(self, mcp_server, test_output_dir):
        """Test detecting broken references."""
        doc = test_output_dir / "doc.md"
        doc.write_text("# Doc\n\nLink to [Missing](missing.md)")
        
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await validate_structure(
                root_dir=str(test_output_dir),
                check_references=True
            )
            
        assert result["success"]
        assert len(result["broken_references"]) == 1
        assert result["broken_references"][0]["target"] == "missing.md"
        
    @pytest.mark.asyncio
    async def test_validate_orphaned_files(self, mcp_server, test_output_dir):
        """Test detecting orphaned files."""
        # Create files where one is not referenced
        index = test_output_dir / "index.md"
        index.write_text("# Index\n\nLink to [Doc 1](doc1.md)")
        
        doc1 = test_output_dir / "doc1.md"
        doc1.write_text("# Doc 1")
        
        orphan = test_output_dir / "orphan.md"
        orphan.write_text("# Orphaned Doc")
        
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await validate_structure(
                root_dir=str(test_output_dir),
                check_orphans=True
            )
            
        assert result["success"]
        assert str(orphan) in result["orphaned_files"]


class TestAnalyzeDocument:
    """Test analyze_document tool."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_statistics(self, mcp_server, sample_claude_md):
        """Test analyzing document with statistics."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await analyze_document(
                file_path=str(sample_claude_md),
                include_statistics=True,
                include_growth=False,
                include_recommendations=False
            )
            
        assert result["success"]
        assert result["statistics"] is not None
        
        stats = result["statistics"]
        assert stats["total_lines"] > 0
        assert stats["total_sections"] > 0
        assert stats["code_block_count"] > 0  # We have GraphQL code block
        
    @pytest.mark.asyncio
    async def test_analyze_category_distribution(self, mcp_server, sample_claude_md):
        """Test analyzing category distribution."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await analyze_document(
                file_path=str(sample_claude_md),
                include_statistics=False,
                include_growth=False,
                include_recommendations=False
            )
            
        assert result["success"]
        assert len(result["category_distribution"]) > 0
        
        # Check we found multiple categories
        categories = {dist["category"] for dist in result["category_distribution"]}
        assert len(categories) >= 3
        
    @pytest.mark.asyncio
    async def test_analyze_with_recommendations(self, mcp_server, sample_claude_md):
        """Test analyzing with extraction recommendations."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await analyze_document(
                file_path=str(sample_claude_md),
                include_statistics=True,
                include_recommendations=True
            )
            
        assert result["success"]
        assert len(result["recommendations"]) > 0
        
        # Check recommendation structure
        for rec in result["recommendations"]:
            assert "section_id" in rec
            assert "category" in rec
            assert "priority" in rec
            assert rec["priority"] in ["high", "medium", "low"]
            
    @pytest.mark.asyncio
    async def test_analyze_insights(self, mcp_server, sample_claude_md):
        """Test that analysis provides insights."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await analyze_document(
                file_path=str(sample_claude_md),
                include_statistics=True,
                include_growth=True,
                include_recommendations=True
            )
            
        assert result["success"]
        assert len(result["insights"]) > 0
        
        # Insights should be meaningful strings
        for insight in result["insights"]:
            assert isinstance(insight, str)
            assert len(insight) > 10  # Not empty or trivial


class TestMCPServerLifecycle:
    """Test MCP server lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initialization."""
        config = TrapperKeeperConfig()
        server = TrapperKeeperMCP(config)
        
        # Server should not be initialized yet
        assert server.orchestrator is None
        
        await server.initialize()
        
        # After initialization
        assert server.orchestrator is not None
        assert server.organize_tool is not None
        assert server.extract_tool is not None
        assert server.reference_tool is not None
        assert server.validate_tool is not None
        assert server.analyze_tool is not None
        
        await server.shutdown()
        
    @pytest.mark.asyncio
    async def test_server_shutdown(self):
        """Test server shutdown."""
        config = TrapperKeeperConfig()
        server = TrapperKeeperMCP(config)
        await server.initialize()
        
        # Add a mock watcher
        mock_watcher = AsyncMock()
        server.watchers["test_dir"] = mock_watcher
        
        await server.shutdown()
        
        # Watcher should be stopped
        mock_watcher.stop.assert_called_once()
        assert len(server.watchers) == 0


class TestErrorHandling:
    """Test error handling in MCP tools."""
    
    @pytest.mark.asyncio
    async def test_organize_nonexistent_file(self, mcp_server):
        """Test organizing a non-existent file."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await organize_documentation(
                file_path="/nonexistent/file.md",
                dry_run=True
            )
            
        assert not result["success"]
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()
        
    @pytest.mark.asyncio
    async def test_validate_nonexistent_directory(self, mcp_server):
        """Test validating a non-existent directory."""
        with patch('src.trapper_keeper.mcp.server.get_server', return_value=mcp_server):
            result = await validate_structure(
                root_dir="/nonexistent/directory"
            )
            
        assert not result["success"]
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])