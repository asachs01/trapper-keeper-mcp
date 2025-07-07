"""Create reference tool for MCP."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .base import BaseTool
from ...extractor import ReferenceGenerator


class CreateReferenceRequest(BaseModel):
    """Request to create references."""
    source_file: str = Field(..., description="Path to source file that was extracted from")
    extracted_files: List[str] = Field(..., description="List of extracted content files")
    reference_format: str = Field("markdown", description="Format for references (markdown, link-list, index)")
    index_file: Optional[str] = Field(None, description="Path to index file to update")
    create_backlinks: bool = Field(True, description="Add backlinks in extracted files")
    update_source: bool = Field(True, description="Update source file with references")
    

class ReferenceLink(BaseModel):
    """Information about a created reference link."""
    source_section: str
    target_file: str
    link_text: str
    link_format: str
    category: str
    

class CreateReferenceResponse(BaseModel):
    """Response from create reference."""
    success: bool
    references_created: List[ReferenceLink]
    total_references: int
    source_updated: bool
    index_updated: bool
    backlinks_created: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time: float


class CreateReferenceTool(BaseTool):
    """Tool for creating reference links between documents."""
    
    def __init__(self, config, event_bus=None):
        super().__init__("create_reference", config, event_bus)
        self.reference_generator: Optional[ReferenceGenerator] = None
        
    async def initialize(self) -> None:
        """Initialize tool components."""
        self.reference_generator = ReferenceGenerator(self.config.processing, self.event_bus)
        await self.reference_generator.initialize()
        
    async def execute(self, request: CreateReferenceRequest) -> CreateReferenceResponse:
        """Execute the create reference tool."""
        start_time = time.time()
        
        # Initialize if needed
        if not self.reference_generator:
            await self.initialize()
            
        try:
            # Validate paths
            source_path = Path(request.source_file)
            if not source_path.exists():
                return CreateReferenceResponse(
                    success=False,
                    references_created=[],
                    total_references=0,
                    source_updated=False,
                    index_updated=False,
                    backlinks_created=0,
                    errors=[f"Source file not found: {source_path}"],
                    processing_time=time.time() - start_time
                )
                
            # Validate extracted files
            extracted_paths = []
            for file_path in request.extracted_files:
                path = Path(file_path)
                if not path.exists():
                    return CreateReferenceResponse(
                        success=False,
                        references_created=[],
                        total_references=0,
                        source_updated=False,
                        index_updated=False,
                        backlinks_created=0,
                        errors=[f"Extracted file not found: {path}"],
                        processing_time=time.time() - start_time
                    )
                extracted_paths.append(path)
                
            # Generate references
            references_created = []
            
            # Read source content
            source_content = source_path.read_text(encoding='utf-8')
            updated_content = source_content
            
            # Process each extracted file
            for extracted_path in extracted_paths:
                # Read extracted content metadata
                extracted_content = extracted_path.read_text(encoding='utf-8')
                
                # Extract metadata from content (assuming frontmatter or headers)
                metadata = self._extract_metadata(extracted_content)
                
                # Generate reference link
                if request.reference_format == "markdown":
                    link = self._create_markdown_link(
                        source_path, extracted_path, metadata
                    )
                elif request.reference_format == "link-list":
                    link = self._create_list_link(
                        source_path, extracted_path, metadata
                    )
                else:  # index format
                    link = self._create_index_link(
                        source_path, extracted_path, metadata
                    )
                    
                reference = ReferenceLink(
                    source_section=metadata.get("source_section", ""),
                    target_file=str(extracted_path),
                    link_text=link["text"],
                    link_format=link["format"],
                    category=metadata.get("category", "General")
                )
                references_created.append(reference)
                
                # Update source content if requested
                if request.update_source and metadata.get("source_section"):
                    updated_content = self._insert_reference_in_content(
                        updated_content,
                        metadata["source_section"],
                        link["format"]
                    )
                    
            # Save updated source if changed
            source_updated = False
            if request.update_source and updated_content != source_content:
                source_path.write_text(updated_content, encoding='utf-8')
                source_updated = True
                
            # Create backlinks if requested
            backlinks_created = 0
            if request.create_backlinks:
                for extracted_path in extracted_paths:
                    if await self._add_backlink(extracted_path, source_path):
                        backlinks_created += 1
                        
            # Update index if requested
            index_updated = False
            if request.index_file:
                index_path = Path(request.index_file)
                if await self._update_index(index_path, references_created):
                    index_updated = True
                    
            return CreateReferenceResponse(
                success=True,
                references_created=references_created,
                total_references=len(references_created),
                source_updated=source_updated,
                index_updated=index_updated,
                backlinks_created=backlinks_created,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            self._logger.error("create_reference_failed", error=str(e))
            return CreateReferenceResponse(
                success=False,
                references_created=[],
                total_references=0,
                source_updated=False,
                index_updated=False,
                backlinks_created=0,
                errors=[str(e)],
                processing_time=time.time() - start_time
            )
            
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from file content."""
        metadata = {}
        
        # Look for frontmatter
        if content.startswith("---"):
            try:
                import yaml
                frontmatter_end = content.find("---", 3)
                if frontmatter_end > 0:
                    frontmatter = content[3:frontmatter_end]
                    metadata = yaml.safe_load(frontmatter) or {}
            except:
                pass
                
        # Look for headers
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith("# "):
                metadata["title"] = line[2:].strip()
                break
                
        # Look for category indicators
        for line in lines[:20]:
            if "Category:" in line or "category:" in line:
                metadata["category"] = line.split(":", 1)[1].strip()
                break
                
        return metadata
        
    def _create_markdown_link(self, source_path: Path, target_path: Path, metadata: Dict) -> Dict:
        """Create a markdown-style reference link."""
        relative_path = self._get_relative_path(source_path.parent, target_path)
        title = metadata.get("title", target_path.stem)
        category = metadata.get("category", "")
        
        link_text = f"[{title}]({relative_path})"
        if category:
            link_text = f"{category}: {link_text}"
            
        return {
            "text": link_text,
            "format": f"\n> **Extracted**: {link_text}\n"
        }
        
    def _create_list_link(self, source_path: Path, target_path: Path, metadata: Dict) -> Dict:
        """Create a list-style reference link."""
        relative_path = self._get_relative_path(source_path.parent, target_path)
        title = metadata.get("title", target_path.stem)
        
        return {
            "text": title,
            "format": f"\n- [{title}]({relative_path})"
        }
        
    def _create_index_link(self, source_path: Path, target_path: Path, metadata: Dict) -> Dict:
        """Create an index-style reference link."""
        relative_path = self._get_relative_path(source_path.parent, target_path)
        title = metadata.get("title", target_path.stem)
        category = metadata.get("category", "General")
        
        return {
            "text": f"{category}: {title}",
            "format": f"| {category} | [{title}]({relative_path}) | {datetime.now().strftime('%Y-%m-%d')} |"
        }
        
    def _get_relative_path(self, from_dir: Path, to_path: Path) -> str:
        """Get relative path from one directory to a file."""
        try:
            return str(to_path.relative_to(from_dir))
        except ValueError:
            # If not relative, use absolute path
            return str(to_path)
            
    def _insert_reference_in_content(self, content: str, section_id: str, reference: str) -> str:
        """Insert reference link in the appropriate section."""
        # This is a simplified implementation
        # In practice, would need to parse the document structure
        lines = content.split('\n')
        updated_lines = []
        
        in_section = False
        for line in lines:
            updated_lines.append(line)
            
            # Simple heuristic: look for section headers
            if section_id in line and line.startswith("#"):
                in_section = True
            elif in_section and line.startswith("#"):
                # End of section, insert reference before next section
                updated_lines.insert(-1, reference)
                in_section = False
                
        # If still in section at end, append reference
        if in_section:
            updated_lines.append(reference)
            
        return '\n'.join(updated_lines)
        
    async def _add_backlink(self, extracted_path: Path, source_path: Path) -> bool:
        """Add a backlink from extracted content to source."""
        try:
            content = extracted_path.read_text(encoding='utf-8')
            
            # Add backlink at the end
            relative_source = self._get_relative_path(extracted_path.parent, source_path)
            backlink = f"\n\n---\n\n**Source**: [{source_path.name}]({relative_source})\n"
            
            if backlink not in content:
                content += backlink
                extracted_path.write_text(content, encoding='utf-8')
                
            return True
        except Exception as e:
            self._logger.error("add_backlink_failed", error=str(e))
            return False
            
    async def _update_index(self, index_path: Path, references: List[ReferenceLink]) -> bool:
        """Update index file with new references."""
        try:
            # Create index if it doesn't exist
            if not index_path.exists():
                index_content = "# Extracted Content Index\n\n"
                index_content += "| Category | Title | File | Date |\n"
                index_content += "|----------|-------|------|------|\n"
            else:
                index_content = index_path.read_text(encoding='utf-8')
                
            # Add new references
            for ref in references:
                index_line = f"| {ref.category} | {ref.link_text} | {ref.target_file} | {datetime.now().strftime('%Y-%m-%d')} |\n"
                if index_line not in index_content:
                    index_content += index_line
                    
            index_path.write_text(index_content, encoding='utf-8')
            return True
            
        except Exception as e:
            self._logger.error("update_index_failed", error=str(e))
            return False