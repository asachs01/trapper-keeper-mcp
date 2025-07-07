"""Integration tests for MCP tools."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest
import pytest_asyncio

from trapper_keeper.mcp.tools import (
    ExtractTool,
    AnalyzeTool,
    OrganizeTool,
    ValidateTool,
    ReferenceTool,
)
from trapper_keeper.core.types import (
    Document,
    DocumentType,
    ExtractedContent,
    ExtractionCategory,
    ProcessingConfig,
    OrganizationConfig,
)


class TestExtractTool:
    """Integration tests for ExtractTool."""
    
    @pytest_asyncio.fixture
    async def tool(self, temp_dir):
        """Create an extract tool."""
        config = ProcessingConfig()
        tool = ExtractTool(config)
        yield tool
    
    @pytest.mark.asyncio
    async def test_extract_from_file(self, tool, temp_dir, sample_markdown_content):
        """Test extracting content from a file."""
        # Create test file
        test_file = temp_dir / "test.md"
        test_file.write_text(sample_markdown_content)
        
        # Extract content
        result = await tool.execute(path=str(test_file))
        
        assert result["success"] is True
        assert "extracted_content" in result
        assert len(result["extracted_content"]) > 0
        
        # Check extracted categories
        categories = {item["category"] for item in result["extracted_content"]}
        assert "🏗️ Architecture" in categories
        assert "🗄️ Database" in categories
        assert "🔐 Security" in categories
    
    @pytest.mark.asyncio
    async def test_extract_with_category_filter(self, tool, temp_dir, sample_markdown_content):
        """Test extracting specific categories."""
        test_file = temp_dir / "test.md"
        test_file.write_text(sample_markdown_content)
        
        # Extract only security content
        result = await tool.execute(
            path=str(test_file),
            categories=["🔐 Security"]
        )
        
        assert result["success"] is True
        extracted = result["extracted_content"]
        
        # Should only have security content
        assert all(item["category"] == "🔐 Security" for item in extracted)
        assert len(extracted) > 0
    
    @pytest.mark.asyncio
    async def test_extract_from_content(self, tool):
        """Test extracting from direct content."""
        content = """# API Design
        
        REST API endpoints:
        - GET /users
        - POST /users
        - PUT /users/:id
        """
        
        result = await tool.execute(content=content)
        
        assert result["success"] is True
        assert len(result["extracted_content"]) > 0
        
        # Should detect API category
        categories = {item["category"] for item in result["extracted_content"]}
        assert "🌐 API" in categories
    
    @pytest.mark.asyncio
    async def test_extract_error_handling(self, tool):
        """Test error handling in extraction."""
        # Non-existent file
        result = await tool.execute(path="/nonexistent/file.md")
        
        assert result["success"] is False
        assert "error" in result
        assert "extracted_content" in result
        assert len(result["extracted_content"]) == 0
    
    @pytest.mark.asyncio
    async def test_extract_with_min_importance(self, tool, temp_dir):
        """Test filtering by minimum importance."""
        content = """# Notes
        
        ## Critical Security Issue
        SQL injection vulnerability found!
        
        ## Minor UI Fix
        Button color adjustment needed.
        """
        
        test_file = temp_dir / "test.md"
        test_file.write_text(content)
        
        # Extract with high importance threshold
        result = await tool.execute(
            path=str(test_file),
            min_importance=0.8
        )
        
        extracted = result["extracted_content"]
        
        # Should only include high importance items
        assert all(item["importance"] >= 0.8 for item in extracted)
        assert any("SQL injection" in item["content"] for item in extracted)
        assert not any("Button color" in item["content"] for item in extracted)


class TestAnalyzeTool:
    """Integration tests for AnalyzeTool."""
    
    @pytest_asyncio.fixture
    async def tool(self):
        """Create an analyze tool."""
        tool = AnalyzeTool()
        yield tool
    
    @pytest.mark.asyncio
    async def test_analyze_directory(self, tool, temp_dir, create_test_files):
        """Test analyzing a directory of files."""
        # Create test files
        files = [
            ("doc1.md", "# Architecture\n\nMicroservices design"),
            ("doc2.md", "# Security\n\nAuthentication setup"),
            ("doc3.md", "# Database\n\nSchema design"),
            ("readme.txt", "Setup instructions"),
        ]
        create_test_files(files)
        
        result = await tool.execute(path=str(temp_dir))
        
        assert result["success"] is True
        assert "analysis" in result
        
        analysis = result["analysis"]
        assert analysis["total_files"] == 4
        assert analysis["total_documents"] == 3  # Only .md files
        assert "categories" in analysis
        assert "file_types" in analysis
    
    @pytest.mark.asyncio
    async def test_analyze_with_patterns(self, tool, temp_dir, create_test_files):
        """Test analyzing with file patterns."""
        files = [
            ("test1.md", "Content 1"),
            ("test2.txt", "Content 2"),
            ("ignore.log", "Log content"),
        ]
        create_test_files(files)
        
        # Analyze only markdown files
        result = await tool.execute(
            path=str(temp_dir),
            patterns=["*.md"]
        )
        
        analysis = result["analysis"]
        assert analysis["total_files"] == 1
        assert analysis["total_documents"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_extracted_content(self, tool, temp_dir, create_test_files):
        """Test analyzing previously extracted content."""
        # Create files with varied content
        files = [
            ("api.md", "# API Documentation\n\nREST endpoints"),
            ("db.md", "# Database Schema\n\nTables and relations"),
            ("security.md", "# Security Guide\n\nBest practices"),
        ]
        create_test_files(files)
        
        result = await tool.execute(
            path=str(temp_dir),
            analyze_extracted=True
        )
        
        analysis = result["analysis"]
        assert "extracted_content_stats" in analysis
        stats = analysis["extracted_content_stats"]
        assert "total_extracted" in stats
        assert "by_category" in stats
        assert "importance_distribution" in stats


class TestOrganizeTool:
    """Integration tests for OrganizeTool."""
    
    @pytest_asyncio.fixture
    async def tool(self, temp_dir):
        """Create an organize tool."""
        config = OrganizationConfig(
            output_dir=temp_dir / "organized",
            group_by_category=True,
            create_index=True,
        )
        tool = OrganizeTool(config)
        yield tool
    
    @pytest.mark.asyncio
    async def test_organize_extracted_content(self, tool, temp_dir, sample_extracted_content):
        """Test organizing extracted content."""
        # Mock extraction results
        extraction_results = {
            "doc1.md": sample_extracted_content[:2],
            "doc2.md": sample_extracted_content[2:],
        }
        
        with patch.object(tool, '_load_extracted_content', return_value=extraction_results):
            result = await tool.execute(
                input_path=str(temp_dir),
                output_path=str(temp_dir / "organized")
            )
        
        assert result["success"] is True
        assert "organized_files" in result
        
        # Check output structure
        output_dir = temp_dir / "organized"
        assert output_dir.exists()
        
        # Should have category directories
        assert (output_dir / "Architecture").exists()
        assert (output_dir / "Database").exists()
        assert (output_dir / "Security").exists()
        
        # Should have index file
        assert (output_dir / "index.md").exists()
    
    @pytest.mark.asyncio
    async def test_organize_by_document(self, tool, temp_dir, sample_extracted_content):
        """Test organizing by document instead of category."""
        tool._config.group_by_category = False
        tool._config.group_by_document = True
        
        extraction_results = {
            "doc1.md": sample_extracted_content[:2],
            "doc2.md": sample_extracted_content[2:],
        }
        
        with patch.object(tool, '_load_extracted_content', return_value=extraction_results):
            result = await tool.execute(
                input_path=str(temp_dir),
                output_path=str(temp_dir / "organized")
            )
        
        assert result["success"] is True
        
        # Should have document directories
        output_dir = temp_dir / "organized"
        assert (output_dir / "doc1").exists()
        assert (output_dir / "doc2").exists()
    
    @pytest.mark.asyncio
    async def test_organize_with_template(self, tool, temp_dir):
        """Test organizing with custom template."""
        template = """# {title}
        
