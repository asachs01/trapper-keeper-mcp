"""Unit tests for Markdown document parser."""

import uuid
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest
import pytest_asyncio

from trapper_keeper.parser.markdown_parser import MarkdownParser
from trapper_keeper.core.types import (
    Document,
    DocumentType,
    DocumentSection,
    DocumentMetadata,
)


class TestMarkdownParser:
    """Test MarkdownParser class."""
    
    @pytest.fixture
    def parser(self, mock_event_bus):
        """Create a markdown parser."""
        return MarkdownParser(mock_event_bus)
    
    @pytest.mark.asyncio
    async def test_initialization(self, parser):
        """Test parser initialization."""
        await parser.initialize()
        
        assert parser.is_initialized
        assert parser._md is not None
        assert 'extra' in parser._md.Markdown_extensions
        assert 'tables' in parser._md.Markdown_extensions
        assert 'toc' in parser._md.Markdown_extensions
    
    @pytest.mark.asyncio
    async def test_parse_simple_markdown(self, parser):
        """Test parsing simple markdown content."""
        content = """# Title

This is a paragraph.

## Section 1

Content of section 1.

## Section 2

Content of section 2."""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        assert isinstance(doc, Document)
        assert doc.type == DocumentType.MARKDOWN
        assert doc.content == content
        assert len(doc.sections) == 3  # Title + 2 sections
        
        # Check sections
        assert doc.sections[0].title == "Title"
        assert doc.sections[0].level == 1
        assert doc.sections[1].title == "Section 1"
        assert doc.sections[1].level == 2
        assert doc.sections[2].title == "Section 2"
        assert doc.sections[2].level == 2
    
    @pytest.mark.asyncio
    async def test_parse_with_frontmatter(self, parser):
        """Test parsing markdown with frontmatter."""
        content = """---
title: Test Document
author: John Doe
date: 2024-01-01
tags:
  - test
  - sample
custom:
  field: value
---

# Main Content

This is the main content."""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Check frontmatter
        assert doc.frontmatter["title"] == "Test Document"
        assert doc.frontmatter["author"] == "John Doe"
        assert doc.frontmatter["date"] == "2024-01-01"
        assert doc.frontmatter["tags"] == ["test", "sample"]
        assert doc.frontmatter["custom"]["field"] == "value"
        
        # Check metadata populated from frontmatter
        assert doc.metadata.author == "John Doe"
        assert "test" in doc.metadata.tags
        assert "sample" in doc.metadata.tags
    
    @pytest.mark.asyncio
    async def test_parse_nested_sections(self, parser):
        """Test parsing markdown with nested sections."""
        content = """# Title

## Section 1

### Subsection 1.1

Content 1.1

### Subsection 1.2

Content 1.2

## Section 2

### Subsection 2.1

Content 2.1"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Check section hierarchy
        assert len(doc.sections) == 6  # All sections flat initially
        
        # Find main sections
        main_sections = [s for s in doc.sections if s.level == 1]
        assert len(main_sections) == 1
        assert main_sections[0].title == "Title"
        
        # Find level 2 sections
        level2_sections = [s for s in doc.sections if s.level == 2]
        assert len(level2_sections) == 2
        assert level2_sections[0].title == "Section 1"
        assert level2_sections[1].title == "Section 2"
        
        # Find level 3 sections
        level3_sections = [s for s in doc.sections if s.level == 3]
        assert len(level3_sections) == 3
        assert level3_sections[0].title == "Subsection 1.1"
        assert level3_sections[1].title == "Subsection 1.2"
        assert level3_sections[2].title == "Subsection 2.1"
    
    @pytest.mark.asyncio
    async def test_parse_with_code_blocks(self, parser):
        """Test parsing markdown with code blocks."""
        content = """# Code Examples

Here's some Python code:

```python
def hello_world():
    print("Hello, World!")
```

And some JavaScript:

```javascript
function helloWorld() {
    console.log("Hello, World!");
}
```"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Check that code blocks are preserved in content
        assert "```python" in doc.content
        assert "```javascript" in doc.content
        assert 'def hello_world():' in doc.content
        assert 'function helloWorld()' in doc.content
    
    @pytest.mark.asyncio
    async def test_parse_with_tables(self, parser):
        """Test parsing markdown with tables."""
        content = """# Table Example

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Tables should be preserved in content
        assert "| Column 1 | Column 2 | Column 3 |" in doc.content
        assert doc.sections[0].title == "Table Example"
    
    @pytest.mark.asyncio
    async def test_parse_with_lists(self, parser):
        """Test parsing markdown with lists."""
        content = """# Lists

## Unordered List

- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3

## Ordered List

1. First item
2. Second item
   1. Nested first
   2. Nested second
