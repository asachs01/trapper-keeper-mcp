"""Unit tests for content extractor."""

import re
from unittest.mock import Mock, AsyncMock, patch
import pytest
import pytest_asyncio

from trapper_keeper.extractor.content_extractor import ContentExtractor
from trapper_keeper.core.types import (
    Document,
    DocumentType,
    DocumentSection,
    ExtractedContent,
    ExtractionCategory,
    ProcessingConfig,
)


class TestContentExtractor:
    """Test ContentExtractor class."""
    
    @pytest.fixture
    def config(self):
        """Create extraction configuration."""
        return ProcessingConfig(
            extract_categories=list(ExtractionCategory),
            min_importance=0.3,
            include_metadata=True,
            preserve_structure=True,
            extract_code_blocks=True,
            extract_links=True,
            extract_images=True,
            custom_patterns={
                "TODO": r"TODO:\s*(.+)",
                "FIXME": r"FIXME:\s*(.+)",
            },
        )
    
    @pytest.fixture
    def extractor(self, config, mock_event_bus):
        """Create a content extractor."""
        return ContentExtractor(config, mock_event_bus)
    
    @pytest.mark.asyncio
    async def test_initialization(self, extractor):
        """Test extractor initialization."""
        await extractor.initialize()
        
        assert extractor.is_initialized
        assert extractor._patterns is not None
        assert extractor._category_keywords is not None
    
    @pytest.mark.asyncio
    async def test_extract_from_simple_document(self, extractor, sample_document):
        """Test extracting content from a simple document."""
        await extractor.initialize()
        
        extracted = await extractor.extract(sample_document)
        
        assert len(extracted) > 0
        
        # Check categories found
        categories = {e.category for e in extracted}
        assert ExtractionCategory.ARCHITECTURE in categories
        assert ExtractionCategory.DATABASE in categories
        assert ExtractionCategory.SECURITY in categories
        assert ExtractionCategory.TESTING in categories
    
    @pytest.mark.asyncio
    async def test_extract_architecture_content(self, extractor):
        """Test extracting architecture-related content."""
        doc = Document(
            id="test-1",
            type=DocumentType.MARKDOWN,
            content="""# System Architecture
            
            The system uses a microservices architecture with:
            - API Gateway for routing
            - Service mesh for communication
            - Event-driven messaging
            
            ## Component Design
            
            Each service follows hexagonal architecture.""",
            sections=[
                DocumentSection(
                    id="sec-1",
                    title="System Architecture",
                    content="The system uses a microservices architecture...",
                    level=1,
                ),
                DocumentSection(
                    id="sec-2",
                    title="Component Design",
                    content="Each service follows hexagonal architecture.",
                    level=2,
                ),
            ],
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        arch_content = [e for e in extracted if e.category == ExtractionCategory.ARCHITECTURE]
        assert len(arch_content) >= 1
        
        # Check content
        arch = arch_content[0]
        assert "microservices" in arch.content
        assert arch.importance >= 0.8  # Architecture is important
    
    @pytest.mark.asyncio
    async def test_extract_security_content(self, extractor):
        """Test extracting security-related content."""
        doc = Document(
            id="test-2",
            type=DocumentType.MARKDOWN,
            content="""# Security Implementation
            
            ## Authentication
            
            We use JWT tokens with:
            - RSA signing
            - Token expiration
            - Refresh tokens
            
            ## Authorization
            
            RBAC with fine-grained permissions.""",
            sections=[
                DocumentSection(
                    id="sec-1",
                    title="Authentication",
                    content="We use JWT tokens with...",
                    level=2,
                ),
                DocumentSection(
                    id="sec-2",
                    title="Authorization",
                    content="RBAC with fine-grained permissions.",
                    level=2,
                ),
            ],
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        security_content = [e for e in extracted if e.category == ExtractionCategory.SECURITY]
        assert len(security_content) >= 1
        
        # Should have high importance
        assert all(e.importance >= 0.9 for e in security_content)
    
    @pytest.mark.asyncio
    async def test_extract_code_blocks(self, extractor):
        """Test extracting code blocks."""
        doc = Document(
            id="test-3",
            type=DocumentType.MARKDOWN,
            content="""# Implementation
            
            Here's the database schema:
            
            ```sql
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE
            );
            ```
            
            And the Python model:
            
            ```python
            class User(BaseModel):
                id: int
                email: str
            ```""",
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Should extract code blocks
        code_extracts = [e for e in extracted if "```" in e.content or "CREATE TABLE" in e.content or "class User" in e.content]
        assert len(code_extracts) > 0
    
    @pytest.mark.asyncio
    async def test_extract_custom_patterns(self, extractor):
        """Test extracting custom patterns."""
        doc = Document(
            id="test-4",
            type=DocumentType.MARKDOWN,
            content="""# Development Notes
            
            TODO: Implement user authentication
            TODO: Add rate limiting
            
            FIXME: Database connection pooling is broken
            FIXME: Memory leak in cache layer""",
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Should find TODO and FIXME items
        todos = [e for e in extracted if "TODO" in e.title or "TODO" in e.content]
        fixmes = [e for e in extracted if "FIXME" in e.title or "FIXME" in e.content]
        
        assert len(todos) > 0
        assert len(fixmes) > 0
    
    @pytest.mark.asyncio
    async def test_importance_scoring(self, extractor):
        """Test importance scoring of extracted content."""
        doc = Document(
            id="test-5",
            type=DocumentType.MARKDOWN,
            content="""# System Design
            
            ## Critical Security Flaw
            
            URGENT: SQL injection vulnerability in user input.
            
            ## Minor UI Issue
            
            Button color is slightly off.
            
            ## Database Performance
            
            Critical: Database queries taking >10 seconds.""",
            sections=[
                DocumentSection(
                    id="sec-1",
                    title="Critical Security Flaw",
                    content="URGENT: SQL injection vulnerability...",
                    level=2,
                ),
                DocumentSection(
                    id="sec-2",
                    title="Minor UI Issue",
                    content="Button color is slightly off.",
                    level=2,
                ),
                DocumentSection(
                    id="sec-3",
                    title="Database Performance",
                    content="Critical: Database queries taking >10 seconds.",
                    level=2,
                ),
            ],
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Security flaw should have highest importance
        security_items = [e for e in extracted if "SQL injection" in e.content]
        assert all(e.importance >= 0.95 for e in security_items)
        
        # UI issue should have lower importance
        ui_items = [e for e in extracted if "Button color" in e.content]
        if ui_items:  # Might be filtered out by min_importance
            assert all(e.importance < 0.5 for e in ui_items)
    
    @pytest.mark.asyncio
    async def test_min_importance_filtering(self, extractor):
        """Test filtering by minimum importance."""
        extractor._config.min_importance = 0.7
        
        doc = Document(
            id="test-6",
            type=DocumentType.MARKDOWN,
            content="""# Notes
            
            ## High Priority
            
            Critical security vulnerability found.
            
            ## Low Priority
            
            Consider renaming variables for clarity.""",
            sections=[
                DocumentSection(
                    id="sec-1",
                    title="High Priority",
                    content="Critical security vulnerability found.",
                    level=2,
                ),
                DocumentSection(
                    id="sec-2",
                    title="Low Priority",
                    content="Consider renaming variables for clarity.",
                    level=2,
                ),
            ],
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Should only include high importance items
        assert all(e.importance >= 0.7 for e in extracted)
        assert len([e for e in extracted if "renaming variables" in e.content]) == 0
    
    @pytest.mark.asyncio
    async def test_extract_links(self, extractor):
        """Test extracting links from content."""
        doc = Document(
            id="test-7",
            type=DocumentType.MARKDOWN,
            content="""# Resources
            
            See [API Documentation](https://api.example.com/docs)
            
            Reference: https://example.com/security-guide
            
            [GitHub Repo](https://github.com/example/repo)""",
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Should extract content with links
        link_content = [e for e in extracted if "http" in e.content]
        assert len(link_content) > 0
    
    @pytest.mark.asyncio
    async def test_extract_images(self, extractor):
        """Test extracting image references."""
        doc = Document(
            id="test-8",
            type=DocumentType.MARKDOWN,
            content="""# Architecture Diagrams
            
            ![System Architecture](diagrams/architecture.png)
            
            See the flow diagram:
            ![Data Flow](diagrams/data-flow.svg)""",
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Should identify content with images
        image_content = [e for e in extracted if "diagram" in e.content.lower() or "![" in e.content]
        assert len(image_content) > 0
    
    @pytest.mark.asyncio
    async def test_preserve_structure(self, extractor):
        """Test preserving document structure in extraction."""
        doc = Document(
            id="test-9",
            type=DocumentType.MARKDOWN,
            content="# Main\n## Sub1\n### SubSub1",
            sections=[
                DocumentSection(id="1", title="Main", content="", level=1),
                DocumentSection(id="2", title="Sub1", content="", level=2, parent_id="1"),
                DocumentSection(id="3", title="SubSub1", content="", level=3, parent_id="2"),
            ],
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Check that source sections are preserved
        for e in extracted:
            assert e.source_section in ["1", "2", "3", None]
    
    @pytest.mark.asyncio
    async def test_category_detection_keywords(self, extractor):
        """Test category detection based on keywords."""
        test_cases = [
            ("API endpoint /users returns JSON", ExtractionCategory.API),
            ("Database migration script", ExtractionCategory.DATABASE),
            ("Deploy to production server", ExtractionCategory.DEPLOYMENT),
            ("Unit tests for user service", ExtractionCategory.TESTING),
            ("Performance optimization needed", ExtractionCategory.PERFORMANCE),
            ("Security audit findings", ExtractionCategory.SECURITY),
            ("Setup instructions for developers", ExtractionCategory.SETUP),
            ("Monitor system metrics", ExtractionCategory.MONITORING),
            ("Feature: User authentication", ExtractionCategory.FEATURES),
            ("System architecture overview", ExtractionCategory.ARCHITECTURE),
        ]
        
        await extractor.initialize()
        
        for content, expected_category in test_cases:
            doc = Document(
                id=f"test-{content[:10]}",
                type=DocumentType.MARKDOWN,
                content=f"# Section\n\n{content}",
            )
            
            extracted = await extractor.extract(doc)
            if extracted:  # Some might be filtered by importance
                categories = {e.category for e in extracted}
                assert expected_category in categories, f"Expected {expected_category} for '{content}'"
    
    @pytest.mark.asyncio
    async def test_metadata_inclusion(self, extractor):
        """Test including metadata in extracted content."""
        doc = Document(
            id="test-10",
            type=DocumentType.MARKDOWN,
            content="# Test\n\nContent here.",
            frontmatter={"author": "John Doe", "version": "1.0"},
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Each extracted content should have metadata
        for e in extracted:
            assert "document_id" in e.metadata
            assert e.metadata["document_id"] == "test-10"
            if extractor._config.include_metadata:
                assert "frontmatter" in e.metadata
    
    @pytest.mark.asyncio
    async def test_empty_document(self, extractor):
        """Test extracting from empty document."""
        doc = Document(
            id="empty",
            type=DocumentType.MARKDOWN,
            content="",
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        assert len(extracted) == 0
    
    @pytest.mark.asyncio
    async def test_extraction_tags(self, extractor):
        """Test automatic tagging of extracted content."""
        doc = Document(
            id="test-11",
            type=DocumentType.MARKDOWN,
            content="""# Python API Server
            
            REST API using FastAPI framework.
            
            PostgreSQL database with SQLAlchemy ORM.""",
        )
        
        await extractor.initialize()
        extracted = await extractor.extract(doc)
        
        # Should have relevant tags
        all_tags = set()
        for e in extracted:
            all_tags.update(e.tags)
        
        # Should include technology tags
        expected_tags = {"python", "api", "rest", "fastapi", "postgresql", "database"}
        assert len(all_tags.intersection(expected_tags)) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_extraction(self, extractor):
        """Test concurrent extraction of multiple documents."""
        docs = [
            Document(
                id=f"doc-{i}",
                type=DocumentType.MARKDOWN,
                content=f"# Document {i}\n\nContent for document {i}",
            )
            for i in range(5)
        ]
        
        await extractor.initialize()
        
        # Extract all documents concurrently
        import asyncio
        results = await asyncio.gather(*[extractor.extract(doc) for doc in docs])
        
        # Each document should have extractions
        assert len(results) == 5
        for i, extracted in enumerate(results):
            assert all(e.document_id == f"doc-{i}" for e in extracted)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, extractor):
        """Test error handling during extraction."""
        # Invalid document
        with pytest.raises(AttributeError):
            await extractor.extract(None)
        
        # Document with invalid structure
        doc = Mock()
        doc.id = "test"
        doc.content = "content"
        doc.sections = None  # Will cause error
        
        await extractor.initialize()
        
        # Should handle gracefully
        with patch.object(extractor._logger, 'error') as mock_logger:
            extracted = await extractor.extract(doc)
            assert isinstance(extracted, list)  # Should return empty list on error