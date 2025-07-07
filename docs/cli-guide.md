# CLI Guide

This guide covers all command-line interface (CLI) commands available in Trapper Keeper MCP.

## Command Structure

```bash
trapper-keeper [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS] [ARGUMENTS]
```

## Global Options

```bash
--config PATH           # Path to configuration file
--log-level LEVEL       # Set log level (DEBUG, INFO, WARNING, ERROR)
--quiet, -q            # Suppress non-error output
--verbose, -v          # Enable verbose output (multiple -v for more)
--version              # Show version and exit
--help                 # Show help and exit
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `process` | Process files or directories |
| `extract` | Extract specific content |
| `watch` | Monitor directories for changes |
| `organize` | Organize documentation (interactive) |
| `analyze` | Analyze documents and directories |
| `validate` | Validate document structure |
| `categories` | List available categories |
| `config` | Manage configuration |
| `server` | Run as MCP server |

## Detailed Command Reference

### `process` - Process Files

Process one or more files to extract and categorize content.

```bash
trapper-keeper process [OPTIONS] FILE_OR_DIR...
```

**Options:**
```bash
-o, --output PATH           # Output directory (default: ./tk-output)
-f, --format FORMAT         # Output format: markdown, json, yaml (default: markdown)
-c, --category CATEGORY     # Specific categories to extract (can be repeated)
-p, --pattern PATTERN       # File patterns to match (default: *.md, *.txt)
-r, --recursive             # Process directories recursively
--min-importance FLOAT      # Minimum importance threshold 0.0-1.0 (default: 0.5)
--max-files INT            # Maximum files to process
--parallel                 # Process files in parallel
--dry-run                  # Preview without processing
--ignore PATTERN           # Patterns to ignore
--create-index             # Create index file
--group-by TYPE            # Group output by: category, document, date
```

**Examples:**
```bash
# Process single file
trapper-keeper process README.md

# Process directory with specific categories
trapper-keeper process ./docs -c "🏗️ Architecture" -c "🔐 Security" -r

# Process with JSON output
trapper-keeper process document.md -f json -o ./output

# Dry run with high importance threshold
trapper-keeper process ./docs --dry-run --min-importance 0.8

# Process specific file types
trapper-keeper process . -p "*.md" -p "README*" --ignore "*.draft.*"
```

### `extract` - Extract Content

Extract specific sections or content from documents.

```bash
trapper-keeper extract [OPTIONS] FILE
```

**Options:**
```bash
-s, --section ID           # Extract specific section by ID
-p, --pattern REGEX        # Extract content matching regex
-c, --category CATEGORY    # Extract by category
-o, --output PATH          # Output directory
-f, --format FORMAT        # Output format
--preserve-context         # Include surrounding context
--update-references        # Update source file references
--line-range START:END     # Extract specific line range
```

**Examples:**
```bash
# Extract by category
trapper-keeper extract CLAUDE.md -c "🔐 Security" -o ./security

# Extract by pattern
trapper-keeper extract docs.md -p "API.*endpoint" 

# Extract specific section
trapper-keeper extract document.md -s "sec_123"

# Extract line range
trapper-keeper extract large-file.md --line-range 100:500
```

### `watch` - Monitor Directories

Watch directories for file changes and process automatically.

```bash
trapper-keeper watch [OPTIONS] DIRECTORY...
```

**Options:**
```bash
-p, --pattern PATTERN      # File patterns to watch
-i, --ignore PATTERN       # Patterns to ignore
-r, --recursive            # Watch subdirectories
--process-existing         # Process existing files on start
--auto-organize            # Automatically organize new content
--debounce SECONDS         # Debounce time (default: 2.0)
--max-depth INT           # Maximum directory depth
-o, --output PATH          # Output directory for organized content
```

**Examples:**
```bash
# Watch current directory
trapper-keeper watch .

# Watch with auto-organization
trapper-keeper watch ./docs --auto-organize -o ./organized

# Watch specific patterns
trapper-keeper watch . -p "*.md" -p "*.txt" --ignore "*.tmp"

