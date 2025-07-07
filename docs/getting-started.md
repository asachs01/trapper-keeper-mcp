# Getting Started with Trapper Keeper MCP

Welcome to Trapper Keeper MCP! This guide will help you get up and running quickly with this intelligent document extraction and organization system.

## What is Trapper Keeper MCP?

Trapper Keeper MCP is a Model Context Protocol (MCP) server that watches directories for markdown and text files, extracts categorized content, and organizes it into structured outputs. It's particularly useful for managing large documentation files like CLAUDE.md that can grow unwieldy over time.

## Quick Start (5 minutes)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trapper-keeper-mcp.git
cd trapper-keeper-mcp

# Install with pip
pip install -e .

# Or install with poetry
poetry install
```

### 2. Basic Configuration

Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

The default configuration is ready to use, but you can customize it later.

### 3. Your First Command

Process a markdown file:

```bash
trapper-keeper process README.md
```

This will extract and categorize content from the README file.

## Use Cases

### 1. Managing CLAUDE.md Files

If you work with Claude and maintain a CLAUDE.md file with project context, Trapper Keeper can help organize it:

```bash
# Analyze your CLAUDE.md file
trapper-keeper analyze CLAUDE.md

# Extract specific categories
trapper-keeper extract CLAUDE.md -c "🏗️ Architecture" -c "🔐 Security"

# Watch for changes and auto-organize
trapper-keeper watch . -p "CLAUDE.md" --auto-organize
```

### 2. Documentation Organization

Keep your project documentation organized:

```bash
# Process all documentation files
trapper-keeper process ./docs -r -o ./organized-docs

# Generate an index of all documentation
trapper-keeper analyze ./docs --generate-index
```

### 3. Real-time Monitoring

Watch directories for changes and automatically organize new content:

```bash
# Watch a directory with custom patterns
trapper-keeper watch ./project-docs \
  -p "*.md" \
  -p "*.txt" \
  --ignore "*.draft.*" \
  --recursive
```

## MCP Server Mode

### Quick Setup

Add to your Claude Desktop or other MCP client configuration:

```json
{
  "mcpServers": {
    "trapper-keeper": {
      "command": "python",
      "args": ["-m", "trapper_keeper.mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/trapper-keeper-mcp/src"
      }
    }
  }
}
```

### Using MCP Tools

Once connected, you can use these tools:

1. **organize_documentation** - Analyze and organize a document
2. **extract_content** - Extract specific content from files
3. **validate_structure** - Check document structure
4. **analyze_content** - Get insights about your documentation
5. **generate_references** - Create reference links

Example usage in Claude:

```
Can you help me organize my CLAUDE.md file? It's getting too large and I'd like to extract the security and architecture sections.
```

## Command Examples

### Basic Processing

```bash
# Process a single file
trapper-keeper process document.md

# Process with specific output format
trapper-keeper process document.md -f json -o ./output

# Process with minimum importance threshold
trapper-keeper process document.md --min-importance 0.7
```

### Category Management

```bash
# List all available categories
trapper-keeper categories

# Extract specific categories
trapper-keeper extract document.md \
  -c "🏗️ Architecture" \
  -c "🔐 Security" \
  -c "✅ Features"
```

### Advanced Workflows

```bash
# Dry run to preview changes
trapper-keeper organize document.md --dry-run

# Process directory with custom patterns
trapper-keeper process ./docs \
  -p "*.md" \
  -p "README*" \
  --ignore "*_old*" \
  --recursive

# Watch and auto-organize
trapper-keeper watch ./docs \
  --auto-organize \
  --min-importance 0.6 \
  --output-dir ./organized
```

## Understanding Categories

Trapper Keeper uses emoji-prefixed categories for easy identification:

| Category | Emoji | Description | Keywords |
|----------|-------|-------------|----------|
| Architecture | 🏗️ | System design and structure | architecture, design, structure, pattern |
| Security | 🔐 | Security concerns | security, auth, encryption, permissions |
| Features | ✅ | Feature descriptions | feature, functionality, capability |
| API | 🌐 | API documentation | api, endpoint, route, request |
| Setup | 📋 | Installation and config | setup, install, configure, initialize |
| Critical | 🚨 | Urgent issues | critical, urgent, important, breaking |

## Configuration Deep Dive

### Basic Configuration

```yaml
# config.yaml
extraction:
  categories:
    - "🏗️ Architecture"
    - "🔐 Security"
    - "✅ Features"
  min_importance: 0.5
  max_content_length: 10000

output:
  default_dir: "./tk-output"
  formats: ["markdown", "json"]
  create_index: true

monitoring:
  debounce_seconds: 2.0
  patterns: ["*.md", "*.txt"]
  ignore_patterns: ["*_temp*", "*.draft.*"]
```

### Environment Variables

```bash
# Set logging level
export TRAPPER_KEEPER_LOG_LEVEL=DEBUG

# Set output directory
export TRAPPER_KEEPER_OUTPUT_DIR=/path/to/output

# Set metrics port
export TRAPPER_KEEPER_METRICS_PORT=9090
```

## Next Steps

1. **[Installation Guide](./installation.md)** - Detailed installation instructions
2. **[Configuration Reference](./configuration.md)** - Complete configuration options
3. **[CLI Guide](./cli-guide.md)** - All CLI commands explained
4. **[MCP Tools Reference](./mcp-tools.md)** - Using MCP tools effectively
5. **[Tutorials](./tutorials/basic-usage.md)** - Step-by-step tutorials

## Getting Help

- Run `trapper-keeper --help` for command help
- Check the [Troubleshooting Guide](./troubleshooting.md)
- Visit our [GitHub Issues](https://github.com/yourusername/trapper-keeper-mcp/issues)

## Quick Tips

1. **Start Small**: Begin with a single file before processing directories
2. **Use Dry Run**: Always test with `--dry-run` first
3. **Check Categories**: Run `trapper-keeper categories` to see available categories
4. **Monitor Metrics**: Enable metrics to track performance
5. **Customize Patterns**: Adjust file patterns for your project structure

Welcome to organized documentation! 📚✨