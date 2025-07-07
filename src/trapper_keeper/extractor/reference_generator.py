"""Reference link generation for extracted content."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
import structlog

from ..core.types import ExtractedContent, Document

logger = structlog.get_logger()


class ReferenceGenerator:
    """Generates reference links between documents and extracted content."""
    
    def __init__(self, base_path: Path = Path("docs")):
        self.base_path = base_path
        self._reference_map: Dict[str, List[str]] = {}
        
    def generate_reference_link(
        self,
        source_path: Path,
        target_path: Path,
        section_id: Optional[str] = None,
        link_text: Optional[str] = None
    ) -> str:
        """Generate a markdown reference link."""
        # Calculate relative path
        try:
            rel_path = target_path.relative_to(source_path.parent)
        except ValueError:
            # If not relative, use absolute path from base
            try:
                rel_path = target_path.relative_to(self.base_path)
            except ValueError:
                rel_path = target_path
                
        # Convert to URL-safe path
        url_path = "/".join(quote(part) for part in rel_path.parts)
        
        # Add section anchor if provided
        if section_id:
            url_path += f"#{section_id}"
            
        # Generate link text
        if not link_text:
            link_text = target_path.stem.replace("-", " ").replace("_", " ").title()
            
        return f"[{link_text}]({url_path})"
        
    def generate_backlink(
        self,
        source_path: Path,
        target_path: Path,
        context: Optional[str] = None
    ) -> str:
        """Generate a backlink from target to source."""
        link = self.generate_reference_link(target_path, source_path)
        
        if context:
            return f"← Back to {link} ({context})"
        else:
            return f"← Back to {link}"
            
    def generate_content_reference(
        self,
        content: ExtractedContent,
        output_path: Path,
        source_document: Document
    ) -> Dict[str, str]:
        """Generate reference information for extracted content."""
        references = {}
        
        # Source reference
        if source_document.metadata.path:
            source_link = self.generate_reference_link(
                output_path,
                source_document.metadata.path,
                content.source_section,
                f"Source: {source_document.metadata.path.name}"
            )
            references["source"] = source_link
            
        # Category reference
        category_link = f"[[{content.category}]]"
        references["category"] = category_link
        
        # Tag references
        tag_links = [f"#{tag}" for tag in sorted(content.tags)]
        references["tags"] = " ".join(tag_links)
        
        # Related content references
        related = self._find_related_content(content)
        if related:
            related_links = []
            for rel_content, score in related[:3]:  # Top 3 related
                if rel_content.id != content.id:
                    link = f"[[{rel_content.title}]]"
                    related_links.append(link)
            references["related"] = " | ".join(related_links)
            
        return references
        
    def generate_reference_block(
        self,
        content: ExtractedContent,
        output_path: Path,
        source_document: Document
    ) -> str:
        """Generate a complete reference block for content."""
        refs = self.generate_content_reference(content, output_path, source_document)
        
        lines = ["---", "## References", ""]
        
        if "source" in refs:
            lines.append(f"**Source**: {refs['source']}")
            
        if "category" in refs:
            lines.append(f"**Category**: {refs['category']}")
            
        if "tags" in refs:
            lines.append(f"**Tags**: {refs['tags']}")
            
        if "related" in refs:
            lines.append(f"**Related**: {refs['related']}")
            
        lines.extend(["", "---"])
        
        return "\n".join(lines)
        
    def update_source_with_extraction_links(
        self,
        source_path: Path,
        extractions: List[Tuple[ExtractedContent, Path]]
    ) -> str:
        """Update source document with links to extracted content."""
        if not source_path.exists():
            return ""
            
        content = source_path.read_text(encoding='utf-8')
        
        # Find insertion point (after frontmatter if exists)
        lines = content.split('\n')
        insert_index = 0
        
        # Skip frontmatter
        if lines and lines[0].strip() == '---':
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    insert_index = i + 1
                    break
                    
        # Build extraction links section
        link_section = ["", "## 📚 Extracted Content", ""]
        
        # Group by category
        by_category: Dict[str, List[Tuple[ExtractedContent, Path]]] = {}
        for content, path in extractions:
            category = str(content.category)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((content, path))
            
        # Generate links by category
        for category, items in sorted(by_category.items()):
            link_section.append(f"### {category}")
            link_section.append("")
            
            for content, path in items:
                link = self.generate_reference_link(source_path, path, link_text=content.title)
                # Add metadata
                metadata_parts = []
                
                if content.importance >= 0.8:
                    metadata_parts.append("⭐")
                    
                if content.metadata.get("line_count", 0) > 50:
                    metadata_parts.append(f"{content.metadata['line_count']} lines")
                    
                metadata = f" ({', '.join(metadata_parts)})" if metadata_parts else ""
                
                link_section.append(f"- {link}{metadata}")
                
            link_section.append("")
            
        # Insert links into content
        lines[insert_index:insert_index] = link_section
        
        return '\n'.join(lines)
        
    def generate_index_file(
        self,
        output_dir: Path,
        contents: List[Tuple[ExtractedContent, Path]]
    ) -> str:
        """Generate an index file for extracted contents."""
        lines = [
            "# 📚 Extracted Content Index",
            "",
            f"Generated from {len(set(c.document_id for c, _ in contents))} documents",
            f"Total extractions: {len(contents)}",
            "",
            "---",
            ""
        ]
        
        # Group by category
        by_category: Dict[str, List[Tuple[ExtractedContent, Path]]] = {}
        for content, path in contents:
            category = str(content.category)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((content, path))
            
        # Generate table of contents
        lines.extend(["## Table of Contents", ""])
        for category in sorted(by_category.keys()):
            count = len(by_category[category])
            lines.append(f"- [{category}](#{category.lower().replace(' ', '-')}) ({count} items)")
            
        lines.extend(["", "---", ""])
        
        # Generate sections
        for category, items in sorted(by_category.items()):
            lines.append(f"## {category}")
            lines.append("")
            
            # Sort by importance
            sorted_items = sorted(items, key=lambda x: x[0].importance, reverse=True)
            
            for content, path in sorted_items:
                rel_path = path.relative_to(output_dir)
                link = f"[{content.title}]({rel_path})"
                
                # Build metadata line
                metadata_parts = []
                
                if content.importance >= 0.8:
                    metadata_parts.append("⭐ High importance")
                    
                if content.tags:
                    tags = " ".join(f"`{tag}`" for tag in sorted(content.tags)[:3])
                    metadata_parts.append(f"Tags: {tags}")
                    
                metadata = f"  \n  {' | '.join(metadata_parts)}" if metadata_parts else ""
                
                lines.append(f"- {link}{metadata}")
                
            lines.append("")
            
        return '\n'.join(lines)
        
    def _find_related_content(
        self,
        content: ExtractedContent,
        threshold: float = 0.3
    ) -> List[Tuple[ExtractedContent, float]]:
        """Find related content based on tags and category."""
        # This is a placeholder - in a real implementation,
        # this would search through a content index
        return []
        
    def track_reference(self, source_id: str, target_id: str) -> None:
        """Track a reference between content items."""
        if source_id not in self._reference_map:
            self._reference_map[source_id] = []
        self._reference_map[source_id].append(target_id)
        
    def get_references(self, content_id: str) -> List[str]:
        """Get all references from a content item."""
        return self._reference_map.get(content_id, [])
        
    def validate_references(self, base_dir: Path) -> List[str]:
        """Validate all references point to existing files."""
        errors = []
        
        for source_id, target_ids in self._reference_map.items():
            for target_id in target_ids:
                # This is a simplified check - would need actual path resolution
                # in a real implementation
                pass
                
        return errors