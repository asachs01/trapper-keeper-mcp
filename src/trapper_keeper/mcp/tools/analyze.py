"""Analyze document tool for MCP."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from collections import Counter

from .base import BaseTool
from ...parser import get_parser
from ...core.types import ExtractionCategory


class AnalyzeDocumentRequest(BaseModel):
    """Request to analyze a document."""
    file_path: str = Field(..., description="Path to document to analyze")
    include_statistics: bool = Field(True, description="Include detailed statistics")
    include_growth: bool = Field(True, description="Analyze growth patterns")
    include_recommendations: bool = Field(True, description="Provide extraction recommendations")
    days_for_growth: int = Field(30, description="Number of days to analyze for growth")
    

class DocumentStatistics(BaseModel):
    """Statistical information about a document."""
    total_size: int
    total_lines: int
    total_sections: int
    section_depth_distribution: Dict[int, int]  # level -> count
    average_section_size: float
    code_block_count: int
    link_count: int
    image_count: int
    

class CategoryDistribution(BaseModel):
    """Distribution of content by category."""
    category: str
    section_count: int
    estimated_size: int
    percentage: float
    

class GrowthPattern(BaseModel):
    """Growth pattern information."""
    period_days: int
    lines_added: int
    sections_added: int
    growth_rate: float  # percentage
    most_active_categories: List[str]
    

class ExtractionRecommendation(BaseModel):
    """Recommendation for content extraction."""
    section_id: str
    title: str
    category: str
    reason: str
    priority: str  # "high", "medium", "low"
    estimated_impact: str
    

class AnalyzeDocumentResponse(BaseModel):
    """Response from analyze document."""
    success: bool
    document_id: str
    file_path: str
    last_modified: str
    statistics: Optional[DocumentStatistics] = None
    category_distribution: List[CategoryDistribution] = Field(default_factory=list)
    growth_patterns: Optional[GrowthPattern] = None
    recommendations: List[ExtractionRecommendation] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time: float


class AnalyzeDocumentTool(BaseTool):
    """Tool for analyzing documents and providing insights."""
    
    def __init__(self, config, event_bus=None):
        super().__init__("analyze_document", config, event_bus)
        
    async def execute(self, request: AnalyzeDocumentRequest) -> AnalyzeDocumentResponse:
        """Execute the analyze document tool."""
        start_time = time.time()
        
        try:
            # Validate file
            file_path = Path(request.file_path)
            if not file_path.exists():
                return AnalyzeDocumentResponse(
                    success=False,
                    document_id="",
                    file_path=request.file_path,
                    last_modified="",
                    errors=[f"File not found: {file_path}"],
                    processing_time=time.time() - start_time
                )
                
            # Get file metadata
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Parse document
            parser = get_parser(file_path, self.event_bus)
            if not parser:
                return AnalyzeDocumentResponse(
                    success=False,
                    document_id="",
                    file_path=request.file_path,
                    last_modified=last_modified,
                    errors=[f"No parser available for {file_path}"],
                    processing_time=time.time() - start_time
                )
                
            await parser.initialize()
            content = file_path.read_text(encoding='utf-8')
            document = await parser.parse(content, file_path)
            
            # Gather statistics if requested
            statistics = None
            if request.include_statistics:
                statistics = await self._calculate_statistics(document, content)
                
            # Analyze category distribution
            category_distribution = await self._analyze_categories(document)
            
            # Analyze growth patterns if requested
            growth_patterns = None
            if request.include_growth:
                growth_patterns = await self._analyze_growth(
                    file_path, document, request.days_for_growth
                )
                
            # Generate recommendations if requested
            recommendations = []
            if request.include_recommendations:
                recommendations = await self._generate_recommendations(
                    document, statistics, category_distribution
                )
                
            # Generate insights
            insights = self._generate_insights(
                document, statistics, category_distribution, growth_patterns
            )
            
            return AnalyzeDocumentResponse(
                success=True,
                document_id=document.id,
                file_path=request.file_path,
                last_modified=last_modified,
                statistics=statistics,
                category_distribution=category_distribution,
                growth_patterns=growth_patterns,
                recommendations=recommendations,
                insights=insights,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            self._logger.error("analyze_document_failed", error=str(e))
            return AnalyzeDocumentResponse(
                success=False,
                document_id="",
                file_path=request.file_path,
                last_modified="",
                errors=[str(e)],
                processing_time=time.time() - start_time
            )
            
    async def _calculate_statistics(self, document, content: str) -> DocumentStatistics:
        """Calculate document statistics."""
        lines = content.split('\n')
        
        # Section depth distribution
        depth_distribution = Counter()
        total_section_size = 0
        
        for section in document.sections:
            depth_distribution[section.level] += 1
            total_section_size += len(section.content)
            
        # Count code blocks, links, and images
        import re
        code_blocks = len(re.findall(r'```[\s\S]*?```', content))
        links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        images = len(re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content))
        
        return DocumentStatistics(
            total_size=len(content),
            total_lines=len(lines),
            total_sections=len(document.sections),
            section_depth_distribution=dict(depth_distribution),
            average_section_size=total_section_size / len(document.sections) if document.sections else 0,
            code_block_count=code_blocks,
            link_count=links,
            image_count=images
        )
        
    async def _analyze_categories(self, document) -> List[CategoryDistribution]:
        """Analyze content distribution by category."""
        from ...extractor import CategoryDetector
        
        detector = CategoryDetector()
        
        category_counts = Counter()
        category_sizes = Counter()
        
        for section in document.sections:
            category, confidence = detector.detect_category(section.content, section.title)
            if category != ExtractionCategory.CUSTOM:
                category_counts[category.value] += 1
                category_sizes[category.value] += len(section.content)
                
        total_size = sum(category_sizes.values())
        
        distributions = []
        for category, count in category_counts.most_common():
            distributions.append(CategoryDistribution(
                category=category,
                section_count=count,
                estimated_size=category_sizes[category],
                percentage=(category_sizes[category] / total_size * 100) if total_size > 0 else 0
            ))
            
        return distributions
        
    async def _analyze_growth(
        self, 
        file_path: Path, 
        document,
        days: int
    ) -> Optional[GrowthPattern]:
        """Analyze document growth patterns."""
        try:
            # This is a simplified version - in practice would use git history
            # or file versioning to track actual growth
            
            # For now, provide estimated growth based on document characteristics
            total_sections = len(document.sections)
            estimated_growth_rate = 10.0  # Default 10% growth estimate
            
            # Adjust based on document size
            if total_sections > 50:
                estimated_growth_rate = 5.0  # Larger docs grow slower
            elif total_sections < 10:
                estimated_growth_rate = 20.0  # Smaller docs grow faster
                
            # Find most active categories (top 3)
            category_counts = Counter()
            for section in document.sections:
                # Simple heuristic based on section metadata
                if "recent" in section.title.lower() or "new" in section.title.lower():
                    category_counts["Recent Updates"] += 1
                    
            most_active = [cat for cat, _ in category_counts.most_common(3)]
            if not most_active:
                most_active = ["General Updates"]
                
            return GrowthPattern(
                period_days=days,
                lines_added=int(len(document.content.split('\n')) * estimated_growth_rate / 100),
                sections_added=int(total_sections * estimated_growth_rate / 100),
                growth_rate=estimated_growth_rate,
                most_active_categories=most_active
            )
            
        except Exception as e:
            self._logger.error("analyze_growth_failed", error=str(e))
            return None
            
    async def _generate_recommendations(
        self,
        document,
        statistics: Optional[DocumentStatistics],
        category_distribution: List[CategoryDistribution]
    ) -> List[ExtractionRecommendation]:
        """Generate extraction recommendations."""
        recommendations = []
        
        # Find large sections that could be extracted
        if statistics:
            avg_size = statistics.average_section_size
            for section in document.sections:
                if len(section.content) > avg_size * 2:  # Section is 2x average size
                    recommendations.append(ExtractionRecommendation(
                        section_id=section.id,
                        title=section.title,
                        category="Large Content",
                        reason="Section is significantly larger than average",
                        priority="high",
                        estimated_impact="Reduce document complexity"
                    ))
                    
        # Find categories with high concentration
        total_sections = sum(dist.section_count for dist in category_distribution)
        for dist in category_distribution:
            if dist.percentage > 30:  # More than 30% of content
                # Find sections in this category
                from ...extractor import CategoryDetector
                detector = CategoryDetector()
                
                for section in document.sections[:5]:  # Check first 5 sections
                    category, _ = detector.detect_category(section.content, section.title)
                    if category.value == dist.category:
                        recommendations.append(ExtractionRecommendation(
                            section_id=section.id,
                            title=section.title,
                            category=dist.category,
                            reason=f"High concentration of {dist.category} content",
                            priority="medium",
                            estimated_impact="Better content organization"
                        ))
                        break
                        
        # Find critical sections
        critical_keywords = ["IMPORTANT", "CRITICAL", "URGENT", "REQUIRED"]
        for section in document.sections:
            if any(keyword in section.content.upper() for keyword in critical_keywords):
                recommendations.append(ExtractionRecommendation(
                    section_id=section.id,
                    title=section.title,
                    category="Critical",
                    reason="Contains critical information",
                    priority="high",
                    estimated_impact="Ensure critical info is highlighted"
                ))
                
        # Limit recommendations
        return recommendations[:10]
        
    def _generate_insights(
        self,
        document,
        statistics: Optional[DocumentStatistics],
        category_distribution: List[CategoryDistribution],
        growth_patterns: Optional[GrowthPattern]
    ) -> List[str]:
        """Generate insights about the document."""
        insights = []
        
        # Document size insights
        if statistics:
            if statistics.total_lines > 1000:
                insights.append(
                    f"Large document with {statistics.total_lines} lines. "
                    "Consider extracting major sections for better organization."
                )
            elif statistics.total_lines < 100:
                insights.append(
                    "Small document. May not require extensive organization yet."
                )
                
            # Code content insights
            if statistics.code_block_count > 10:
                insights.append(
                    f"High code content ({statistics.code_block_count} blocks). "
                    "Consider extracting code examples to separate files."
                )
                
            # Structure insights
            if statistics.section_depth_distribution.get(1, 0) > 20:
                insights.append(
                    "Many top-level sections. Consider grouping related sections."
                )
                
        # Category insights
        if category_distribution:
            top_category = category_distribution[0]
            if top_category.percentage > 40:
                insights.append(
                    f"{top_category.category} dominates ({top_category.percentage:.1f}%). "
                    "Consider dedicated document for this category."
                )
                
            # Diversity insight
            if len(category_distribution) > 5:
                insights.append(
                    "Diverse content across many categories. "
                    "Good candidate for category-based extraction."
                )
                
        # Growth insights
        if growth_patterns:
            if growth_patterns.growth_rate > 15:
                insights.append(
                    f"Fast growth rate ({growth_patterns.growth_rate:.1f}%). "
                    "Regular organization will help maintain clarity."
                )
                
        # General insights
        if not insights:
            insights.append(
                "Document appears well-structured. "
                "Monitor growth and extract sections as needed."
            )
            
        return insights