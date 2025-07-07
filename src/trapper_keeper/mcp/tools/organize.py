"""Organize documentation tool for MCP."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool
from ...core.types import ExtractionCategory, ProcessingResult
from ...parser import get_parser
from ...extractor import ContentExtractor, CategoryDetector
from ...organizer import DocumentOrganizer


class OrganizeDocumentationRequest(BaseModel):
    """Request to organize documentation."""
    file_path: str = Field(..., description="Path to CLAUDE.md or similar file to organize")
    dry_run: bool = Field(False, description="Simulate without making changes")
    output_dir: Optional[str] = Field(None, description="Output directory for organized content")
    categories: Optional[List[str]] = Field(None, description="Specific categories to extract")
    min_importance: float = Field(0.5, ge=0.0, le=1.0, description="Minimum importance threshold")
    create_references: bool = Field(True, description="Create reference links in source document")
    
    
class ExtractionSuggestion(BaseModel):
    """Suggestion for content extraction."""
    section_id: str
    title: str
    category: str
    importance: float
    reason: str
    content_preview: str
    

class OrganizeDocumentationResponse(BaseModel):
    """Response from organize documentation."""
    success: bool
    document_id: str
    suggestions: List[ExtractionSuggestion]
    extracted_count: int
    categories_found: List[str]
    output_files: List[str]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time: float
    dry_run: bool


class OrganizeDocumentationTool(BaseTool):
    """Tool for organizing and extracting documentation content."""
    
    def __init__(self, config, event_bus=None):
        super().__init__("organize_documentation", config, event_bus)
        self.extractor: Optional[ContentExtractor] = None
        self.organizer: Optional[DocumentOrganizer] = None
        self.category_detector: Optional[CategoryDetector] = None
        
    async def initialize(self) -> None:
        """Initialize tool components."""
        self.extractor = ContentExtractor(self.config.processing, self.event_bus)
        self.organizer = DocumentOrganizer(self.config.organization, self.event_bus)
        self.category_detector = CategoryDetector(self.config.processing, self.event_bus)
        
        await self.extractor.initialize()
        await self.organizer.initialize()
        await self.category_detector.initialize()
        
    async def execute(self, request: OrganizeDocumentationRequest) -> OrganizeDocumentationResponse:
        """Execute the organize documentation tool."""
        start_time = time.time()
        
        # Initialize if needed
        if not self.extractor:
            await self.initialize()
            
        try:
            # Parse the document
            file_path = Path(request.file_path)
            if not file_path.exists():
                return OrganizeDocumentationResponse(
                    success=False,
                    document_id="",
                    suggestions=[],
                    extracted_count=0,
                    categories_found=[],
                    output_files=[],
                    errors=[f"File not found: {file_path}"],
                    processing_time=time.time() - start_time,
                    dry_run=request.dry_run
                )
                
            # Get parser and parse document
            parser = get_parser(file_path, self.event_bus)
            if not parser:
                return OrganizeDocumentationResponse(
                    success=False,
                    document_id="",
                    suggestions=[],
                    extracted_count=0,
                    categories_found=[],
                    output_files=[],
                    errors=[f"No parser available for {file_path}"],
                    processing_time=time.time() - start_time,
                    dry_run=request.dry_run
                )
                
            await parser.initialize()
            content = file_path.read_text(encoding='utf-8')
            document = await parser.parse(content, file_path)
            
            # Generate extraction suggestions
            suggestions = []
            categories_found = set()
            
            for section in document.sections:
                # Detect category
                category, confidence = self.category_detector.detect_category(section.content, section.title)
                if category == ExtractionCategory.CUSTOM:
                    continue
                    
                # Calculate importance
                importance = self._calculate_importance(section, category)
                
                if importance >= request.min_importance:
                    categories_found.add(category.value)
                    
                    suggestion = ExtractionSuggestion(
                        section_id=section.id,
                        title=section.title,
                        category=category.value,
                        importance=importance,
                        reason=self._generate_extraction_reason(section, category, importance),
                        content_preview=section.content[:200] + "..." if len(section.content) > 200 else section.content
                    )
                    suggestions.append(suggestion)
                    
            # Filter by requested categories if specified
            if request.categories:
                suggestions = [s for s in suggestions if s.category in request.categories]
                categories_found = categories_found.intersection(set(request.categories))
                
            # If not dry run, perform extraction
            output_files = []
            extracted_count = 0
            
            if not request.dry_run and suggestions:
                # Update config if needed
                if request.categories:
                    self.config.processing.extract_categories = request.categories
                self.config.processing.min_importance = request.min_importance
                
                # Extract content
                extracted_contents = await self.extractor.extract(document)
                extracted_count = len(extracted_contents)
                
                # Organize and save
                if extracted_contents:
                    output_dir = Path(request.output_dir) if request.output_dir else self.config.organization.output_dir
                    self.config.organization.output_dir = output_dir
                    
                    organized = await self.organizer.organize(extracted_contents)
                    saved_files = await self.organizer.save(organized)
                    output_files = [str(f) for f in saved_files]
                    
                    # Create references if requested
                    if request.create_references:
                        await self._create_references(document, extracted_contents, file_path)
                        
            return OrganizeDocumentationResponse(
                success=True,
                document_id=document.id,
                suggestions=suggestions,
                extracted_count=extracted_count,
                categories_found=list(categories_found),
                output_files=output_files,
                processing_time=time.time() - start_time,
                dry_run=request.dry_run
            )
            
        except Exception as e:
            self._logger.error("organize_documentation_failed", error=str(e))
            return OrganizeDocumentationResponse(
                success=False,
                document_id="",
                suggestions=[],
                extracted_count=0,
                categories_found=[],
                output_files=[],
                errors=[str(e)],
                processing_time=time.time() - start_time,
                dry_run=request.dry_run
            )
            
    def _calculate_importance(self, section, category) -> float:
        """Calculate importance score for a section."""
        score = 0.5  # Base score
        
        # Adjust based on category
        critical_categories = {
            ExtractionCategory.CRITICAL,
            ExtractionCategory.SECURITY,
            ExtractionCategory.ARCHITECTURE
        }
        if category in critical_categories:
            score += 0.2
            
        # Adjust based on content indicators
        important_keywords = [
            "IMPORTANT", "CRITICAL", "WARNING", "REQUIRED",
            "MUST", "ESSENTIAL", "KEY", "CORE"
        ]
        content_upper = section.content.upper()
        for keyword in important_keywords:
            if keyword in content_upper:
                score += 0.1
                break
                
        # Adjust based on section level (higher level = more important)
        if section.level <= 2:
            score += 0.1
            
        # Adjust based on content length
        if len(section.content) > 500:
            score += 0.1
            
        return min(score, 1.0)
        
    def _generate_extraction_reason(self, section, category, importance) -> str:
        """Generate a reason for extraction suggestion."""
        reasons = []
        
        if importance >= 0.8:
            reasons.append("High importance content")
        elif importance >= 0.6:
            reasons.append("Moderately important content")
            
        if category == ExtractionCategory.CRITICAL:
            reasons.append("Contains critical information")
        elif category == ExtractionCategory.SECURITY:
            reasons.append("Security-related content")
        elif category == ExtractionCategory.ARCHITECTURE:
            reasons.append("Architectural decisions")
            
        if section.level <= 2:
            reasons.append("Top-level section")
            
        return "; ".join(reasons) if reasons else "Relevant content for extraction"
        
    async def _create_references(self, document, extracted_contents, source_path) -> None:
        """Create reference links in the source document."""
        # This would be implemented by the CreateReferenceTool
        # For now, just log
        self._logger.info(
            "would_create_references",
            document_id=document.id,
            extracted_count=len(extracted_contents),
            source_path=str(source_path)
        )