# Installation Guide

This guide provides detailed instructions for installing Trapper Keeper MCP in various environments.

## Requirements

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM (1GB recommended)
- **Disk Space**: 100MB for installation

### Python Dependencies

Core dependencies:
- `fastmcp` - MCP server framework
- `click` - CLI framework
- `rich` - Terminal formatting
- `pyyaml` - YAML configuration
- `watchdog` - File system monitoring
- `prometheus-client` - Metrics collection
- `pydantic` - Data validation

## Installation Methods

### Method 1: pip (Recommended)

```bash
# Install from PyPI (when published)
pip install trapper-keeper-mcp

# Install from GitHub
pip install git+https://github.com/yourusername/trapper-keeper-mcp.git

# Install in development mode
git clone https://github.com/yourusername/trapper-keeper-mcp.git
cd trapper-keeper-mcp
pip install -e .
```

### Method 2: Poetry

```bash
# Clone repository
git clone https://github.com/yourusername/trapper-keeper-mcp.git
cd trapper-keeper-mcp

# Install with poetry
poetry install

# Activate virtual environment
poetry shell
```

### Method 3: Docker

```bash
# Pull the image
docker pull yourusername/trapper-keeper-mcp:latest

# Run container
docker run -v $(pwd):/workspace yourusername/trapper-keeper-mcp
```

### Method 4: From Source

```bash
# Clone repository
git clone https://github.com/yourusername/trapper-keeper-mcp.git
cd trapper-keeper-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Platform-Specific Instructions

### macOS

```bash
# Install Python if needed
brew install python@3.11

# Install system dependencies
brew install watchman  # Optional, for better file watching

# Install Trapper Keeper
pip install trapper-keeper-mcp
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install system dependencies
sudo apt install python3-dev build-essential

# Install Trapper Keeper
pip3 install trapper-keeper-mcp
```

### Windows

```powershell
# Install Python from python.org or:
winget install Python.Python.3.11

# Install Trapper Keeper
pip install trapper-keeper-mcp

# For file watching on Windows, you may need:
pip install watchdog[watchmedo]
```

## MCP Integration

### Claude Desktop

1. Locate your Claude Desktop configuration:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Edit the configuration:

```json
{
  "mcpServers": {
    "trapper-keeper": {
      "command": "python",
      "args": ["-m", "trapper_keeper.mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/trapper-keeper-mcp/src",
        "TRAPPER_KEEPER_CONFIG": "/path/to/config.yaml"
      }
    }
  }
}
```

3. Restart Claude Desktop

### VS Code

Install the MCP extension and add to settings:

```json
{
  "mcp.servers": {
    "trapper-keeper": {
      "command": "trapper-keeper",
      "args": ["server"],
      "env": {
        "TRAPPER_KEEPER_CONFIG": "${workspaceFolder}/config.yaml"
      }
    }
  }
}
```

### Other MCP Clients

For generic MCP client configuration:

```json
{
  "servers": [
    {
      "name": "trapper-keeper",
      "command": "python -m trapper_keeper.mcp.server",
      "env": {
        "PYTHONPATH": "/path/to/trapper-keeper-mcp/src"
      }
    }
  ]
}
```

## Post-Installation Setup

### 1. Verify Installation

```bash
# Check version
trapper-keeper --version

# Run help
trapper-keeper --help

# Test with a simple command
trapper-keeper categories
```

### 2. Create Configuration

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Or generate default configuration
trapper-keeper config --generate > config.yaml
```

### 3. Test Basic Functionality

```bash
# Create a test file
echo "# Test\n## 🏗️ Architecture\nTest content" > test.md

# Process the file
trapper-keeper process test.md

# Check output
ls tk-output/
```

### 4. Configure Shell Completion (Optional)

```bash
# Bash
echo 'eval "$(_TRAPPER_KEEPER_COMPLETE=source_bash trapper-keeper)"' >> ~/.bashrc

# Zsh
echo 'eval "$(_TRAPPER_KEEPER_COMPLETE=source_zsh trapper-keeper)"' >> ~/.zshrc

# Fish
echo 'eval "$(_TRAPPER_KEEPER_COMPLETE=source_fish trapper-keeper)"' >> ~/.config/fish/config.fish
```

## Development Installation

For contributing to Trapper Keeper:

```bash
# Clone with SSH
git clone git@github.com:yourusername/trapper-keeper-mcp.git
cd trapper-keeper-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode with extras
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8
black --check .
```

## Troubleshooting Installation

### Common Issues

#### Python Version Error

```
ERROR: Trapper Keeper requires Python 3.8 or higher
```

Solution:
```bash
# Check Python version
python --version

# Install correct version
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: Download from python.org
```

#### Missing Dependencies

```
ERROR: No module named 'fastmcp'
```

Solution:
```bash
# Reinstall with all dependencies
pip install --force-reinstall trapper-keeper-mcp

# Or install dependencies manually
pip install -r requirements.txt
```

#### Permission Errors

```
ERROR: Could not install packages due to an EnvironmentError
```

Solution:
```bash
# Install in user directory
pip install --user trapper-keeper-mcp

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install trapper-keeper-mcp
```

#### MCP Connection Failed

```
ERROR: Failed to connect to MCP server
```

Solution:
1. Check Python path in MCP configuration
2. Verify Trapper Keeper is installed in the Python environment
3. Check logs: `trapper-keeper server --log-level DEBUG`

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Search [GitHub Issues](https://github.com/yourusername/trapper-keeper-mcp/issues)
3. Join our [Discord Community](https://discord.gg/trapper-keeper)
4. File a bug report with:
   - Python version: `python --version`
   - Trapper Keeper version: `trapper-keeper --version`
   - Full error message
   - Steps to reproduce

## Next Steps

- [Getting Started](./getting-started.md) - Quick start guide
- [Configuration Reference](./configuration.md) - Configure Trapper Keeper
- [CLI Guide](./cli-guide.md) - Learn all CLI commands
- [MCP Tools Reference](./mcp-tools.md) - Use MCP tools