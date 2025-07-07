"""Content extraction from documents."""

import re
import uuid
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import structlog

from ..core.base import Extractor, EventBus
from ..core.types import (
    Document,
    DocumentSection,
    ExtractedContent,
    ExtractionCategory,
    ProcessingConfig,
    EventType
)
from .category_detector import CategoryDetector

logger = structlog.get_logger()


class ContentExtractor(Extractor):
    """Extracts categorized content from documents."""

    def __init__(self, config: ProcessingConfig, event_bus: Optional[EventBus] = None):
        super().__init__("ContentExtractor", event_bus)
        self.config = config
        self.category_detector = CategoryDetector()

        # Extraction strategies
        self.min_section_size = getattr(config, 'min_section_size', 100)  # chars
        self.max_section_size = getattr(config, 'max_section_size', 5000)  # chars
        self.context_lines_before = getattr(config, 'context_lines_before', 2)
        self.context_lines_after = getattr(config, 'context_lines_after', 2)

    async def _initialize(self) -> None:
        """Initialize the extractor."""
        pass

    async def _start(self) -> None:
        """Start the extractor."""
        pass

    async def _stop(self) -> None:
        """Stop the extractor."""
        pass

    async def extract(self, document: Document) -> List[ExtractedContent]:
        """Extract content from a document."""
        self._logger.info("extracting_content", doc_id=document.id)

        await self.publish_event(
            EventType.EXTRACTION_STARTED,
            {"document_id": document.id}
        )

        extracted_contents = []

        try:
            # Extract from document sections
            for section in document.sections:
                contents = await self._extract_from_section(document, section)
                extracted_contents.extend(contents)

            # Extract code blocks if enabled
            if self.config.extract_code_blocks:
                code_contents = await self._extract_code_blocks(document)
                extracted_contents.extend(code_contents)

            # Extract links if enabled
            if self.config.extract_links:
                link_contents = await self._extract_links(document)
                extracted_contents.extend(link_contents)

            # Filter by importance
            extracted_contents = [
                content for content in extracted_contents
                if content.importance >= self.config.min_importance
            ]

            self._logger.info(
                "content_extracted",
                doc_id=document.id,
                count=len(extracted_contents)
            )

            await self.publish_event(
                EventType.EXTRACTION_COMPLETED,
                {
                    "document_id": document.id,
                    "extracted_count": len(extracted_contents)
                }
            )

        except Exception as e:
            self._logger.error(
                "extraction_failed",
                doc_id=document.id,
                error=str(e)
            )

            await self.publish_event(
                EventType.EXTRACTION_FAILED,
                {
                    "document_id": document.id,
                    "error": str(e)
                }
            )

            raise

        return extracted_contents

    def get_supported_categories(self) -> List[str]:
        """Get list of supported extraction categories."""
        return [cat.value for cat in ExtractionCategory]

    async def _extract_from_section(
        self,
        document: Document,
        section: DocumentSection
    ) -> List[ExtractedContent]:
        """Extract content from a document section."""
        contents = []

        # Skip empty sections
        if not section.content.strip():
            return contents

        # Detect category
        category, confidence = self.category_detector.detect_category(
            section.content,
            section.title
        )

        # Check if category is in our extraction list
        if self._should_extract_category(category):
            # Calculate importance based on various factors
            importance = self._calculate_importance(
                section,
                category,
                confidence
            )

            # Create extracted content
            content = ExtractedContent(
                id=str(uuid.uuid4())[:8],
                document_id=document.id,
                category=category,
                title=section.title,
                content=section.content,
                importance=importance,
                source_section=section.id,
                tags=self._extract_tags(section),
                metadata={
                    "level": section.level,
                    "confidence": confidence,
                    "has_code": bool(self._find_code_blocks(section.content)),
                    "has_links": bool(self._find_links(section.content)),
                }
            )

            contents.append(content)

        # Process child sections
        for child in section.children:
            child_contents = await self._extract_from_section(document, child)
            contents.extend(child_contents)

        return contents

    async def _extract_code_blocks(self, document: Document) -> List[ExtractedContent]:
        """Extract code blocks as separate content items."""
        contents = []

        # Find all code blocks in the document
        code_blocks = self._find_code_blocks(document.content)

        for i, block in enumerate(code_blocks):
            # Try to detect what the code is about
            category = ExtractionCategory.CUSTOM
            title = f"Code Block {i + 1}"

            # Look for patterns in the code
            if "test" in block["language"].lower() or "test" in block["code"].lower():
                category = ExtractionCategory.TESTING
                title = f"Test Code ({block['language']})"
            elif "api" in block["code"].lower() or "endpoint" in block["code"].lower():
                category = ExtractionCategory.API
                title = f"API Code ({block['language']})"
            elif "config" in block["language"].lower() or "configuration" in block["code"].lower():
                category = ExtractionCategory.CONFIGURATION
                title = f"Configuration ({block['language']})"

            content = ExtractedContent(
                id=str(uuid.uuid4())[:8],
                document_id=document.id,
                category=category,
                title=title,
                content=block["code"],
                importance=0.7,  # Code blocks are generally important
                tags={block["language"], "code"},
                metadata={
                    "language": block["language"],
                    "line_count": len(block["code"].split('\n')),
                    "char_count": len(block["code"]),
                }
            )

            contents.append(content)

        return contents

    async def _extract_links(self, document: Document) -> List[ExtractedContent]:
        """Extract links as separate content items."""
        contents = []

        # Find all links in the document
        links = self._find_links(document.content)

        # Group links by category
        api_links = []
        doc_links = []
        other_links = []

        for link in links:
            url = link["url"].lower()
            if "api" in url or "endpoint" in url:
                api_links.append(link)
            elif "doc" in url or "guide" in url or "tutorial" in url:
                doc_links.append(link)
            else:
                other_links.append(link)

        # Create content items for link groups
        if api_links:
            content = ExtractedContent(
                id=str(uuid.uuid4())[:8],
                document_id=document.id,
                category=ExtractionCategory.API,
                title="API References",
                content=self._format_links(api_links),
                importance=0.6,
                tags={"links", "api"},
                metadata={"link_count": len(api_links)}
            )
            contents.append(content)

        if doc_links:
            content = ExtractedContent(
                id=str(uuid.uuid4())[:8],
                document_id=document.id,
                category=ExtractionCategory.DOCUMENTATION,
                title="Documentation Links",
                content=self._format_links(doc_links),
                importance=0.5,
                tags={"links", "documentation"},
                metadata={"link_count": len(doc_links)}
            )
            contents.append(content)

        return contents

    def _should_extract_category(self, category: ExtractionCategory) -> bool:
        """Check if a category should be extracted."""
        if not self.config.extract_categories:
            return True

        return category in self.config.extract_categories or category.value in self.config.extract_categories

    def _calculate_importance(
        self,
        section: DocumentSection,
        category: ExtractionCategory,
        confidence: float
    ) -> float:
        """Calculate importance score for extracted content."""
        # Base importance from category confidence
        importance = min(confidence / 10.0, 1.0)

        # Adjust based on section level (higher level = more important)
        level_factor = 1.0 - (section.level - 1) * 0.1
        importance *= max(level_factor, 0.5)

        # Adjust based on content length
        content_length = len(section.content)
        if content_length < 100:
            importance *= 0.8
        elif content_length > 1000:
            importance *= 1.1

        # Boost for critical categories
        if category == ExtractionCategory.CRITICAL:
            importance *= 1.5
        elif category == ExtractionCategory.SECURITY:
            importance *= 1.3

        # Ensure within bounds
        return max(0.0, min(importance, 1.0))

    def _extract_tags(self, section: DocumentSection) -> Set[str]:
        """Extract tags from a section."""
        tags = set()

        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', section.content)
        tags.update(hashtags)

        # Extract @mentions
        mentions = re.findall(r'@(\w+)', section.content)
        tags.update(mentions)

        # Add section level as tag
        tags.add(f"h{section.level}")

        return tags

    def _find_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Find code blocks in content."""
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
            })

        return code_blocks

    def _find_links(self, content: str) -> List[Dict[str, str]]:
        """Find links in content."""
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
            })

        return links

    def _format_links(self, links: List[Dict[str, str]]) -> str:
        """Format links as markdown list."""
        lines = []
        for link in links:
            lines.append(f"- [{link['text']}]({link['url']})")
        return '\n'.join(lines)

    async def extract_with_strategy(
        self,
        document: Document,
        strategy: str = "auto"
    ) -> List[ExtractedContent]:
        """Extract content using a specific strategy."""
        strategies = {
            "auto": self._extract_auto,
            "by_size": self._extract_by_size,
            "by_section": self._extract_by_section,
            "by_type": self._extract_by_type,
        }

        strategy_func = strategies.get(strategy, self._extract_auto)
        return await strategy_func(document)

    async def _extract_auto(self, document: Document) -> List[ExtractedContent]:
        """Automatically choose best extraction strategy."""
        # Calculate document characteristics
        total_size = len(document.content)
        section_count = len(document.sections)

        # Choose strategy based on document characteristics
        if total_size > 10000:  # Large documents
            return await self._extract_by_size(document)
        elif section_count > 10:  # Many sections
            return await self._extract_by_section(document)
        else:
            return await self.extract(document)

    async def _extract_by_size(self, document: Document) -> List[ExtractedContent]:
        """Extract content by breaking into size-appropriate chunks."""
        extracted_contents = []

        for section in document.sections:
            if len(section.content) <= self.max_section_size:
                # Extract as single content
                contents = await self._extract_from_section(document, section)
                extracted_contents.extend(contents)
            else:
                # Break into smaller chunks
                chunks = self._split_content_by_size(section.content, self.max_section_size)
                for i, chunk in enumerate(chunks):
                    # Create a temporary section for the chunk
                    chunk_section = DocumentSection(
                        id=f"{section.id}_chunk_{i}",
                        title=f"{section.title} (Part {i + 1})",
                        content=chunk,
                        level=section.level,
                        parent_id=section.parent_id,
                        metadata={**section.metadata, "is_chunk": True, "chunk_index": i}
                    )
                    contents = await self._extract_from_section(document, chunk_section)
                    extracted_contents.extend(contents)

        return extracted_contents

    async def _extract_by_section(self, document: Document) -> List[ExtractedContent]:
        """Extract content preserving section boundaries."""
        extracted_contents = []

        # Group small sections together
        section_groups = self._group_sections_by_hierarchy(document.sections)

        for group in section_groups:
            if len(group) == 1:
                # Single section
                contents = await self._extract_from_section(document, group[0])
                extracted_contents.extend(contents)
            else:
                # Multiple related sections
                combined_content = self._combine_sections(group)
                contents = await self._extract_from_combined_sections(document, group, combined_content)
                extracted_contents.extend(contents)

        return extracted_contents

    async def _extract_by_type(self, document: Document) -> List[ExtractedContent]:
        """Extract content grouped by type (code, documentation, etc.)."""
        type_groups = {
            "code": [],
            "documentation": [],
            "configuration": [],
            "other": []
        }

        # Categorize sections
        for section in document.sections:
            category, _ = self.category_detector.detect_category(section.content, section.title)

            if category in [ExtractionCategory.API, ExtractionCategory.TESTING]:
                type_groups["code"].append(section)
            elif category in [ExtractionCategory.DOCUMENTATION, ExtractionCategory.SETUP]:
                type_groups["documentation"].append(section)
            elif category == ExtractionCategory.CONFIGURATION:
                type_groups["configuration"].append(section)
            else:
                type_groups["other"].append(section)

        extracted_contents = []

        # Extract each type group
        for type_name, sections in type_groups.items():
            if sections:
                for section in sections:
                    contents = await self._extract_from_section(document, section)
                    # Add type metadata
                    for content in contents:
                        content.metadata["content_type"] = type_name
                    extracted_contents.extend(contents)

        return extracted_contents

    def _split_content_by_size(self, content: str, max_size: int) -> List[str]:
        """Split content into chunks of appropriate size."""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > max_size and current_chunk:
                # Save current chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        # Save last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _group_sections_by_hierarchy(self, sections: List[DocumentSection]) -> List[List[DocumentSection]]:
        """Group sections by their hierarchical relationships."""
        groups = []
        processed = set()

        for section in sections:
            if section.id in processed:
                continue

            # Find all related sections (parent and children)
            group = [section]
            processed.add(section.id)

            # Add children
            for child in section.children:
                if child.id not in processed:
                    group.append(child)
                    processed.add(child.id)

            groups.append(group)

        return groups

    def _combine_sections(self, sections: List[DocumentSection]) -> str:
        """Combine multiple sections into a single content block."""
        combined_parts = []

        for section in sections:
            # Add section header
            header_level = '#' * section.level
            combined_parts.append(f"{header_level} {section.title}")
            combined_parts.append("")  # Empty line
            combined_parts.append(section.content)
            combined_parts.append("")  # Empty line

        return '\n'.join(combined_parts)

    async def _extract_from_combined_sections(
        self,
        document: Document,
        sections: List[DocumentSection],
        combined_content: str
    ) -> List[ExtractedContent]:
        """Extract content from combined sections."""
        # Use the highest level section as the primary
        primary_section = min(sections, key=lambda s: s.level)

        # Detect category for combined content
        category, confidence = self.category_detector.detect_category(
            combined_content,
            primary_section.title
        )

        if self._should_extract_category(category):
            importance = self._calculate_importance(primary_section, category, confidence)

            content = ExtractedContent(
                id=str(uuid.uuid4())[:8],
                document_id=document.id,
                category=category,
                title=primary_section.title,
                content=combined_content,
                importance=importance,
                source_section=primary_section.id,
                tags=self._extract_tags_from_sections(sections),
                metadata={
                    "is_combined": True,
                    "section_count": len(sections),
                    "section_ids": [s.id for s in sections],
                    "confidence": confidence,
                }
            )

            return [content]

        return []

    def _extract_tags_from_sections(self, sections: List[DocumentSection]) -> Set[str]:
        """Extract tags from multiple sections."""
        tags = set()
        for section in sections:
            tags.update(self._extract_tags(section))
        return tags

    async def extract_with_context(
        self,
        document: Document,
        section_id: str
    ) -> Optional[ExtractedContent]:
        """Extract a section with surrounding context."""
        # Find the section
        target_section = None
        for section in document.sections:
            if section.id == section_id:
                target_section = section
                break

        if not target_section:
            return None

        # Get context
        context_before, context_after = self._get_section_context(document, target_section)

        # Build content with context
        content_parts = []

        if context_before:
            content_parts.append("<!-- Context before -->")
            content_parts.append(context_before)
            content_parts.append("<!-- End context -->")
            content_parts.append("")

        content_parts.append(target_section.content)

        if context_after:
            content_parts.append("")
            content_parts.append("<!-- Context after -->")
            content_parts.append(context_after)
            content_parts.append("<!-- End context -->")

        content_with_context = '\n'.join(content_parts)

        # Detect category
        category, confidence = self.category_detector.detect_category(
            target_section.content,
            target_section.title
        )

        importance = self._calculate_importance(target_section, category, confidence)

        return ExtractedContent(
            id=str(uuid.uuid4())[:8],
            document_id=document.id,
            category=category,
            title=target_section.title,
            content=content_with_context,
            importance=importance,
            source_section=target_section.id,
            tags=self._extract_tags(target_section),
            metadata={
                "has_context": True,
                "context_before_lines": len(context_before.split('\n')) if context_before else 0,
                "context_after_lines": len(context_after.split('\n')) if context_after else 0,
                "confidence": confidence,
            }
        )

    def _get_section_context(
        self,
        document: Document,
        target_section: DocumentSection
    ) -> Tuple[str, str]:
        """Get context before and after a section."""
        # Find section index
        section_index = -1
        for i, section in enumerate(document.sections):
            if section.id == target_section.id:
                section_index = i
                break

        if section_index == -1:
            return "", ""

        # Get context before
        context_before_parts = []
        if section_index > 0:
            prev_section = document.sections[section_index - 1]
            lines = prev_section.content.split('\n')
            context_lines = lines[-self.context_lines_before:] if lines else []
            if context_lines:
                context_before_parts.extend(context_lines)

        # Get context after
        context_after_parts = []
        if section_index < len(document.sections) - 1:
            next_section = document.sections[section_index + 1]
            lines = next_section.content.split('\n')
            context_lines = lines[:self.context_lines_after] if lines else []
            if context_lines:
                context_after_parts.extend(context_lines)

        return '\n'.join(context_before_parts), '\n'.join(context_after_parts)

    async def extract_from_sections(
        self,
        document: Document,
        sections: List[DocumentSection]
    ) -> List[ExtractedContent]:
        """Extract content from specific sections."""
        extracted_contents = []

        for section in sections:
            contents = await self._extract_from_section(document, section)
            extracted_contents.extend(contents)

        return extracted_contents
