# MCP Tools Reference

## Overview

Trapper Keeper MCP provides a comprehensive set of tools for managing and organizing documentation through the Model Context Protocol (MCP). These tools are designed to work together seamlessly, enabling intelligent content extraction, organization, and maintenance of documentation structure.

## Core Tools

### 1. `organize_documentation`

**Purpose**: Main orchestration tool that analyzes a document and suggests/executes content extraction.

**Parameters**:
- `file_path` (required): Path to CLAUDE.md or similar documentation file
- `dry_run` (default: false): Preview suggestions without making changes
- `output_dir`: Directory for organized content (uses config default if not provided)
- `categories`: Specific categories to extract (all by default)
- `min_importance` (default: 0.5): Minimum importance threshold (0.0-1.0)
- `create_references` (default: true): Create reference links in source document

**Example**:
```python
await organize_documentation(
    file_path="/path/to/CLAUDE.md",
    dry_run=True,
    categories=["🔐 Security", "🏗️ Architecture"],
    min_importance=0.6
)
```

**Response**:
```json
{
    "success": true,
    "document_id": "doc_123",
    "suggestions": [
        {
            "section_id": "sec1",
            "title": "Security Configuration",
            "category": "🔐 Security",
            "importance": 0.85,
            "reason": "High importance content; Security-related content",
            "content_preview": "Critical security settings..."
        }
    ],
    "extracted_count": 0,  // 0 for dry_run
    "categories_found": ["🔐 Security", "🏗️ Architecture"],
    "output_files": [],
    "dry_run": true
}
```

### 2. `extract_content`

**Purpose**: Extract specific sections from a document based on various criteria.

**Parameters**:
- `file_path` (required): Path to the file to extract from
- `section_ids`: Specific section IDs to extract
- `patterns`: Regex patterns to match content
- `categories`: Categories to extract
- `preserve_context` (default: true): Include surrounding context
- `update_references` (default: true): Update references in source
- `dry_run` (default: false): Preview extraction without changes
- `output_dir`: Output directory for extracted content

**Example**:
```python
await extract_content(
    file_path="/path/to/CLAUDE.md",
    patterns=["API", "endpoint"],
    categories=["🌐 API"],
    preserve_context=True
)
```

**Response**:
```json
{
    "success": true,
    "document_id": "doc_123",
    "extracted_sections": [
        {
            "section_id": "sec3",
            "title": "API Documentation",
            "category": "🌐 API",
            "content": "REST API endpoints...",
            "context_before": "Previous section content...",
            "context_after": "Next section content...",
            "output_file": "/output/api/rest-endpoints.md"
        }
    ],
    "total_extracted": 1,
    "categories_extracted": ["🌐 API"],
    "output_files": ["/output/api/rest-endpoints.md"],
    "references_updated": true
}
```

### 3. `create_reference`

**Purpose**: Create reference links between source documents and extracted content.

**Parameters**:
- `source_file` (required): Path to source file that was extracted from
- `extracted_files` (required): List of extracted content files
- `reference_format` (default: "markdown"): Format for references (markdown, link-list, index)
- `index_file`: Path to index file to update
- `create_backlinks` (default: true): Add backlinks in extracted files
- `update_source` (default: true): Update source file with references

**Example**:
```python
await create_reference(
    source_file="/path/to/CLAUDE.md",
    extracted_files=[
        "/output/security/auth.md",
        "/output/api/endpoints.md"
    ],
    reference_format="markdown",
    create_backlinks=True
)
```

**Response**:
```json
{
    "success": true,
    "references_created": [
        {
            "source_section": "sec2",
            "target_file": "/output/security/auth.md",
            "link_text": "[Authentication Setup](../output/security/auth.md)",
            "link_format": "\n> **Extracted**: 🔐 Security: [Authentication Setup](../output/security/auth.md)\n",
            "category": "🔐 Security"
        }
    ],
    "total_references": 2,
    "source_updated": true,
    "index_updated": false,
    "backlinks_created": 2
}
```

### 4. `validate_structure`

**Purpose**: Validate documentation structure and check for issues.

**Parameters**:
- `root_dir` (required): Root directory to validate
- `source_files`: Specific files to check (all by default)
- `check_references` (default: true): Validate all references are valid
- `check_orphans` (default: true): Find orphaned documents
- `check_structure` (default: true): Verify directory structure
- `patterns` (default: ["*.md", "*.txt"]): File patterns to validate

**Example**:
```python
await validate_structure(
    root_dir="/project/docs",
    check_references=True,
    check_orphans=True
)
```

**Response**:
```json
{
    "success": true,
    "root_dir": "/project/docs",
    "total_files_checked": 15,
    "valid_files": 13,
    "files_with_issues": 2,
    "orphaned_files": ["/project/docs/old-notes.md"],
    "broken_references": [
        {
            "source": "/project/docs/index.md",
            "target": "missing-file.md"
        }
    ],
    "file_validations": [...],
    "structure_valid": true,
    "issues": [
        {
            "type": "broken_reference",
            "severity": "error",
            "file_path": "/project/docs/index.md",
            "message": "Broken reference: missing-file.md"
        }
    ]
}
```

### 5. `analyze_document`

**Purpose**: Analyze a document and provide insights and recommendations.

