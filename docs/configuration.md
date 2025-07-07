# Configuration Reference

This guide covers all configuration options for Trapper Keeper MCP. Configuration can be provided via YAML files, environment variables, or command-line arguments.

## Configuration Files

### Default Locations

Trapper Keeper looks for configuration in these locations (in order):

1. `./config.yaml` (current directory)
2. `~/.trapper-keeper/config.yaml` (user home)
3. `/etc/trapper-keeper/config.yaml` (system-wide)
4. Path specified by `TRAPPER_KEEPER_CONFIG` environment variable
5. Path specified by `--config` command-line argument

### Complete Configuration Example

```yaml
# config.yaml - Complete configuration reference
version: "1.0"

# Extraction settings
extraction:
  # Categories to extract
  categories:
    - "🏗️ Architecture"
    - "🗄️ Database"
    - "🔐 Security"
    - "✅ Features"
    - "📊 Monitoring"
    - "🚨 Critical"
    - "📋 Setup"
    - "🌐 API"
    - "🧪 Testing"
    - "⚡ Performance"
    - "📚 Documentation"
    - "🚀 Deployment"
    - "⚙️ Configuration"
    - "📦 Dependencies"
  
  # Minimum importance score (0.0-1.0)
  min_importance: 0.5
  
  # Maximum content length per section
  max_content_length: 10000
  
  # Extract code blocks
  extract_code_blocks: true
  
  # Extract links
  extract_links: true
  
  # Preserve formatting
  preserve_formatting: true

# Output settings
output:
  # Default output directory
  default_dir: "./tk-output"
  
  # Output formats
  formats:
    - "markdown"
    - "json"
    - "yaml"
  
  # Create index file
  create_index: true
  
  # Index filename
  index_filename: "index.md"
  
  # Group by options: category, document, date
  group_by: "category"
  
  # Include metadata
  include_metadata: true
  
  # Create subdirectories
  create_subdirs: true
  
  # Timestamp format
  timestamp_format: "%Y-%m-%d %H:%M:%S"

# Monitoring settings
monitoring:
  # File watching enabled
  enabled: true
  
  # Debounce time in seconds
  debounce_seconds: 2.0
  
  # File patterns to watch
  patterns:
    - "*.md"
    - "*.txt"
    - "*.markdown"
    - "README*"
    - "CLAUDE*"
  
  # Patterns to ignore
  ignore_patterns:
    - "*.tmp"
    - "*.swp"
    - "*~"
    - ".*"
    - "__pycache__"
    - "*.pyc"
    - "node_modules"
    - ".git"
  
  # Watch subdirectories
  recursive: true
  
  # Maximum directory depth
  max_depth: 10
  
  # Process existing files on start
  process_existing: true

# Parser settings
parser:
  # Maximum file size in bytes
  max_file_size: 10485760  # 10MB
  
  # Encoding
  encoding: "utf-8"
  
  # Encoding fallbacks
  encoding_fallbacks:
    - "utf-8"
    - "latin-1"
    - "cp1252"
  
  # Parse frontmatter
  parse_frontmatter: true
  
  # Code fence languages to highlight
  code_languages:
    - "python"
    - "javascript"
    - "typescript"
    - "bash"
    - "yaml"
    - "json"

# Category detection settings
detection:
  # Use keyword matching
  use_keywords: true
  
  # Use pattern matching
  use_patterns: true
  
  # Use ML classification (if available)
  use_ml: false
  
  # Confidence threshold
  confidence_threshold: 0.6
  
  # Custom patterns
  custom_patterns:
    "🏗️ Architecture":
      keywords: ["architecture", "design", "structure", "pattern", "diagram"]
      patterns: [".*architect.*", ".*design pattern.*"]
    "🔐 Security":
      keywords: ["security", "auth", "encryption", "password", "token", "ssl"]
      patterns: [".*security.*", ".*authenticat.*"]

# MCP server settings
mcp:
  # Server host
  host: "localhost"
  
  # Server port
  port: 3000
  
  # Enable request logging
  log_requests: true
  
  # Request timeout in seconds
  timeout: 30
  
  # Maximum concurrent requests
  max_concurrent: 10
  
  # Enable metrics endpoint
  enable_metrics: true

# Metrics settings
metrics:
  # Enable metrics collection
  enabled: true
  
  # Metrics port
  port: 9090
  
  # Metrics path
  path: "/metrics"
  
  # Collection interval in seconds
  interval: 60
  
  # Histogram buckets for processing time
  processing_buckets:
    - 0.1
    - 0.5
    - 1.0
    - 2.5
    - 5.0
    - 10.0

# Logging settings
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR
  level: "INFO"
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Log to file
  file:
    enabled: true
    path: "./logs/trapper-keeper.log"
    max_size: 10485760  # 10MB
    backup_count: 5
  
  # Log to console
  console:
    enabled: true
    colorize: true

# Performance settings
performance:
  # Maximum concurrent file processing
  max_concurrent: 5
  
  # Process timeout in seconds
  process_timeout: 300
  
  # Memory limit in MB
  memory_limit: 1024
  
  # Enable caching
  enable_cache: true
  
  # Cache size
  cache_size: 100
  
  # Cache TTL in seconds
  cache_ttl: 3600

# Security settings
security:
  # Allowed file paths (glob patterns)
  allowed_paths:
    - "./**/*"
  
  # Denied file paths (glob patterns)
  denied_paths:
    - "/etc/*"
    - "/sys/*"
    - "/proc/*"
  
  # Maximum file size
  max_file_size: 10485760
  
  # Enable symlink following
  follow_symlinks: false
  
  # Sanitize filenames
  sanitize_filenames: true

# Plugin settings
plugins:
  # Enable plugins
  enabled: false
  
  # Plugin directory
  directory: "./plugins"
  
  # Auto-load plugins
  auto_load: true
  
  # Plugin allowlist
  allowlist: []
  
  # Plugin denylist
  denylist: []
```