# Watch multiple directories
trapper-keeper watch ./docs ./notes --recursive
```

### `organize` - Interactive Organization

Interactively organize documentation with suggestions.

```bash
trapper-keeper organize [OPTIONS] FILE
```

**Options:**
```bash
--auto-approve             # Automatically approve suggestions
--threshold FLOAT          # Suggestion threshold (default: 0.6)
-o, --output PATH          # Output directory
--no-references            # Don't create reference links
--batch                    # Batch mode (non-interactive)
```

**Examples:**
```bash
# Interactive organization
trapper-keeper organize CLAUDE.md

# Auto-approve high confidence suggestions
trapper-keeper organize docs.md --auto-approve --threshold 0.8

# Batch mode
trapper-keeper organize *.md --batch -o ./organized
```

### `analyze` - Analyze Documents

Analyze documents for insights and statistics.

```bash
trapper-keeper analyze [OPTIONS] FILE_OR_DIR
```

**Options:**
```bash
--detailed                 # Show detailed analysis
--growth                   # Analyze growth patterns
--recommendations          # Show extraction recommendations
--format FORMAT            # Output format: text, json, markdown
--days INT                 # Days to analyze for growth (default: 30)
--generate-report          # Generate analysis report
-o, --output PATH          # Report output path
```

**Examples:**
```bash
# Basic analysis
trapper-keeper analyze CLAUDE.md

# Detailed analysis with recommendations
trapper-keeper analyze ./docs --detailed --recommendations

# Generate growth report
trapper-keeper analyze . --growth --days 90 --generate-report

# JSON output
trapper-keeper analyze document.md --format json
```

### `validate` - Validate Structure

Validate document structure and references.

```bash
trapper-keeper validate [OPTIONS] PATH
```

**Options:**
```bash
--check-references         # Validate all references
--check-orphans           # Find orphaned documents
--check-structure         # Verify directory structure
--fix                     # Attempt to fix issues
--strict                  # Strict validation mode
-p, --pattern PATTERN     # File patterns to validate
```

**Examples:**
```bash
# Basic validation
trapper-keeper validate ./docs

# Full validation
trapper-keeper validate . --check-references --check-orphans

# Fix issues
trapper-keeper validate ./docs --fix

# Validate specific files
trapper-keeper validate . -p "*.md" --strict
```

### `categories` - List Categories

List and manage extraction categories.

```bash
trapper-keeper categories [OPTIONS]
```

**Options:**
```bash
--add CATEGORY            # Add custom category
--remove CATEGORY         # Remove category
--show-keywords           # Show category keywords
--show-patterns           # Show detection patterns
--export                  # Export category configuration
```

**Examples:**
```bash
# List all categories
trapper-keeper categories

# Show with keywords
trapper-keeper categories --show-keywords

# Add custom category
trapper-keeper categories --add "🎯 Custom"