**Parameters**:
- `file_path` (required): Path to document to analyze
- `include_statistics` (default: true): Include detailed statistics
- `include_growth` (default: true): Analyze growth patterns
- `include_recommendations` (default: true): Provide extraction recommendations
- `days_for_growth` (default: 30): Number of days to analyze for growth

**Example**:
```python
await analyze_document(
    file_path="/path/to/CLAUDE.md",
    include_statistics=True,
    include_recommendations=True
)
```

**Response**:
```json
{
    "success": true,
    "document_id": "doc_123",
    "file_path": "/path/to/CLAUDE.md",
    "last_modified": "2024-01-15T10:30:00Z",
    "statistics": {
        "total_size": 15420,
        "total_lines": 542,
        "total_sections": 12,
        "section_depth_distribution": {"1": 4, "2": 6, "3": 2},
        "average_section_size": 1285.0,
        "code_block_count": 8,
        "link_count": 23,
        "image_count": 0
    },
    "category_distribution": [
        {
            "category": "🏗️ Architecture",
            "section_count": 3,
            "estimated_size": 4200,
            "percentage": 27.2
        }
    ],
    "recommendations": [
        {
            "section_id": "sec2",
            "title": "Security Configuration",
            "category": "🔐 Security",
            "reason": "High concentration of Security content",
            "priority": "high",
            "estimated_impact": "Better content organization"
        }
    ],
    "insights": [
        "Large document with 542 lines. Consider extracting major sections for better organization.",
        "Architecture dominates (27.2%). Consider dedicated document for this category.",
        "Fast growth rate (15.0%). Regular organization will help maintain clarity."
    ]
}
```

## Additional Tools

### `get_server_metrics`

**Purpose**: Get server performance metrics and statistics.

**Example**:
```python
await get_server_metrics()
```

**Response**:
```json
{
    "server": {
        "start_time": "2024-01-15T09:00:00Z",
        "uptime": "2h 30m",
        "total_requests": 145,
        "active_watchers": 3,
        "processed_files": 42,
        "extracted_contents": 128,
        "requests_per_minute": 0.97
    },
    "tools": {
        "organize_documentation": {
            "total_calls": 23,
            "successful_calls": 21,
            "failed_calls": 2,
            "success_rate": "91.30%",
            "average_duration": "1.245s",
            "min_duration": "0.523s",
            "max_duration": "3.421s"
        }
    },
    "formatted_report": "=== Trapper Keeper MCP Server Metrics ===\n..."
}
```

## Workflow Examples

### 1. Initial Document Organization

```python
# Step 1: Analyze the document
analysis = await analyze_document(file_path="/docs/CLAUDE.md")

# Step 2: Preview organization suggestions
suggestions = await organize_documentation(
    file_path="/docs/CLAUDE.md",
    dry_run=True,
    min_importance=0.5
)

# Step 3: Execute organization
result = await organize_documentation(
    file_path="/docs/CLAUDE.md",
    dry_run=False,
    output_dir="/docs/organized",
    categories=["🔐 Security", "🏗️ Architecture", "🌐 API"]
)

# Step 4: Validate the structure
validation = await validate_structure(root_dir="/docs")
```

### 2. Targeted Extraction

```python
# Extract specific patterns
api_content = await extract_content(
    file_path="/docs/CLAUDE.md",
    patterns=["API", "endpoint", "REST"],
    categories=["🌐 API"],
    output_dir="/docs/api"
)

# Create references
refs = await create_reference(
    source_file="/docs/CLAUDE.md",
    extracted_files=api_content["output_files"],
    reference_format="markdown"
)
```

### 3. Maintenance Workflow

```python
# Regular validation
validation = await validate_structure(
    root_dir="/docs",
    check_references=True,
    check_orphans=True
)

# Fix any issues found
for issue in validation["issues"]:
    if issue["type"] == "orphaned_file":
        # Handle orphaned files
        pass
    elif issue["type"] == "broken_reference":
        # Fix broken references
        pass

# Check metrics
metrics = await get_server_metrics()
print(metrics["formatted_report"])
```

## Categories

Trapper Keeper supports the following extraction categories:

- 🏗️ Architecture
- 🗄️ Database
- 🔐 Security
- ✅ Features
- 📊 Monitoring
- 🚨 Critical
- 📋 Setup
- 🌐 API
- 🧪 Testing
- ⚡ Performance
- 📚 Documentation
- 🚀 Deployment
- ⚙️ Configuration
- 📦 Dependencies
- 🔧 Custom

## Best Practices

1. **Start with Analysis**: Always analyze a document first to understand its structure
2. **Use Dry Run**: Preview changes with `dry_run=True` before executing
3. **Incremental Extraction**: Extract high-importance content first (min_importance=0.7)
4. **Regular Validation**: Run `validate_structure` regularly to maintain integrity
5. **Monitor Performance**: Check `get_server_metrics` to track tool usage
6. **Preserve Context**: Keep `preserve_context=true` for better understanding
7. **Update References**: Always create references to maintain navigation

## Error Handling

All tools return a response with:
- `success`: Boolean indicating if the operation succeeded
- `errors`: List of error messages if failed
- `warnings`: List of warning messages

Always check the `success` field before using the response data.

## Integration with FastMCP

These tools are exposed through FastMCP and can be called from any MCP client. The server runs on the configured host and port (default: localhost:8765).

For more information about FastMCP integration, see: https://gofastmcp.com