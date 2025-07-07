# Trapper Keeper MCP

> **Keep your AI context organized like a boss** 📚✨

An intelligent document extraction and organization system built as a Model Context Protocol (MCP) server using Python and FastMCP. Trapper Keeper watches directories for markdown and text files, extracts categorized content, and organizes it into structured outputs.

## 🏗️ Architecture

Trapper Keeper MCP is designed with a modular, event-driven architecture that supports both CLI and MCP server modes:

### Key Components

- **Core**: Base classes, type definitions, and configuration management
- **Monitoring**: File system monitoring with debouncing and pattern matching
- **Parser**: Extensible document parsing (currently supports Markdown)
- **Extractor**: Intelligent content extraction with category detection
- **Organizer**: Flexible output organization and formatting
- **MCP Server**: FastMCP-based server implementation
- **CLI**: Rich command-line interface

## ✅ Features

### Intelligent Content Extraction

- **Category Detection**: Automatically categorizes content using pattern matching and keywords
- **Importance Scoring**: Assigns importance scores based on content relevance
- **Section Parsing**: Preserves document structure with hierarchical sections
- **Code Block Extraction**: Extracts and categorizes code snippets
- **Link Extraction**: Groups and organizes document links

### Real-time File Monitoring

- **Directory Watching**: Monitors directories for file changes
- **Pattern Matching**: Configurable file patterns and ignore rules
- **Debouncing**: Prevents duplicate processing of rapid changes
- **Event System**: Async event-driven architecture for scalability

### Flexible Organization

- **Multiple Output Formats**: Markdown, JSON, and YAML
- **Grouping Options**: By category, document, or custom grouping
- **Index Generation**: Automatic index creation with statistics
- **Metadata Preservation**: Maintains source information and timestamps

## 📋 Setup

### Prerequisites

- Python 3.8 or higher
- pip or poetry for dependency management

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trapper-keeper-mcp.git
cd trapper-keeper-mcp
```

2. Install dependencies:
```bash
pip install -e .
```

3. Copy the example configuration:
```bash
cp config.example.yaml config.yaml
```

4. Edit `config.yaml` to match your needs

### MCP Integration

Add to your MCP settings:

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

## 🌐 API

### CLI Commands

```bash
# Process a single file
trapper-keeper process document.md -o ./output

# Process a directory
trapper-keeper process ./docs -c "🏗️ Architecture" -c "🔐 Security" -f json

# Watch a directory
trapper-keeper watch ./docs -p "*.md" -p "*.txt" --recursive

# List categories
trapper-keeper categories

# Run as MCP server
trapper-keeper server

# Show/save configuration
trapper-keeper config
trapper-keeper config -o my-config.yaml
```

### Category Configuration

The system uses emoji-prefixed categories for easy identification:

- 🏗️ Architecture - System design and structure
- 🗄️ Database - Database schemas and queries
- 🔐 Security - Authentication and security concerns
- ✅ Features - Feature descriptions and requirements
- 📊 Monitoring - Logging and observability
- 🚨 Critical - Urgent issues and blockers
- 📋 Setup - Installation and configuration
- 🌐 API - API endpoints and integrations
- 🧪 Testing - Test cases and strategies
- ⚡ Performance - Optimization and speed
- 📚 Documentation - Guides and references
- 🚀 Deployment - Deployment and CI/CD
- ⚙️ Configuration - Settings and options
- 📦 Dependencies - Package management

## MCP Tools Available

The MCP server exposes the following tools:

### `process_file`
Process a single file and extract categorized content.

```python
{
    "file_path": "/path/to/document.md",
    "extract_categories": ["🏗️ Architecture", "🔐 Security"],
    "output_format": "markdown"
}
```

### `process_directory`
Process all matching files in a directory.

```python
{
    "directory_path": "/path/to/docs",
    "patterns": ["*.md", "*.txt"],
    "recursive": true,
    "output_dir": "./output",
    "output_format": "json"
}
```

### `watch_directory`
Start watching a directory for changes.

```python
{
    "directory_path": "/path/to/docs",
    "patterns": ["*.md"],
    "recursive": true,
    "process_existing": true
}
```

### `stop_watching`
Stop watching a specific directory.

### `list_watched_directories`
Get information about all watched directories.

### `get_categories`
Get list of available extraction categories.

### `update_config`
Update server configuration at runtime.

## 📊 Monitoring

Trapper Keeper includes Prometheus metrics for monitoring:

- Files processed (success/failure counts)
- Event publications by type
- Content extraction by category
- Processing duration histograms
- Queue sizes and active watchers

Metrics are exposed on port 9090 by default.

## 🚨 Critical Configuration

### Environment Variables

- `TRAPPER_KEEPER_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `TRAPPER_KEEPER_METRICS_PORT`: Prometheus metrics port
- `TRAPPER_KEEPER_MCP_PORT`: MCP server port
- `TRAPPER_KEEPER_OUTPUT_DIR`: Default output directory
- `TRAPPER_KEEPER_MAX_CONCURRENT`: Maximum concurrent file processing

## 🔐 Security

- File access is restricted to configured paths
- No remote code execution
- Configurable ignore patterns for sensitive files
- All file operations are read-only by default

## Development

### Project Structure

```
src/trapper_keeper/
├── core/           # Base classes and types
├── monitoring/     # File monitoring
├── parser/         # Document parsers
├── extractor/      # Content extraction
├── organizer/      # Output organization
├── mcp/           # MCP server
├── cli/           # CLI interface
└── utils/         # Utilities
```

### Adding a New Parser

1. Create a new parser class inheriting from `Parser`
2. Implement required methods: `parse()`, `can_parse()`
3. Register in `parser_factory.py`

### Adding a New Category

1. Add to `ExtractionCategory` enum in `types.py`
2. Add detection patterns in `category_detector.py`

### Plugin System

The architecture supports plugins through the `Plugin` protocol. Plugins can:
- Process documents
- Add new extraction categories
- Implement custom output formats

## Why "Trapper Keeper"?

Named after the iconic 90s school organizer, Trapper Keeper MCP does for your code documentation what those colorful binders did for school papers - keeps everything organized, accessible, and prevents the chaos of loose papers (or in our case, sprawling documentation) from taking over your project.

## Documentation

### Getting Started
- [Quick Start Guide](docs/getting-started.md) - Get up and running in 5 minutes
- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Configuration Reference](docs/configuration.md) - All configuration options

### User Guides
- [CLI Guide](docs/cli-guide.md) - Complete CLI command reference
- [MCP Tools Reference](docs/mcp-tools.md) - Using MCP tools effectively
- [API Reference](docs/api-reference.md) - Python API documentation
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions

### Tutorials
- [Basic Usage](docs/tutorials/basic-usage.md) - Step-by-step tutorials
- [Advanced Workflows](docs/tutorials/advanced-workflows.md) - Complex use cases
- [Integration Guide](docs/tutorials/integration-guide.md) - Integrate with other tools
- [Custom Categories](docs/tutorials/custom-categories.md) - Create custom categories

### Architecture & Development
- [Architecture Overview](docs/architecture/overview.md) - System design
- [Contributing Guide](docs/development/contributing.md) - How to contribute
- [Plugin Development](docs/development/plugin-development.md) - Extend functionality

### Examples
- [Example Configurations](examples/configurations/) - Configuration examples
- [Python Scripts](examples/scripts/) - API usage examples
- [Docker Setup](examples/docker/) - Docker deployment examples
- [CLAUDE.md Examples](examples/claude-files/) - Sample documentation files

## License

MIT License - see LICENSE file for details.