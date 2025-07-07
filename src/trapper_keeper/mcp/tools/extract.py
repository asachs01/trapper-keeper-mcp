"""Extract content tool for MCP."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .base import BaseTool
from ...core.types import ExtractedContent, ExtractionCategory
from ...parser import get_parser
from ...extractor import ContentExtractor


class ExtractContentRequest(BaseModel):
    """Request to extract specific content."""
    file_path: str = Field(..., description="Path to the file to extract from")
    section_ids: Optional[List[str]] = Field(None, description="Specific section IDs to extract")
    patterns: Optional[List[str]] = Field(None, description="Regex patterns to match content")
    categories: Optional[List[str]] = Field(None, description="Categories to extract")
    preserve_context: bool = Field(True, description="Include surrounding context")
    update_references: bool = Field(True, description="Update references in source")
    dry_run: bool = Field(False, description="Preview extraction without changes")
    output_dir: Optional[str] = Field(None, description="Output directory for extracted content")
    

class ExtractedSection(BaseModel):
    """Information about an extracted section."""
    section_id: str
    title: str
    category: str
    content: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    output_file: Optional[str] = None
    

class ExtractContentResponse(BaseModel):
    """Response from extract content."""
    success: bool
    document_id: str
    extracted_sections: List[ExtractedSection]
    total_extracted: int
    categories_extracted: List[str]
    output_files: List[str]
    references_updated: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time: float
    dry_run: bool


class ExtractContentTool(BaseTool):
    """Tool for extracting specific content sections."""
    
    def __init__(self, config, event_bus=None):
        super().__init__("extract_content", config, event_bus)
        self.extractor: Optional[ContentExtractor] = None
        
    async def initialize(self) -> None:
        """Initialize tool components."""
        self.extractor = ContentExtractor(self.config.processing, self.event_bus)
        await self.extractor.initialize()
        
    async def execute(self, request: ExtractContentRequest) -> ExtractContentResponse:
        """Execute the extract content tool."""
        start_time = time.time()
        
        # Initialize if needed
        if not self.extractor:
            await self.initialize()
            
        try:
            # Parse the document
            file_path = Path(request.file_path)
            if not file_path.exists():
                return ExtractContentResponse(
                    success=False,
                    document_id="",
                    extracted_sections=[],
                    total_extracted=0,
                    categories_extracted=[],
                    output_files=[],
                    references_updated=False,
                    errors=[f"File not found: {file_path}"],
                    processing_time=time.time() - start_time,
                    dry_run=request.dry_run
                )
                
            # Get parser and parse document
            parser = get_parser(file_path, self.event_bus)
            if not parser:
                return ExtractContentResponse(
                    success=False,
                    document_id="",
                    extracted_sections=[],
                    total_extracted=0,
                    categories_extracted=[],
                    output_files=[],
                    references_updated=False,
                    errors=[f"No parser available for {file_path}"],
                    processing_time=time.time() - start_time,
                    dry_run=request.dry_run
                )
                
            await parser.initialize()
            content = file_path.read_text(encoding='utf-8')
            document = await parser.parse(content, file_path)
            
            # Extract sections based on criteria
            extracted_sections = []
            categories_extracted = set()
            
            # If specific section IDs provided
            if request.section_ids:
                sections_to_extract = [
                    s for s in document.sections 
                    if s.id in request.section_ids
                ]
            else:
                sections_to_extract = document.sections
                
            # Apply pattern matching if specified
            if request.patterns:
                import re
                pattern_sections = []
                for section in sections_to_extract:
                    for pattern in request.patterns:
                        if re.search(pattern, section.content, re.IGNORECASE):
                            pattern_sections.append(section)
                            break
                sections_to_extract = pattern_sections
                
            # Extract content from selected sections
            if not request.dry_run:
                # Configure extractor
                if request.categories:
                    self.config.processing.extract_categories = [
                        ExtractionCategory(cat) if cat in [e.value for e in ExtractionCategory]
                        else cat
                        for cat in request.categories
                    ]
                    
                extracted_contents = await self.extractor.extract_from_sections(
                    document, sections_to_extract
                )
            else:
                # For dry run, simulate extraction
                extracted_contents = []
                for section in sections_to_extract:
                    # Detect category
                    from ...extractor import CategoryDetector
                    detector = CategoryDetector()
                    category, confidence = detector.detect_category(section.content, section.title)
                    if request.categories and category.value not in request.categories:
                        continue
                        
                    extracted_contents.append(
                        ExtractedContent(
                            id=f"{document.id}_{section.id}",
                            document_id=document.id,
                            category=category,
                            title=section.title,
                            content=section.content,
                            source_section=section.id
                        )
                    )
                    
            # Build response sections
            output_files = []
            for content in extracted_contents:
                categories_extracted.add(content.category.value if hasattr(content.category, 'value') else content.category)
                
                # Get context if requested
                context_before = None
                context_after = None
                if request.preserve_context:
                    context_before, context_after = self._get_section_context(
                        document, content.source_section
                    )
                    
                extracted_section = ExtractedSection(
                    section_id=content.source_section or content.id,
                    title=content.title,
                    category=content.category.value if hasattr(content.category, 'value') else content.category,
                    content=content.content,
                    context_before=context_before,
                    context_after=context_after
                )
                extracted_sections.append(extracted_section)
                
            # Save extracted content if not dry run
            if not request.dry_run and extracted_contents:
                output_dir = Path(request.output_dir) if request.output_dir else self.config.organization.output_dir
                
                from ...organizer import DocumentOrganizer
                organizer = DocumentOrganizer(self.config.organization, self.event_bus)
                await organizer.initialize()
                
                organized = await organizer.organize(extracted_contents)
                saved_files = await organizer.save(organized, output_dir)
                output_files = [str(f) for f in saved_files]
                
                # Update output files in sections
                for section, file_path in zip(extracted_sections, output_files):
                    section.output_file = file_path
                    
            # Update references if requested
            references_updated = False
            if not request.dry_run and request.update_references and extracted_contents:
                references_updated = await self._update_references(
                    document, extracted_contents, file_path
                )
                
            return ExtractContentResponse(
                success=True,
                document_id=document.id,
                extracted_sections=extracted_sections,
                total_extracted=len(extracted_sections),
                categories_extracted=list(categories_extracted),
                output_files=output_files,
                references_updated=references_updated,
                processing_time=time.time() - start_time,
                dry_run=request.dry_run
            )
            
        except Exception as e:
            self._logger.error("extract_content_failed", error=str(e))
            return ExtractContentResponse(
                success=False,
                document_id="",
                extracted_sections=[],
                total_extracted=0,
                categories_extracted=[],
                output_files=[],
                references_updated=False,
                errors=[str(e)],
                processing_time=time.time() - start_time,
                dry_run=request.dry_run
            )
            
    def _get_section_context(self, document, section_id: str, context_size: int = 200):
        """Get context before and after a section."""
        # Find section index
        section_idx = None
        for i, section in enumerate(document.sections):
            if section.id == section_id:
                section_idx = i
                break
                
        if section_idx is None:
            return None, None
            
        # Get previous section content (last N characters)
        context_before = None
        if section_idx > 0:
            prev_section = document.sections[section_idx - 1]
            if len(prev_section.content) > context_size:
                context_before = "..." + prev_section.content[-context_size:]
            else:
                context_before = prev_section.content
                
        # Get next section content (first N characters)
        context_after = None
        if section_idx < len(document.sections) - 1:
            next_section = document.sections[section_idx + 1]
            if len(next_section.content) > context_size:
                context_after = next_section.content[:context_size] + "..."
            else:
                context_after = next_section.content
                
        return context_before, context_after
        
    async def _update_references(self, document, extracted_contents, source_path) -> bool:
        """Update references in the source document."""
        try:
            # This would be implemented to add reference links
            # For now, just log
            self._logger.info(
                "would_update_references",
                document_id=document.id,
                extracted_count=len(extracted_contents),
                source_path=str(source_path)
            )
            return True
        except Exception as e:
            self._logger.error("update_references_failed", error=str(e))
            return False