3. Third item"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Lists should be preserved
        assert "- Item 1" in doc.content
        assert "1. First item" in doc.content
        assert len(doc.sections) == 3  # Lists + 2 subsections
    
    @pytest.mark.asyncio
    async def test_parse_with_links_and_images(self, parser):
        """Test parsing markdown with links and images."""
        content = """# Links and Images

Here's a [link to Google](https://www.google.com).

And an image:

![Alt text](image.png)

And a reference-style link: [Reference][1]

[1]: https://example.com"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Links and images should be preserved
        assert "[link to Google](https://www.google.com)" in doc.content
        assert "![Alt text](image.png)" in doc.content
        assert "[Reference][1]" in doc.content
    
    @pytest.mark.asyncio
    async def test_parse_with_metadata(self, parser):
        """Test parsing with file metadata."""
        content = "# Simple Document\n\nContent here."
        path = Path("/test/document.md")
        
        await parser.initialize()
        doc = await parser.parse(content, path)
        
        # Check metadata
        assert doc.metadata.path == path
        assert doc.metadata.size == len(content)
    
    @pytest.mark.asyncio
    async def test_parse_empty_content(self, parser):
        """Test parsing empty content."""
        await parser.initialize()
        doc = await parser.parse("")
        
        assert doc.content == ""
        assert len(doc.sections) == 0
        assert doc.type == DocumentType.MARKDOWN
    
    @pytest.mark.asyncio
    async def test_parse_malformed_frontmatter(self, parser):
        """Test parsing with malformed frontmatter."""
        content = """---
title: Missing closing
author: John Doe

# Content

This is content."""
        
        await parser.initialize()
        # Should handle gracefully
        doc = await parser.parse(content)
        
        # Should treat as content without frontmatter
        assert len(doc.frontmatter) == 0
        assert "---" in doc.content
    
    @pytest.mark.asyncio
    async def test_section_content_extraction(self, parser):
        """Test extracting content for each section."""
        content = """# Title

Introduction paragraph.

## Section 1

Content for section 1.
More content here.

## Section 2

Content for section 2.

### Subsection 2.1

Subsection content."""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Check section contents
        title_section = next(s for s in doc.sections if s.title == "Title")
        assert "Introduction paragraph." in title_section.content
        
        section1 = next(s for s in doc.sections if s.title == "Section 1")
        assert "Content for section 1." in section1.content
        assert "More content here." in section1.content
        
        section2 = next(s for s in doc.sections if s.title == "Section 2")
        assert "Content for section 2." in section2.content
    
    @pytest.mark.asyncio
    async def test_parse_with_special_characters(self, parser):
        """Test parsing content with special characters."""
        content = """# Special Characters

This has **bold** and *italic* text.

Also `inline code` and ~~strikethrough~~.

Special chars: & < > " '"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Special characters should be preserved
        assert "**bold**" in doc.content
        assert "*italic*" in doc.content
        assert "`inline code`" in doc.content
        assert "~~strikethrough~~" in doc.content
        assert "& < > \" '" in doc.content
    
    @pytest.mark.asyncio
    async def test_parse_with_blockquotes(self, parser):
        """Test parsing markdown with blockquotes."""
        content = """# Quotes

> This is a blockquote
> with multiple lines

> > And a nested blockquote"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        assert "> This is a blockquote" in doc.content
        assert "> > And a nested blockquote" in doc.content
    
    @pytest.mark.asyncio
    async def test_parse_with_horizontal_rules(self, parser):
        """Test parsing markdown with horizontal rules."""
        content = """# Document

Section 1

---

Section 2

***

Section 3"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        assert "---" in doc.content
        assert "***" in doc.content
    
    @pytest.mark.asyncio
    async def test_unique_document_ids(self, parser):
        """Test that parsed documents get unique IDs."""
        content = "# Test"
        
        await parser.initialize()
        doc1 = await parser.parse(content)
        doc2 = await parser.parse(content)
        
        assert doc1.id != doc2.id
        assert doc1.id.startswith("doc-")
        assert doc2.id.startswith("doc-")
    
    @pytest.mark.asyncio
    async def test_unique_section_ids(self, parser):
        """Test that sections get unique IDs."""
        content = """# Section 1

## Subsection

# Section 1

## Subsection"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # All sections should have unique IDs
        section_ids = [s.id for s in doc.sections]
        assert len(section_ids) == len(set(section_ids))
        
        # All should start with "sec-"
        assert all(sid.startswith("sec-") for sid in section_ids)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, parser):
        """Test error handling in parser."""
        await parser.initialize()
        
        # Test with None
        with pytest.raises(TypeError):
            await parser.parse(None)
        
        # Test with non-string
        with pytest.raises(TypeError):
            await parser.parse(123)
    
    @pytest.mark.asyncio
    async def test_section_hierarchy_building(self, parser):
        """Test building proper section hierarchy."""
        content = """# Main

## Child 1

### Grandchild 1.1

## Child 2

### Grandchild 2.1

### Grandchild 2.2"""
        
        await parser.initialize()
        doc = await parser.parse(content)
        
        # Verify parent-child relationships are set
        main = next(s for s in doc.sections if s.title == "Main")
        child1 = next(s for s in doc.sections if s.title == "Child 1")
        child2 = next(s for s in doc.sections if s.title == "Child 2")
        grandchild11 = next(s for s in doc.sections if s.title == "Grandchild 1.1")
        grandchild21 = next(s for s in doc.sections if s.title == "Grandchild 2.1")
        grandchild22 = next(s for s in doc.sections if s.title == "Grandchild 2.2")
        
        # Check parent IDs
        assert child1.parent_id == main.id
        assert child2.parent_id == main.id
        assert grandchild11.parent_id == child1.id
        assert grandchild21.parent_id == child2.id
        assert grandchild22.parent_id == child2.id