Category: {category}
Importance: {importance}

{content}
"""
        
        tool._config.template = template
        
        extraction_results = {
            "doc1.md": [
                ExtractedContent(
                    id="1",
                    document_id="doc1",
                    category=ExtractionCategory.API,
                    title="API Design",
                    content="REST endpoints",
                    importance=0.8,
                )
            ]
        }
        
        with patch.object(tool, '_load_extracted_content', return_value=extraction_results):
            result = await tool.execute(
                input_path=str(temp_dir),
                output_path=str(temp_dir / "organized")
            )
        
        assert result["success"] is True
        
        # Check formatted output
        api_file = temp_dir / "organized" / "API" / "api_design.md"
        if api_file.exists():
            content = api_file.read_text()
            assert "Category: 🌐 API" in content
            assert "Importance: 0.8" in content


class TestValidateTool:
    """Integration tests for ValidateTool."""
    
    @pytest_asyncio.fixture
    async def tool(self):
        """Create a validate tool."""
        tool = ValidateTool()
        yield tool
    
    @pytest.mark.asyncio
    async def test_validate_markdown_files(self, tool, temp_dir, create_test_files):
        """Test validating markdown files."""
        files = [
            ("valid.md", "# Valid Markdown\n\nContent here."),
            ("invalid.md", "# Unclosed code block\n\n```python\nno closing"),
            ("empty.md", ""),
        ]
        create_test_files(files)
        
        result = await tool.execute(path=str(temp_dir))
        
        assert result["success"] is True
        assert "validation_results" in result
        
        results = result["validation_results"]
        assert len(results) == 3
        
        # Check individual results
        valid_result = next(r for r in results if r["file"] == "valid.md")
        assert valid_result["valid"] is True
        assert len(valid_result["issues"]) == 0
        
        invalid_result = next(r for r in results if r["file"] == "invalid.md")
        assert len(invalid_result["issues"]) > 0
    
    @pytest.mark.asyncio
    async def test_validate_with_rules(self, tool, temp_dir, create_test_files):
        """Test validation with custom rules."""
        files = [
            ("doc1.md", "# Short\n\nVery brief content."),
            ("doc2.md", "# " + "A" * 100 + "\n\nLong title"),
        ]
        create_test_files(files)
        
        # Custom validation rules
        rules = {
            "min_content_length": 50,
            "max_title_length": 50,
            "required_sections": ["Introduction", "Conclusion"],
        }
        
        result = await tool.execute(
            path=str(temp_dir),
            rules=rules
        )
        
        results = result["validation_results"]
        
        # Both should have issues
        for r in results:
            assert len(r["issues"]) > 0


class TestReferenceTool:
    """Integration tests for ReferenceTool."""
    
    @pytest_asyncio.fixture
    async def tool(self):
        """Create a reference tool."""
        tool = ReferenceTool()
        yield tool
    
    @pytest.mark.asyncio
    async def test_generate_references(self, tool, temp_dir, create_test_files):
        """Test generating references between documents."""
        files = [
            ("api.md", "# API\n\nSee [Database Schema](db.md) for details."),
            ("db.md", "# Database\n\nUsed by [API](api.md)."),
            ("auth.md", "# Auth\n\nUses [Database](db.md) and [API](api.md)."),
        ]
        create_test_files(files)
        
        result = await tool.execute(path=str(temp_dir))
        
        assert result["success"] is True
        assert "references" in result
        
        refs = result["references"]
        assert "cross_references" in refs
        assert "reference_graph" in refs
        
        # Check cross references
        cross_refs = refs["cross_references"]
        assert "api.md" in cross_refs
        assert "db.md" in cross_refs["api.md"]["references"]
    
    @pytest.mark.asyncio
    async def test_generate_reference_graph(self, tool, temp_dir, create_test_files):
        """Test generating reference graph visualization."""
        files = [
            ("a.md", "[Link to B](b.md)"),
            ("b.md", "[Link to C](c.md)"),
            ("c.md", "[Link to A](a.md)"),  # Circular reference
        ]
        create_test_files(files)
        
        result = await tool.execute(
            path=str(temp_dir),
            output_format="graph"
        )
        
        assert result["success"] is True
        
        graph = result["references"]["reference_graph"]
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 3
        assert len(graph["edges"]) == 3
    
    @pytest.mark.asyncio
    async def test_detect_broken_references(self, tool, temp_dir, create_test_files):
        """Test detecting broken references."""
        files = [
            ("doc1.md", "[Valid link](doc2.md) and [broken link](missing.md)"),
            ("doc2.md", "Target document"),
        ]
        create_test_files(files)
        
        result = await tool.execute(
            path=str(temp_dir),
            check_broken=True
        )
        
        refs = result["references"]
        assert "broken_references" in refs
        
        broken = refs["broken_references"]
        assert len(broken) > 0
        assert any(ref["target"] == "missing.md" for ref in broken)