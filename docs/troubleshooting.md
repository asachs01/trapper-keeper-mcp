# Troubleshooting Guide

This guide helps you resolve common issues with Trapper Keeper MCP.

## Common Issues

### Installation Issues

#### Python Version Error

**Problem:**
```
ERROR: Trapper Keeper requires Python 3.8 or higher
```

**Solution:**
1. Check your Python version:
   ```bash
   python --version
   ```
2. Install Python 3.8 or higher:
   - macOS: `brew install python@3.11`
   - Ubuntu: `sudo apt install python3.11`
   - Windows: Download from [python.org](https://python.org)

3. Use virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install trapper-keeper-mcp
   ```

#### Missing Dependencies

**Problem:**
```
ModuleNotFoundError: No module named 'fastmcp'
```

**Solution:**
```bash
# Reinstall with all dependencies
pip install --upgrade --force-reinstall trapper-keeper-mcp

# Or install manually
pip install fastmcp click rich pyyaml watchdog prometheus-client pydantic
```

#### Permission Denied

**Problem:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Option 1: Install in user directory
pip install --user trapper-keeper-mcp

# Option 2: Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install trapper-keeper-mcp

# Option 3: Fix permissions (not recommended)
sudo pip install trapper-keeper-mcp
```

### MCP Server Issues

#### Connection Failed

**Problem:**
```
ERROR: Failed to connect to MCP server
Connection refused on localhost:3000
```

**Solution:**
1. Check if server is running:
   ```bash
   ps aux | grep trapper-keeper
   ```

2. Check port availability:
   ```bash
   lsof -i :3000
   ```

3. Start server manually:
   ```bash
   trapper-keeper server --log-level DEBUG
   ```

4. Check MCP client configuration:
   ```json
   {
     "mcpServers": {
       "trapper-keeper": {
         "command": "python",
         "args": ["-m", "trapper_keeper.mcp.server"],
         "env": {
           "PYTHONPATH": "/absolute/path/to/trapper-keeper-mcp/src"
         }
       }
     }
   }
   ```

#### Server Crashes

**Problem:**
```
Server started but immediately exits
```

**Solution:**
1. Check logs:
   ```bash
   trapper-keeper server --log-level DEBUG 2>&1 | tee server.log
   ```

2. Common causes:
   - Missing configuration file
   - Invalid configuration
   - Port already in use
   - Insufficient permissions

3. Validate configuration:
   ```bash
   trapper-keeper config validate
   ```

### Processing Issues

#### File Not Found

**Problem:**
```
ERROR: File not found: document.md
```

**Solution:**
1. Check file path:
   ```bash
   # Use absolute path
   trapper-keeper process /full/path/to/document.md
   
   # Or ensure you're in correct directory
   pwd
   ls -la document.md
   ```

2. Check file permissions:
   ```bash
   ls -l document.md
   # Should show read permissions
   ```

3. Handle symlinks:
   ```bash
   # Follow symlinks
   realpath document.md
   ```

#### Empty Output

**Problem:**
```
Processing completed but no content extracted
```

**Solution:**
1. Lower importance threshold:
   ```bash
   trapper-keeper process document.md --min-importance 0.3
   ```

2. Check categories:
   ```bash
   # List available categories
   trapper-keeper categories
   
   # Try without category filter
   trapper-keeper process document.md -c ALL
   ```

3. Verify file content:
   ```bash
   # Check if file has expected structure
   head -50 document.md
   ```

4. Enable verbose output:
   ```bash
   trapper-keeper process document.md -vv
   ```

#### Memory Error

**Problem:**
```
MemoryError: Unable to allocate array
```

**Solution:**
1. Process smaller files:
   ```bash
   # Split large file
   split -l 1000 large-file.md chunk-
   
   # Process chunks
   for chunk in chunk-*; do
     trapper-keeper process "$chunk"
   done
   ```

2. Increase memory limit:
   ```bash
   # Set memory limit in config
   performance:
     memory_limit: 2048  # 2GB
   ```

3. Use streaming mode:
   ```bash
   trapper-keeper process large-file.md --streaming
   ```

### Category Detection Issues

#### Wrong Categories

**Problem:**
```
Content is being categorized incorrectly
```

**Solution:**
1. Update category keywords:
   ```yaml
   # config.yaml
   detection:
     custom_patterns:
       "🔐 Security":
         keywords: ["auth", "security", "password", "token", "oauth"]
         patterns: [".*authentication.*", ".*authorization.*"]
   ```

2. Adjust confidence threshold:
   ```bash
   trapper-keeper process document.md --confidence-threshold 0.7
   ```

3. Use explicit categories:
   ```bash
   trapper-keeper extract document.md -c "🔐 Security" --pattern "auth"
   ```

#### Missing Categories

**Problem:**
```
Expected categories not being detected
```

**Solution:**
1. Add custom categories:
   ```bash
   trapper-keeper categories --add "🎯 Custom Category"
   ```

2. Define detection patterns:
   ```yaml
   detection:
     custom_patterns:
       "🎯 Custom Category":
         keywords: ["specific", "terms"]
         importance_boost: 0.2
   ```

### File Watching Issues

#### Not Detecting Changes

**Problem:**
```
File changes not being detected by watch command
```

**Solution:**
1. Check debounce settings:
   ```yaml
   monitoring:
     debounce_seconds: 2.0  # Reduce if needed
   ```

2. Verify patterns:
   ```bash
   trapper-keeper watch . -p "*.md" -p "*.txt" --verbose
   ```

3. Check ignore patterns:
   ```bash
   # Make sure files aren't ignored
   trapper-keeper watch . --show-config | grep ignore
   ```

4. Use polling on network drives:
   ```bash
   trapper-keeper watch /network/drive --use-polling
   ```

#### Too Many Events

**Problem:**
```
Overwhelming number of file change events
```

**Solution:**
1. Increase debounce time:
   ```yaml
   monitoring:
     debounce_seconds: 5.0
   ```

2. Add ignore patterns:
   ```bash
   trapper-keeper watch . \
     --ignore "*.tmp" \
     --ignore "*.swp" \
     --ignore ".git/*"
   ```

3. Limit recursion depth:
   ```bash
   trapper-keeper watch . --max-depth 2
   ```

### Performance Issues

#### Slow Processing

**Problem:**
```
Processing takes too long
```

**Solution:**
1. Enable parallel processing:
   ```bash
   trapper-keeper process ./docs --parallel
   ```

2. Adjust concurrent limit:
   ```yaml
   performance:
     max_concurrent: 10
   ```

3. Use caching:
   ```yaml
   performance:
     enable_cache: true
     cache_size: 500
   ```

4. Profile performance:
   ```bash
   trapper-keeper process document.md --profile
   ```

#### High Memory Usage

**Problem:**
```
Excessive memory consumption
```

**Solution:**
1. Limit file size:
   ```yaml
   parser:
     max_file_size: 5242880  # 5MB
   ```

2. Process in batches:
   ```bash
   find . -name "*.md" | \
     xargs -n 10 trapper-keeper process
   ```

3. Clear cache:
   ```bash
   trapper-keeper cache clear
   ```

### Configuration Issues

#### Invalid Configuration

**Problem:**
```
ERROR: Invalid configuration: Expected dict, got str
```

**Solution:**
1. Validate YAML syntax:
   ```bash
   # Online YAML validator or
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. Check configuration:
   ```bash
   trapper-keeper config validate
   ```

3. Use default configuration:
   ```bash
   trapper-keeper config generate > config.yaml
   ```

#### Configuration Not Loading

**Problem:**
```
Changes to config.yaml not taking effect
```

**Solution:**
1. Check config location:
   ```bash
   trapper-keeper config show --location
   ```

2. Specify config explicitly:
   ```bash
   trapper-keeper --config ./my-config.yaml process document.md
   ```

3. Check environment variable:
   ```bash
   echo $TRAPPER_KEEPER_CONFIG
   ```

## Debugging Techniques

### Enable Debug Logging

```bash
# Via command line
trapper-keeper --log-level DEBUG process document.md

# Via environment variable
export TRAPPER_KEEPER_LOG_LEVEL=DEBUG
trapper-keeper process document.md

# Via configuration
logging:
  level: DEBUG
```

### Verbose Output

```bash
# Single -v for INFO level
trapper-keeper -v process document.md

# Double -vv for DEBUG level
trapper-keeper -vv process document.md

# Triple -vvv for TRACE level
trapper-keeper -vvv process document.md
```

### Dry Run Mode

```bash
# Preview without making changes
trapper-keeper process document.md --dry-run

# Combine with verbose for details
trapper-keeper -vv process document.md --dry-run
```

### Check System Information

```bash
# Show version and dependencies
trapper-keeper --version --verbose

# Show configuration
trapper-keeper config show

# Show server status
trapper-keeper server --status
```

## Getting Help

### Built-in Help

```bash
# General help
trapper-keeper --help

# Command-specific help
trapper-keeper process --help

# Show all available commands
trapper-keeper help --all
```

### Log Files

Default log locations:
- `./logs/trapper-keeper.log`
- `~/.trapper-keeper/logs/`
- `/var/log/trapper-keeper/`

### Community Support

1. **GitHub Issues**: [Report bugs](https://github.com/yourusername/trapper-keeper-mcp/issues)
2. **Discussions**: [Ask questions](https://github.com/yourusername/trapper-keeper-mcp/discussions)
3. **Discord**: Join our community server

### Reporting Issues

When reporting issues, include:

1. **System Information**:
   ```bash
   trapper-keeper --version --verbose > system-info.txt
   ```

2. **Configuration**:
   ```bash
   trapper-keeper config show > config-dump.txt
   ```

3. **Debug Logs**:
   ```bash
   trapper-keeper --log-level DEBUG [command] 2>&1 | tee debug.log
   ```

4. **Steps to Reproduce**:
   - Exact commands run
   - Sample files (if possible)
   - Expected vs actual behavior

## FAQ

**Q: Can I use Trapper Keeper without MCP?**
A: Yes, the CLI works standalone. MCP server mode is optional.

**Q: How do I add custom categories?**
A: Use `trapper-keeper categories --add "🎯 Custom"` or edit config.yaml.

**Q: Can I process non-Markdown files?**
A: Currently supports Markdown and plain text. More formats coming soon.

**Q: Is there a file size limit?**
A: Default is 10MB. Adjust with `parser.max_file_size` in config.

**Q: Can I run multiple instances?**
A: Yes, but use different ports/output directories to avoid conflicts.

## Next Steps

- [Configuration Reference](./configuration.md) - Fine-tune settings
- [API Reference](./api-reference.md) - Programming interface
- [Contributing](./development/contributing.md) - Help improve Trapper Keeper