# Export configuration
trapper-keeper categories --export > categories.yaml
```

### `config` - Configuration Management

Manage Trapper Keeper configuration.

```bash
trapper-keeper config [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
- `show` - Display current configuration
- `validate` - Validate configuration file
- `generate` - Generate default configuration
- `export` - Export effective configuration
- `edit` - Edit configuration interactively

**Examples:**
```bash
# Show current configuration
trapper-keeper config show

# Validate configuration
trapper-keeper config validate

# Generate default config
trapper-keeper config generate > config.yaml

# Export with defaults filled
trapper-keeper config export > full-config.yaml

# Interactive edit
trapper-keeper config edit
```

### `server` - MCP Server Mode

Run Trapper Keeper as an MCP server.

```bash
trapper-keeper server [OPTIONS]
```

**Options:**
```bash
--host HOST               # Server host (default: localhost)
--port PORT               # Server port (default: 3000)
--no-metrics              # Disable metrics endpoint
--metrics-port PORT       # Metrics port (default: 9090)
--max-concurrent INT      # Max concurrent requests
--timeout SECONDS         # Request timeout
```

**Examples:**
```bash
# Run with defaults
trapper-keeper server

# Custom host and port
trapper-keeper server --host 0.0.0.0 --port 8080

# With performance limits
trapper-keeper server --max-concurrent 20 --timeout 60
```

## Output Formats

### Markdown Output (Default)

```markdown
# Extracted Content

## 🏗️ Architecture

### System Design
*Extracted from: document.md (lines 45-89)*

Content here...

---
```

### JSON Output

```json
{
  "document_id": "doc_123",
  "extracted": [
    {
      "category": "🏗️ Architecture",
      "title": "System Design",
      "content": "...",
      "metadata": {
        "source": "document.md",
        "lines": [45, 89],
        "importance": 0.85
      }
    }
  ]
}
```

### YAML Output

```yaml
document_id: doc_123
extracted:
  - category: 🏗️ Architecture
    title: System Design
    content: |
      ...
    metadata:
      source: document.md
      lines: [45, 89]
      importance: 0.85
```

## Advanced Usage

### Chaining Commands

```bash
# Analyze, then process based on results
trapper-keeper analyze docs.md --format json | \
  jq -r '.recommendations[].category' | \
  xargs -I {} trapper-keeper extract docs.md -c {}
```

### Batch Processing

```bash
# Process all markdown files in subdirectories
find . -name "*.md" -type f | \
  xargs trapper-keeper process --parallel -o ./organized

# Watch multiple directories
echo "docs notes wiki" | \
  xargs -n1 -I {} trapper-keeper watch {} --recursive
```

### Configuration Overrides

```bash
# Override config file settings
trapper-keeper --config prod.yaml \
  process docs.md \
  --min-importance 0.8 \
  --output /secure/output
```

### Scripting

```bash
#!/bin/bash
# organize-project.sh

# Analyze all documentation
trapper-keeper analyze ./docs --generate-report -o analysis.md

# Process high-importance content
trapper-keeper process ./docs \
  --min-importance 0.7 \
  -c "🚨 Critical" \
  -c "🔐 Security" \
  -o ./important

# Validate structure
trapper-keeper validate ./docs --check-references --fix

# Start watching
trapper-keeper watch ./docs --auto-organize &
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | File not found |
| 4 | Permission denied |
| 5 | Validation failed |
| 6 | Processing error |
| 7 | Server error |

## Environment Variables

```bash
# Override default config location
export TRAPPER_KEEPER_CONFIG=/etc/trapper-keeper/config.yaml

# Set default output directory
export TRAPPER_KEEPER_OUTPUT_DIR=/var/trapper-keeper/output

# Enable debug logging
export TRAPPER_KEEPER_LOG_LEVEL=DEBUG

# Set parallel processing threads
export TRAPPER_KEEPER_MAX_WORKERS=8
```

## Aliases and Shortcuts

Add to your shell configuration:

```bash
# Bash/Zsh aliases
alias tk='trapper-keeper'
alias tkp='trapper-keeper process'
alias tkw='trapper-keeper watch'
alias tka='trapper-keeper analyze'

# Functions
tkorg() {
  trapper-keeper organize "$1" -o "./organized/$(basename $1 .md)"
}

tkextract() {
  trapper-keeper extract "$1" -c "$2" -o "./extracted/$2"
}
```

## Tips and Tricks

1. **Use `--dry-run`**: Always preview changes before processing
2. **Start with high thresholds**: Begin with `--min-importance 0.7` or higher
3. **Process incrementally**: Extract one category at a time
4. **Monitor performance**: Use `--verbose` to see processing details
5. **Validate regularly**: Run `validate` after major changes
6. **Use watch for automation**: Set up `watch` for continuous organization
7. **Export configurations**: Save working configs with `config export`

## Getting Help

```bash
# General help
trapper-keeper --help

# Command-specific help
trapper-keeper process --help

# List all commands
trapper-keeper --help | grep "Commands:"

# Show version and system info
trapper-keeper --version --verbose
```

## Next Steps

- [Configuration Reference](./configuration.md) - Detailed configuration options
- [MCP Tools Reference](./mcp-tools.md) - Using MCP tools
- [Tutorials](./tutorials/basic-usage.md) - Step-by-step guides