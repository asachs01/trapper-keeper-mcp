"""Document organization implementation."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict
import aiofiles
import structlog

from ..core.base import Organizer, EventBus
from ..core.types import (
    ExtractedContent,
    ExtractionCategory,
    OrganizationConfig,
    EventType
)

logger = structlog.get_logger()


class DocumentOrganizer(Organizer):
    """Organizes extracted content into structured output."""
    
    def __init__(self, config: OrganizationConfig, event_bus: Optional[EventBus] = None):
        super().__init__("DocumentOrganizer", event_bus)
        self.config = config
        
    async def _initialize(self) -> None:
        """Initialize the organizer."""
        # Create output directory if it doesn't exist
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def _start(self) -> None:
        """Start the organizer."""
        pass
        
    async def _stop(self) -> None:
        """Stop the organizer."""
        pass
        
    async def organize(
        self,
        contents: List[ExtractedContent]
    ) -> Dict[str, List[ExtractedContent]]:
        """Organize extracted contents into categories."""
        self._logger.info("organizing_content", count=len(contents))
        
        await self.publish_event(
            EventType.ORGANIZATION_STARTED,
            {"content_count": len(contents)}
        )
        
        try:
            organized = defaultdict(list)
            
            if self.config.group_by_category:
                # Group by category
                for content in contents:
                    category_key = content.category
                    if isinstance(category_key, ExtractionCategory):
                        category_key = category_key.value
                    organized[category_key].append(content)
                    
            elif self.config.group_by_document:
                # Group by source document
                for content in contents:
                    organized[content.document_id].append(content)
                    
            else:
                # Single group
                organized["all"] = contents
                
            # Sort contents within each group by importance
            for group in organized.values():
                group.sort(key=lambda x: x.importance, reverse=True)
                
            self._logger.info(
                "content_organized",
                groups=len(organized),
                total_contents=len(contents)
            )
            
            await self.publish_event(
                EventType.ORGANIZATION_COMPLETED,
                {
                    "group_count": len(organized),
                    "content_count": len(contents)
                }
            )
            
            return dict(organized)
            
        except Exception as e:
            self._logger.error("organization_failed", error=str(e))
            
            await self.publish_event(
                EventType.ORGANIZATION_FAILED,
                {"error": str(e)}
            )
            
            raise
            
    async def save(
        self,
        organized_content: Dict[str, List[ExtractedContent]],
        output_dir: Optional[Path] = None
    ) -> None:
        """Save organized content to output directory."""
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save based on format
        if self.config.format == "markdown":
            await self._save_as_markdown(organized_content, output_dir)
        elif self.config.format == "json":
            await self._save_as_json(organized_content, output_dir)
        elif self.config.format == "yaml":
            await self._save_as_yaml(organized_content, output_dir)
        else:
            raise ValueError(f"Unsupported format: {self.config.format}")
            
        # Create index if requested
        if self.config.create_index:
            await self._create_index(organized_content, output_dir)
            
        self._logger.info(
            "content_saved",
            output_dir=str(output_dir),
            format=self.config.format
        )
        
    async def _save_as_markdown(
        self,
        organized_content: Dict[str, List[ExtractedContent]],
        output_dir: Path
    ) -> None:
        """Save organized content as markdown files."""
        for category, contents in organized_content.items():
            # Create category file
            filename = f"{self._sanitize_filename(category)}.md"
            filepath = output_dir / filename
            
            # Build markdown content
            lines = [
                f"# {category}",
                f"\n*Generated on {datetime.utcnow().isoformat()}*\n",
                f"Total items: {len(contents)}\n",
                "---\n"
            ]
            
            for content in contents:
                lines.append(f"## {content.title}\n")
                
                if self.config.include_metadata:
                    lines.append(f"- **Category**: {content.category}")
                    lines.append(f"- **Importance**: {content.importance:.2f}")
                    lines.append(f"- **Document**: {content.document_id}")
                    if content.tags:
                        lines.append(f"- **Tags**: {', '.join(sorted(content.tags))}")
                    lines.append("")
                    
                lines.append(content.content)
                lines.append("\n---\n")
                
            # Write file
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(lines))
                
    async def _save_as_json(
        self,
        organized_content: Dict[str, List[ExtractedContent]],
        output_dir: Path
    ) -> None:
        """Save organized content as JSON files."""
        for category, contents in organized_content.items():
            filename = f"{self._sanitize_filename(category)}.json"
            filepath = output_dir / filename
            
            # Convert to JSON-serializable format
            data = {
                "category": category,
                "generated_at": datetime.utcnow().isoformat(),
                "total_items": len(contents),
                "contents": []
            }
            
            for content in contents:
                item = {
                    "id": content.id,
                    "title": content.title,
                    "content": content.content,
                    "document_id": content.document_id,
                    "importance": content.importance,
                    "extracted_at": content.extracted_at.isoformat(),
                }
                
                if self.config.include_metadata:
                    item.update({
                        "category": content.category.value if isinstance(content.category, ExtractionCategory) else content.category,
                        "tags": list(content.tags),
                        "source_section": content.source_section,
                        "metadata": content.metadata
                    })
                    
                data["contents"].append(item)
                
            # Write file
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
                
    async def _save_as_yaml(
        self,
        organized_content: Dict[str, List[ExtractedContent]],
        output_dir: Path
    ) -> None:
        """Save organized content as YAML files."""
        for category, contents in organized_content.items():
            filename = f"{self._sanitize_filename(category)}.yaml"
            filepath = output_dir / filename
            
            # Convert to YAML-serializable format
            data = {
                "category": category,
                "generated_at": datetime.utcnow().isoformat(),
                "total_items": len(contents),
                "contents": []
            }
            
            for content in contents:
                item = {
                    "id": content.id,
                    "title": content.title,
                    "content": content.content,
                    "document_id": content.document_id,
                    "importance": content.importance,
                    "extracted_at": content.extracted_at.isoformat(),
                }
                
                if self.config.include_metadata:
                    item.update({
                        "category": content.category.value if isinstance(content.category, ExtractionCategory) else content.category,
                        "tags": list(content.tags),
                        "source_section": content.source_section,
                        "metadata": content.metadata
                    })
                    
                data["contents"].append(item)
                
            # Write file
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))
                
    async def _create_index(
        self,
        organized_content: Dict[str, List[ExtractedContent]],
        output_dir: Path
    ) -> None:
        """Create an index file for all organized content."""
        index_path = output_dir / "index.md"
        
        lines = [
            "# Trapper Keeper Content Index",
            f"\n*Generated on {datetime.utcnow().isoformat()}*\n",
            "## Categories\n"
        ]
        
        # Category overview
        total_contents = 0
        for category, contents in sorted(organized_content.items()):
            total_contents += len(contents)
            filename = f"{self._sanitize_filename(category)}.{self.config.format}"
            lines.append(f"- [{category}](./{filename}) ({len(contents)} items)")
            
        lines.append(f"\n**Total items**: {total_contents}\n")
        
        # Statistics by category
        lines.append("## Statistics\n")
        lines.append("| Category | Count | Avg Importance |")
        lines.append("|----------|-------|----------------|")
        
        for category, contents in sorted(organized_content.items()):
            avg_importance = sum(c.importance for c in contents) / len(contents) if contents else 0
            lines.append(f"| {category} | {len(contents)} | {avg_importance:.2f} |")
            
        # Document sources
        doc_ids = set()
        for contents in organized_content.values():
            doc_ids.update(c.document_id for c in contents)
            
        lines.append(f"\n## Source Documents\n")
        lines.append(f"Total documents processed: {len(doc_ids)}\n")
        for doc_id in sorted(doc_ids):
            lines.append(f"- {doc_id}")
            
        # Write index
        async with aiofiles.open(index_path, 'w', encoding='utf-8') as f:
            await f.write('\n'.join(lines))
            
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # Remove emojis and special characters
        sanitized = re.sub(r'[^\w\s-]', '', name)
        # Replace spaces with underscores
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Convert to lowercase
        return sanitized.lower() or "unknown"


import re