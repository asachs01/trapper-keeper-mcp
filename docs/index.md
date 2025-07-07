# Trapper Keeper MCP Documentation

Welcome to the comprehensive documentation for Trapper Keeper MCP - an intelligent document extraction and organization system built as a Model Context Protocol (MCP) server.

## What is Trapper Keeper MCP?

Trapper Keeper MCP helps you manage large documentation files (like CLAUDE.md) by:

- **📚 Extracting** categorized content from markdown and text files
- **🗂️ Organizing** content into structured, manageable sections
- **🔍 Monitoring** directories for changes and auto-organizing
- **🔗 Creating** reference links between source and extracted content
- **📊 Analyzing** documentation health and providing insights

## Quick Links

### 🚀 Getting Started
- [**Quick Start Guide**](getting-started.md) - Get running in 5 minutes
- [**Installation**](installation.md) - Detailed setup instructions
- [**First Tutorial**](tutorials/basic-usage.md) - Learn by doing

### 📖 User Guides
- [**CLI Reference**](cli-guide.md) - All command-line commands
- [**MCP Tools**](mcp-tools.md) - Using with Claude and other MCP clients
- [**Configuration**](configuration.md) - Customize behavior

### 🎓 Tutorials
- [**Basic Usage**](tutorials/basic-usage.md) - Step-by-step guide
- [**Advanced Workflows**](tutorials/advanced-workflows.md) - Power user techniques
- [**Integrations**](tutorials/integration-guide.md) - Connect with other tools
- [**Custom Categories**](tutorials/custom-categories.md) - Domain-specific setup

### 🔧 Development
- [**API Reference**](api-reference.md) - Python API documentation
- [**Architecture**](architecture/overview.md) - System design
- [**Contributing**](development/contributing.md) - Join the project

## Key Features

### 🏗️ Intelligent Content Extraction
- Automatic category detection using keywords and patterns
- Importance scoring to extract only relevant content
- Preserves document structure and formatting
- Extracts code blocks, links, and TODOs

### 📁 Flexible Organization
- Multiple output formats (Markdown, JSON, YAML)
- Group by category, document, or custom schemes
- Automatic index generation
- Reference link creation

### 👁️ Real-time Monitoring
- Watch directories for changes
- Auto-organize on file modifications
- Configurable debouncing
- Event-driven architecture

### 🔌 Extensible Design
- Plugin system for custom functionality
- Support for new file formats
- Custom extraction categories
- API for programmatic use

## Use Cases

### Managing CLAUDE.md Files
Keep your AI context files organized as they grow:
```bash
trapper-keeper organize CLAUDE.md
```

### Documentation Maintenance
Organize project documentation automatically:
```bash
trapper-keeper watch ./docs --auto-organize
```

### CI/CD Integration
Process documentation in your pipeline:
```yaml
- name: Organize Docs
  run: trapper-keeper process ./docs -o ./organized
```

### Research & Analysis
Extract specific topics across multiple files:
```bash
trapper-keeper extract ./papers -c "🔬 Research" -c "📊 Results"
```

## Example Workflow

```bash
# 1. Install Trapper Keeper
pip install trapper-keeper-mcp

# 2. Process a documentation file
trapper-keeper process README.md

# 3. View organized output
ls tk-output/
cat tk-output/architecture.md

# 4. Watch for changes
trapper-keeper watch . --auto-organize
```

## Documentation Map

```
📚 Documentation
├── 🚀 Getting Started
│   ├── Quick Start Guide
│   ├── Installation
│   └── Configuration
├── 📖 User Guides
│   ├── CLI Commands
│   ├── MCP Tools
│   └── API Reference
├── 🎓 Tutorials
│   ├── Basic Usage
│   ├── Advanced Workflows
│   ├── Integrations
│   └── Custom Categories
├── 🏗️ Architecture
│   ├── System Overview
│   ├── Components
│   └── Data Flow
├── 🔧 Development
│   ├── Contributing
│   ├── Plugin Development
│   └── Testing
└── 📦 Examples
    ├── Configurations
    ├── Scripts
    └── Docker
```

## Getting Help

### 💬 Community Support
- [GitHub Discussions](https://github.com/yourusername/trapper-keeper-mcp/discussions) - Ask questions
- [Discord Server](https://discord.gg/trapper-keeper) - Real-time chat
- [Issue Tracker](https://github.com/yourusername/trapper-keeper-mcp/issues) - Report bugs

### 📚 Resources
- [Troubleshooting Guide](troubleshooting.md) - Common issues
- [FAQ](faq.md) - Frequently asked questions
- [Changelog](../CHANGELOG.md) - Recent updates

## Why Trapper Keeper?

Named after the iconic 90s school organizer, Trapper Keeper MCP brings the same organizational power to your documentation that those colorful binders brought to school papers.

Just as the original Trapper Keeper prevented loose papers from creating chaos, Trapper Keeper MCP prevents documentation sprawl by intelligently organizing your content into manageable, categorized sections.

## Start Your Journey

Ready to organize your documentation? Start here:

1. 📖 Read the [Quick Start Guide](getting-started.md)
2. 💻 Follow the [Installation Instructions](installation.md)
3. 🎯 Try the [Basic Usage Tutorial](tutorials/basic-usage.md)
4. 🚀 Explore [Advanced Features](tutorials/advanced-workflows.md)

Welcome to organized documentation! 📚✨