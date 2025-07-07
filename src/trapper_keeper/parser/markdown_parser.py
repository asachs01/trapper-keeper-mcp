"""Markdown document parser."""

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import frontmatter
import markdown
from markdown.extensions.toc import TocExtension
import structlog

from ..core.base import Parser, EventBus
from ..core.types import Document, DocumentSection, DocumentType, DocumentMetadata

logger = structlog.get_logger()


class MarkdownParser(Parser):
    """Parser for Markdown documents."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("MarkdownParser", event_bus)
        self._md = markdown.Markdown(
            extensions=[
                'extra',
                'codehilite',
                'tables',
                'toc',
                'meta',
                'nl2br',
                'sane_lists',
            ]
        )

    async def _initialize(self) -> None:
        """Initialize the parser."""
        pass

    async def _start(self) -> None:
        """Start the parser."""
        pass

    async def _stop(self) -> None:
        """Stop the parser."""
        pass

    async def parse(self, content: str, path: Optional[Path] = None) -> Document:
        """Parse Markdown content into a Document."""
        self._logger.debug("parsing_markdown", path=str(path) if path else None)

        # Parse frontmatter
        post = frontmatter.loads(content)
        frontmatter_data = post.metadata
        markdown_content = post.content

        # Create document ID
        doc_id = str(uuid.uuid4())
        if path:
            # Use path as part of ID for consistency
            doc_id = f"{path.stem}_{doc_id[:8]}"

        # Create metadata
        metadata = DocumentMetadata(path=path)
        if path and path.exists():
            stat = path.stat()
            metadata.size = stat.st_size
            metadata.modified_at = datetime.fromtimestamp(stat.st_mtime)

        # Extract tags from frontmatter
        if "tags" in frontmatter_data:
            tags = frontmatter_data["tags"]
            if isinstance(tags, list):
                metadata.tags.update(tags)
            elif isinstance(tags, str):
                metadata.tags.add(tags)

        # Parse sections
        sections = await self._parse_sections(markdown_content)

        # Create document
        document = Document(
            id=doc_id,
            type=DocumentType.MARKDOWN,
            content=content,
            metadata=metadata,
            frontmatter=frontmatter_data,
            sections=sections
        )

        self._logger.info(
            "markdown_parsed",
            doc_id=doc_id,
            sections=len(sections),
            has_frontmatter=bool(frontmatter_data)
        )

        return document

    def can_parse(self, path: Path) -> bool:
        """Check if the parser can handle a file."""
        return path.suffix.lower() in [".md", ".markdown", ".mdown", ".mkd"]

    async def _parse_sections(self, content: str) -> List[DocumentSection]:
        """Parse markdown content into sections with advanced detection."""
        sections = []
        current_section = None
        section_stack = []

        # Split content into lines
        lines = content.split('\n')
        current_content = []
        in_code_block = False
        code_block_lang = None

        for i, line in enumerate(lines):
            # Check for code block boundaries
            code_fence_match = re.match(r'^```(\w*)?', line)
            if code_fence_match:
                in_code_block = not in_code_block
                if in_code_block:
                    code_block_lang = code_fence_match.group(1) or 'text'
                current_content.append(line)
                continue

            # Skip heading detection inside code blocks
            if in_code_block:
                current_content.append(line)
                continue

            # Check if line is a heading
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match:
                # Save current section if exists
                if current_section:
                    section_content = '\n'.join(current_content).strip()
                    current_section.content = section_content

                    # Extract section metadata
                    current_section.metadata = await self._extract_section_metadata(
                        section_content,
                        current_section.title
                    )
                    sections.append(current_section)

                # Clear content buffer
                current_content = []

                # Parse heading
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Create new section
                section_id = str(uuid.uuid4())[:8]
                current_section = DocumentSection(
                    id=section_id,
                    title=title,
                    content="",
                    level=level
                )

                # Manage section hierarchy
                while section_stack and section_stack[-1].level >= level:
                    section_stack.pop()

                if section_stack:
                    parent = section_stack[-1]
                    current_section.parent_id = parent.id
                    parent.children.append(current_section)

                section_stack.append(current_section)
            else:
                # Add line to current content
                current_content.append(line)

        # Save last section
        if current_section:
            section_content = '\n'.join(current_content).strip()
            current_section.content = section_content
            current_section.metadata = await self._extract_section_metadata(
                section_content,
                current_section.title
            )
            sections.append(current_section)

        # If no sections found, create a default one
        if not sections and content.strip():
            default_section = DocumentSection(
                id=str(uuid.uuid4())[:8],
                title="Content",
                content=content.strip(),
                level=1
            )
            default_section.metadata = await self._extract_section_metadata(
                content.strip(),
                "Content"
            )
            sections.append(default_section)

        return sections

    async def _extract_section_metadata(self, content: str, title: str) -> Dict[str, Any]:
        """Extract metadata from section content."""
        metadata = {
            "word_count": len(content.split()),
            "char_count": len(content),
            "has_code_blocks": bool(self._extract_code_blocks(content)),
            "has_links": bool(self._extract_links(content)),
            "has_images": bool(self._extract_images(content)),
            "has_lists": bool(re.search(r'^[\s]*[-*+]\s', content, re.MULTILINE)),
            "has_tables": bool(re.search(r'\|.*\|', content)),
            "has_blockquotes": bool(re.search(r'^>', content, re.MULTILINE)),
        }

        # Extract code blocks with language info
        code_blocks = self._extract_code_blocks(content)
        if code_blocks:
            metadata["code_languages"] = list(set(block["language"] for block in code_blocks))
            metadata["code_block_count"] = len(code_blocks)

        # Extract list types
        if metadata["has_lists"]:
            metadata["list_types"] = []
            if re.search(r'^[\s]*[-*+]\s', content, re.MULTILINE):
                metadata["list_types"].append("unordered")
            if re.search(r'^[\s]*\d+\.\s', content, re.MULTILINE):
                metadata["list_types"].append("ordered")

        return metadata

    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown content."""
        code_blocks = []

        # Match fenced code blocks
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or 'text'
            code = match.group(2).strip()

            code_blocks.append({
                'language': language,
                'code': code,
                'start': match.start(),
                'end': match.end()
            })

        return code_blocks

    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract links from markdown content."""
        links = []

        # Match markdown links [text](url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.finditer(pattern, content)

        for match in matches:
            text = match.group(1)
            url = match.group(2)

            links.append({
                'text': text,
                'url': url,
                'start': match.start(),
                'end': match.end()
            })

        return links

    def _extract_images(self, content: str) -> List[Dict[str, str]]:
        """Extract images from markdown content."""
        images = []

        # Match markdown images ![alt](url)
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.finditer(pattern, content)

        for match in matches:
            alt_text = match.group(1)
            url = match.group(2)

            images.append({
                'alt_text': alt_text,
                'url': url,
                'start': match.start(),
                'end': match.end()
            })

        return images


from datetime import datetime
