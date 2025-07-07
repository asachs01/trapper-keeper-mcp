"""Validate structure tool for MCP."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from .base import BaseTool


class ValidateStructureRequest(BaseModel):
    """Request to validate documentation structure."""
    root_dir: str = Field(..., description="Root directory to validate")
    source_files: Optional[List[str]] = Field(None, description="Specific source files to check")
    check_references: bool = Field(True, description="Validate all references are valid")
    check_orphans: bool = Field(True, description="Find orphaned documents")
    check_structure: bool = Field(True, description="Verify directory structure")
    patterns: List[str] = Field(["*.md", "*.txt"], description="File patterns to validate")
    

class ValidationIssue(BaseModel):
    """A validation issue found."""
    type: str  # "broken_reference", "orphaned_file", "missing_category", etc.
    severity: str  # "error", "warning", "info"
    file_path: str
    message: str
    details: Optional[Dict[str, Any]] = None
    

class FileValidation(BaseModel):
    """Validation results for a single file."""
    file_path: str
    is_valid: bool
    has_references: bool
    reference_count: int
    broken_references: List[str]
    categories_found: List[str]
    issues: List[ValidationIssue]
    

class ValidateStructureResponse(BaseModel):
    """Response from validate structure."""
    success: bool
    root_dir: str
    total_files_checked: int
    valid_files: int
    files_with_issues: int
    orphaned_files: List[str]
    broken_references: List[Dict[str, str]]  # {"source": "...", "target": "..."}
    file_validations: List[FileValidation]
    structure_valid: bool
    issues: List[ValidationIssue]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time: float


class ValidateStructureTool(BaseTool):
    """Tool for validating documentation structure and references."""
    
    def __init__(self, config, event_bus=None):
        super().__init__("validate_structure", config, event_bus)
        
    async def execute(self, request: ValidateStructureRequest) -> ValidateStructureResponse:
        """Execute the validate structure tool."""
        start_time = time.time()
        
        try:
            root_path = Path(request.root_dir)
            if not root_path.exists():
                return ValidateStructureResponse(
                    success=False,
                    root_dir=request.root_dir,
                    total_files_checked=0,
                    valid_files=0,
                    files_with_issues=0,
                    orphaned_files=[],
                    broken_references=[],
                    file_validations=[],
                    structure_valid=False,
                    issues=[],
                    errors=[f"Root directory not found: {root_path}"],
                    processing_time=time.time() - start_time
                )
                
            # Collect all files to validate
            files_to_check = []
            if request.source_files:
                files_to_check = [Path(f) for f in request.source_files if Path(f).exists()]
            else:
                # Find all matching files
                for pattern in request.patterns:
                    files_to_check.extend(root_path.rglob(pattern))
                    
            # Validate each file
            file_validations = []
            all_issues = []
            all_references = {}  # Map of file -> list of references
            referenced_files = set()  # Files that are referenced by others
            
            for file_path in files_to_check:
                validation = await self._validate_file(file_path, root_path, request)
                file_validations.append(validation)
                
                if validation.issues:
                    all_issues.extend(validation.issues)
                    
                # Track references
                if validation.has_references:
                    all_references[str(file_path)] = validation.broken_references
                    
                # Extract referenced files from content
                referenced_files.update(
                    self._extract_referenced_files(file_path, root_path)
                )
                
            # Find orphaned files if requested
            orphaned_files = []
            if request.check_orphans:
                all_file_paths = {str(f) for f in files_to_check}
                orphaned_files = [
                    f for f in all_file_paths 
                    if f not in referenced_files and not self._is_index_file(Path(f))
                ]
                
                # Add orphan issues
                for orphan in orphaned_files:
                    issue = ValidationIssue(
                        type="orphaned_file",
                        severity="warning",
                        file_path=orphan,
                        message="File is not referenced by any other document"
                    )
                    all_issues.append(issue)
                    
            # Collect all broken references
            broken_references = []
            for source, broken_refs in all_references.items():
                for ref in broken_refs:
                    broken_references.append({
                        "source": source,
                        "target": ref
                    })
                    
            # Validate structure if requested
            structure_valid = True
            if request.check_structure:
                structure_issues = await self._validate_directory_structure(
                    root_path, self.config.organization.output_dir
                )
                all_issues.extend(structure_issues)
                if any(i.severity == "error" for i in structure_issues):
                    structure_valid = False
                    
            # Calculate summary stats
            valid_files = sum(1 for v in file_validations if v.is_valid)
            files_with_issues = sum(1 for v in file_validations if v.issues)
            
            return ValidateStructureResponse(
                success=True,
                root_dir=request.root_dir,
                total_files_checked=len(file_validations),
                valid_files=valid_files,
                files_with_issues=files_with_issues,
                orphaned_files=orphaned_files,
                broken_references=broken_references,
                file_validations=file_validations,
                structure_valid=structure_valid,
                issues=all_issues,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            self._logger.error("validate_structure_failed", error=str(e))
            return ValidateStructureResponse(
                success=False,
                root_dir=request.root_dir,
                total_files_checked=0,
                valid_files=0,
                files_with_issues=0,
                orphaned_files=[],
                broken_references=[],
                file_validations=[],
                structure_valid=False,
                issues=[],
                errors=[str(e)],
                processing_time=time.time() - start_time
            )
            
    async def _validate_file(
        self, 
        file_path: Path, 
        root_path: Path,
        request: ValidateStructureRequest
    ) -> FileValidation:
        """Validate a single file."""
        issues = []
        broken_references = []
        categories_found = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for references
            references = self._extract_references(content)
            has_references = len(references) > 0
            
            # Validate references if requested
            if request.check_references and references:
                for ref in references:
                    ref_path = self._resolve_reference(ref, file_path, root_path)
                    if not ref_path or not ref_path.exists():
                        broken_references.append(ref)
                        issues.append(ValidationIssue(
                            type="broken_reference",
                            severity="error",
                            file_path=str(file_path),
                            message=f"Broken reference: {ref}",
                            details={"reference": ref}
                        ))
                        
            # Check for categories
            categories_found = self._extract_categories(content)
            if not categories_found:
                issues.append(ValidationIssue(
                    type="missing_category",
                    severity="warning",
                    file_path=str(file_path),
                    message="No category information found",
                    details={}
                ))
                
            # Check file structure
            if not self._validate_file_structure(content):
                issues.append(ValidationIssue(
                    type="invalid_structure",
                    severity="warning",
                    file_path=str(file_path),
                    message="File structure does not follow expected format",
                    details={}
                ))
                
            is_valid = len([i for i in issues if i.severity == "error"]) == 0
            
            return FileValidation(
                file_path=str(file_path),
                is_valid=is_valid,
                has_references=has_references,
                reference_count=len(references),
                broken_references=broken_references,
                categories_found=categories_found,
                issues=issues
            )
            
        except Exception as e:
            return FileValidation(
                file_path=str(file_path),
                is_valid=False,
                has_references=False,
                reference_count=0,
                broken_references=[],
                categories_found=[],
                issues=[ValidationIssue(
                    type="read_error",
                    severity="error",
                    file_path=str(file_path),
                    message=f"Failed to read file: {str(e)}",
                    details={}
                )]
            )
            
    def _extract_references(self, content: str) -> List[str]:
        """Extract all references from content."""
        import re
        references = []
        
        # Markdown links: [text](path)
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        references.extend([link[1] for link in md_links if not link[1].startswith('http')])
        
        # Reference-style links: [text][ref]
        ref_links = re.findall(r'\[([^\]]+)\]\[([^\]]+)\]', content)
        # Find corresponding definitions
        for _, ref_id in ref_links:
            ref_def = re.search(rf'\[{re.escape(ref_id)}\]:\s*(.+)', content)
            if ref_def and not ref_def.group(1).startswith('http'):
                references.append(ref_def.group(1))
                
        return references
        
    def _extract_referenced_files(self, file_path: Path, root_path: Path) -> Set[str]:
        """Extract all files referenced by this file."""
        referenced = set()
        
        try:
            content = file_path.read_text(encoding='utf-8')
            references = self._extract_references(content)
            
            for ref in references:
                ref_path = self._resolve_reference(ref, file_path, root_path)
                if ref_path and ref_path.exists():
                    referenced.add(str(ref_path))
                    
        except Exception as e:
            self._logger.error("extract_referenced_files_failed", error=str(e))
            
        return referenced
        
    def _resolve_reference(self, ref: str, source_file: Path, root_path: Path) -> Optional[Path]:
        """Resolve a reference to an absolute path."""
        try:
            # Clean the reference
            ref = ref.strip()
            if ref.startswith('#'):  # Internal anchor
                return None
                
            # Try relative to source file
            ref_path = source_file.parent / ref
            if ref_path.exists():
                return ref_path.resolve()
                
            # Try relative to root
            ref_path = root_path / ref
            if ref_path.exists():
                return ref_path.resolve()
                
            # Try as absolute path
            ref_path = Path(ref)
            if ref_path.exists():
                return ref_path.resolve()
                
            return None
            
        except Exception:
            return None
            
    def _extract_categories(self, content: str) -> List[str]:
        """Extract categories from content."""
        categories = []
        
        # Look for category in frontmatter
        if content.startswith("---"):
            try:
                import yaml
                frontmatter_end = content.find("---", 3)
                if frontmatter_end > 0:
                    frontmatter = content[3:frontmatter_end]
                    data = yaml.safe_load(frontmatter) or {}
                    if "category" in data:
                        categories.append(data["category"])
                    if "categories" in data:
                        categories.extend(data["categories"])
            except:
                pass
                
        # Look for category headers
        import re
        category_matches = re.findall(
            r'(?:Category|Categories):\s*(.+)',
            content, 
            re.IGNORECASE
        )
        for match in category_matches:
            categories.extend([c.strip() for c in match.split(',')])
            
        return list(set(categories))  # Remove duplicates
        
    def _validate_file_structure(self, content: str) -> bool:
        """Validate that file follows expected structure."""
        # Check for basic structure elements
        has_title = content.strip().startswith('#') or '---' in content[:10]
        has_content = len(content.strip()) > 50  # Arbitrary minimum
        
        return has_title and has_content
        
    def _is_index_file(self, file_path: Path) -> bool:
        """Check if file is an index file."""
        index_names = ['index', 'readme', 'toc', 'contents']
        return file_path.stem.lower() in index_names
        
    async def _validate_directory_structure(
        self, 
        root_path: Path,
        expected_output_dir: Path
    ) -> List[ValidationIssue]:
        """Validate directory structure follows expected organization."""
        issues = []
        
        # Check if output directory exists
        if not expected_output_dir.exists():
            issues.append(ValidationIssue(
                type="missing_directory",
                severity="info",
                file_path=str(expected_output_dir),
                message="Expected output directory does not exist"
            ))
            
        # Check for expected category directories
        from ...core.types import ExtractionCategory
        
        if expected_output_dir.exists() and self.config.organization.group_by_category:
            for category in ExtractionCategory:
                category_dir = expected_output_dir / category.value
                if not category_dir.exists():
                    issues.append(ValidationIssue(
                        type="missing_category_dir",
                        severity="info",
                        file_path=str(category_dir),
                        message=f"Category directory missing: {category.value}"
                    ))
                    
        return issues