## Environment Variables

All configuration options can be overridden using environment variables:

```bash
# General settings
export TRAPPER_KEEPER_CONFIG=/path/to/config.yaml
export TRAPPER_KEEPER_LOG_LEVEL=DEBUG

# Output settings
export TRAPPER_KEEPER_OUTPUT_DIR=/custom/output
export TRAPPER_KEEPER_OUTPUT_FORMAT=json

# Monitoring settings
export TRAPPER_KEEPER_WATCH_PATTERNS="*.md,*.txt"
export TRAPPER_KEEPER_IGNORE_PATTERNS="*.tmp,*.swp"

# MCP settings
export TRAPPER_KEEPER_MCP_HOST=0.0.0.0
export TRAPPER_KEEPER_MCP_PORT=3001

# Metrics settings
export TRAPPER_KEEPER_METRICS_ENABLED=true
export TRAPPER_KEEPER_METRICS_PORT=9091

# Performance settings
export TRAPPER_KEEPER_MAX_CONCURRENT=10
export TRAPPER_KEEPER_PROCESS_TIMEOUT=600
```

## Command-Line Arguments

Configuration can also be provided via command-line arguments:

```bash
# Override configuration file
trapper-keeper --config /path/to/custom.yaml process document.md

# Override output directory
trapper-keeper process document.md --output-dir /custom/output

# Override log level
trapper-keeper --log-level DEBUG process document.md

# Override categories
trapper-keeper extract document.md \
  --category "🏗️ Architecture" \
  --category "🔐 Security"

# Override importance threshold
trapper-keeper process document.md --min-importance 0.7
```

## Configuration Precedence

Configuration is loaded in this order (later overrides earlier):

1. Built-in defaults
2. Configuration files (in order listed above)
3. Environment variables
4. Command-line arguments

## Category Configuration

### Default Categories

```yaml
extraction:
  categories:
    - name: "🏗️ Architecture"
      keywords: ["architecture", "design", "structure", "pattern"]
      importance_boost: 0.2
      
    - name: "🔐 Security"
      keywords: ["security", "auth", "encryption", "password"]
      importance_boost: 0.3
      
    - name: "🚨 Critical"
      keywords: ["critical", "urgent", "breaking", "important"]
      importance_boost: 0.5
```

### Custom Categories

Add custom categories:

```yaml
extraction:
  categories:
    - "🎯 Custom Category"
  
detection:
  custom_patterns:
    "🎯 Custom Category":
      keywords: ["custom", "specific", "terms"]
      patterns: [".*custom pattern.*"]
      importance_boost: 0.1
```

## Output Configuration

### Output Formats

```yaml
output:
  formats:
    - name: "markdown"
      extension: ".md"
      template: "default"
      
    - name: "json"
      extension: ".json"
      pretty: true
      indent: 2
      
    - name: "yaml"
      extension: ".yaml"
      default_flow_style: false
```

### Grouping Options

```yaml
output:
  group_by: "category"  # Options: category, document, date, none
  
  # Category grouping
  category_groups:
    "Development":
      - "🏗️ Architecture"
      - "🌐 API"
      - "🧪 Testing"
    "Operations":
      - "🚀 Deployment"
      - "📊 Monitoring"
      - "⚙️ Configuration"
```

## Advanced Configuration

### Multi-Environment Setup

```yaml
# config.development.yaml
extends: config.yaml
logging:
  level: "DEBUG"
output:
  default_dir: "./dev-output"

# config.production.yaml
extends: config.yaml
logging:
  level: "WARNING"
performance:
  max_concurrent: 20
```

### Performance Tuning

```yaml
# For large file processing
performance:
  max_concurrent: 10
  process_timeout: 600
  memory_limit: 2048
  
parser:
  max_file_size: 52428800  # 50MB
  
# For many small files
performance:
  max_concurrent: 20
  process_timeout: 60
  enable_cache: true
  cache_size: 500
```

### Security Hardening

```yaml
security:
  # Restrict to specific directories
  allowed_paths:
    - "./docs/**/*"
    - "./content/**/*"
  
  # Explicitly deny sensitive paths
  denied_paths:
    - "**/.env"
    - "**/.git/**"
    - "**/secrets/**"
  
  # Disable symlinks
  follow_symlinks: false
  
  # Strict file size limit
  max_file_size: 5242880  # 5MB
```

## Validation

Validate your configuration:

```bash
# Validate configuration file
trapper-keeper config validate

# Show effective configuration
trapper-keeper config show

# Export current configuration
trapper-keeper config export > my-config.yaml
```

## Migration

Migrate from older versions:

```bash
# Migrate v0.x config to v1.0
trapper-keeper config migrate old-config.yaml > new-config.yaml
```

## Next Steps

- [CLI Guide](./cli-guide.md) - Learn all CLI commands
- [MCP Tools Reference](./mcp-tools.md) - Configure MCP tools
- [Troubleshooting](./troubleshooting.md) - Common configuration issues