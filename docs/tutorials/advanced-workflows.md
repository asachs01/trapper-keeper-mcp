# Advanced Workflows Tutorial

This tutorial covers advanced use cases and workflows for power users of Trapper Keeper MCP.

## Workflow 1: Large Documentation Project

### Scenario
You have a large project with hundreds of documentation files that need organization.

### Step 1: Initial Analysis

Analyze the entire documentation structure:

```bash
# Get overview of all documentation
trapper-keeper analyze ./docs --detailed --generate-report -o analysis-report.md

# Find files that need organization
find ./docs -name "*.md" -size +50k -exec \
  trapper-keeper analyze {} --format json \; > large-files.json
```

### Step 2: Batch Processing Strategy

Create a processing script:

```bash
#!/bin/bash
# batch-organize.sh

# Configuration
BASE_DIR="./docs"
OUTPUT_DIR="./organized-docs"
LOG_FILE="./processing.log"

# Create output structure
mkdir -p "$OUTPUT_DIR"/{architecture,security,features,api,setup}

# Process by priority
echo "Processing critical documentation..." | tee -a "$LOG_FILE"
trapper-keeper process "$BASE_DIR" \
  -c "🚨 Critical" \
  -c "🔐 Security" \
  --min-importance 0.8 \
  -o "$OUTPUT_DIR/critical" \
  --parallel

echo "Processing architecture documentation..." | tee -a "$LOG_FILE"
trapper-keeper process "$BASE_DIR" \
  -c "🏗️ Architecture" \
  --min-importance 0.6 \
  -o "$OUTPUT_DIR/architecture" \
  --parallel

# Continue for other categories...
```

### Step 3: Validation and Cleanup

```bash
# Validate all processed files
trapper-keeper validate "$OUTPUT_DIR" \
  --check-references \
  --check-orphans \
  --fix

# Generate master index
trapper-keeper analyze "$OUTPUT_DIR" \
  --generate-index \
  -o "$OUTPUT_DIR/master-index.md"
```

## Workflow 2: CLAUDE.md Maintenance

### Scenario
Your CLAUDE.md file grows with each feature. You need automated maintenance.

### Step 1: Growth Monitoring

Create a monitoring script:

```python
#!/usr/bin/env python3
# monitor-claude.py

import subprocess
import json
from datetime import datetime
import os

def check_claude_growth():
    """Monitor CLAUDE.md growth and trigger organization."""
    
    # Analyze current state
    result = subprocess.run([
        "trapper-keeper", "analyze", "CLAUDE.md", 
        "--format", "json", "--growth", "--days", "7"
    ], capture_output=True, text=True)
    
    analysis = json.loads(result.stdout)
    
    # Check growth rate
    growth_rate = analysis.get("growth", {}).get("rate", 0)
    file_size = analysis.get("statistics", {}).get("total_size", 0)
    
    # Trigger organization if needed
    if growth_rate > 0.15 or file_size > 50000:  # 15% growth or >50KB
        print(f"Organizing CLAUDE.md - Growth: {growth_rate:.1%}, Size: {file_size}")
        organize_claude()
    else:
        print(f"CLAUDE.md stable - Growth: {growth_rate:.1%}, Size: {file_size}")

def organize_claude():
    """Organize CLAUDE.md into categories."""
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.rename("CLAUDE.md", f"CLAUDE.md.backup.{timestamp}")
    
    # Process with high importance threshold
    subprocess.run([
        "trapper-keeper", "process", f"CLAUDE.md.backup.{timestamp}",
        "--min-importance", "0.7",
        "-o", "./claude-organized",
        "--create-references"
    ])
    
    # Create new CLAUDE.md with references
    create_new_claude()

def create_new_claude():
    """Create new CLAUDE.md with references to organized content."""
    
    with open("CLAUDE.md", "w") as f:
        f.write("# CLAUDE.md - Project Context\n\n")
        f.write("This file contains references to organized documentation.\n\n")
        
        # Add references from organized content
        # ... implementation details ...

if __name__ == "__main__":
    check_claude_growth()
```

### Step 2: Automated Organization

Set up automated organization:

```bash
# Add to crontab
0 */6 * * * /path/to/monitor-claude.py

# Or use systemd timer
cat > /etc/systemd/system/claude-maintenance.service << EOF
[Unit]
Description=CLAUDE.md Maintenance
After=network.target

[Service]
Type=oneshot
ExecStart=/path/to/monitor-claude.py
User=youruser
EOF

cat > /etc/systemd/system/claude-maintenance.timer << EOF
[Unit]
Description=Run CLAUDE.md Maintenance every 6 hours
Requires=claude-maintenance.service

[Timer]
OnCalendar=0/6:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl enable claude-maintenance.timer
systemctl start claude-maintenance.timer
```

## Workflow 3: Multi-Repository Documentation

### Scenario
Managing documentation across multiple repositories.

### Step 1: Aggregation Script

```bash
#!/bin/bash
# aggregate-docs.sh

REPOS=(
    "https://github.com/org/repo1"
    "https://github.com/org/repo2"
    "https://github.com/org/repo3"
)

WORK_DIR="./multi-repo-docs"
OUTPUT_DIR="./unified-docs"

# Clone/update repositories
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

for repo in "${REPOS[@]}"; do
    repo_name=$(basename "$repo")
    if [ -d "$repo_name" ]; then
        echo "Updating $repo_name..."
        cd "$repo_name" && git pull && cd ..
    else
        echo "Cloning $repo_name..."
        git clone "$repo"
    fi
done

cd ..

# Process all repositories
for repo in "${REPOS[@]}"; do
    repo_name=$(basename "$repo")
    echo "Processing $repo_name..."
    
    trapper-keeper process "$WORK_DIR/$repo_name" \
        -p "*.md" \
        -p "docs/**/*.md" \
        -r \
        -o "$OUTPUT_DIR/$repo_name" \
        --create-index
done

# Create unified index
trapper-keeper analyze "$OUTPUT_DIR" \
    --generate-report \
    -o "$OUTPUT_DIR/unified-index.md"
```

### Step 2: Cross-Reference Generation

```python
#!/usr/bin/env python3
# generate-xref.py

import os
import re
from pathlib import Path

def generate_cross_references(base_dir):
    """Generate cross-references between repositories."""
    
    references = {}
    
    # Scan all markdown files
    for md_file in Path(base_dir).rglob("*.md"):
        content = md_file.read_text()
        
        # Find references to other repos
        repo_refs = re.findall(r'(?:repo1|repo2|repo3)/(\S+)', content)
        
        if repo_refs:
            references[str(md_file)] = repo_refs
    
    # Generate reference map
    with open(f"{base_dir}/cross-references.md", "w") as f:
        f.write("# Cross-Repository References\n\n")
        
        for file, refs in references.items():
            f.write(f"## {file}\n\n")
            for ref in refs:
                f.write(f"- [{ref}](./{ref})\n")
            f.write("\n")

if __name__ == "__main__":
    generate_cross_references("./unified-docs")
```

## Workflow 4: Documentation CI/CD Pipeline

### Scenario
Automated documentation processing in CI/CD pipeline.

### GitHub Actions Workflow

```yaml
# .github/workflows/docs-pipeline.yml
name: Documentation Pipeline

on:
  push:
    paths:
      - 'docs/**'
      - '**.md'
  pull_request:
    paths:
      - 'docs/**'
      - '**.md'
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      needs_organization: ${{ steps.check.outputs.needs_organization }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Trapper Keeper
        run: pip install trapper-keeper-mcp
      
      - name: Analyze Documentation
        id: check
        run: |
          trapper-keeper analyze . --format json > analysis.json
          
          # Check if organization needed
          TOTAL_SIZE=$(jq '.statistics.total_size' analysis.json)
          if [ $TOTAL_SIZE -gt 100000 ]; then
            echo "needs_organization=true" >> $GITHUB_OUTPUT
          else
            echo "needs_organization=false" >> $GITHUB_OUTPUT
          fi
      
      - name: Upload Analysis
        uses: actions/upload-artifact@v3
        with:
          name: documentation-analysis
          path: analysis.json

  organize:
    needs: analyze
    if: needs.analyze.outputs.needs_organization == 'true'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Trapper Keeper
        run: pip install trapper-keeper-mcp
      
      - name: Organize Documentation
        run: |
          trapper-keeper process . \
            -r \
            -o ./organized \
            --min-importance 0.6 \
            --parallel
      
      - name: Validate Organization
        run: |
          trapper-keeper validate ./organized \
            --check-references \
            --check-structure
      
      - name: Generate Reports
        run: |
          trapper-keeper analyze ./organized \
            --detailed \
            --generate-report \
            -o ./organized/report.md
      
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'docs: Organize documentation'
          title: 'Automated Documentation Organization'
          body: |
            This PR was automatically generated by the documentation pipeline.
            
            See the analysis report in `organized/report.md` for details.
          branch: docs/auto-organization
          delete-branch: true
```

## Workflow 5: Real-time Documentation Dashboard

### Scenario
Create a dashboard to monitor documentation health.

### Step 1: Metrics Collection

```python
#!/usr/bin/env python3
# collect-metrics.py

import subprocess
import json
import sqlite3
from datetime import datetime
import schedule
import time

def setup_database():
    """Create metrics database."""
    conn = sqlite3.connect('doc-metrics.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            timestamp TEXT,
            total_files INTEGER,
            total_size INTEGER,
            categories TEXT,
            avg_importance REAL,
            issues INTEGER
        )
    ''')
    
    conn.commit()
    return conn

def collect_metrics():
    """Collect documentation metrics."""
    
    # Run analysis
    result = subprocess.run([
        "trapper-keeper", "analyze", "./docs",
        "--format", "json", "--detailed"
    ], capture_output=True, text=True)
    
    analysis = json.loads(result.stdout)
    
    # Run validation
    val_result = subprocess.run([
        "trapper-keeper", "validate", "./docs",
        "--format", "json"
    ], capture_output=True, text=True)
    
    validation = json.loads(val_result.stdout)
    
    # Store metrics
    conn = setup_database()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        analysis['statistics']['total_files'],
        analysis['statistics']['total_size'],
        json.dumps(analysis['category_distribution']),
        analysis.get('avg_importance', 0.5),
        len(validation.get('issues', []))
    ))
    
    conn.commit()
    conn.close()

def generate_dashboard():
    """Generate HTML dashboard."""
    
    conn = sqlite3.connect('doc-metrics.db')
    cursor = conn.cursor()
    
    # Get recent metrics
    cursor.execute('''
        SELECT * FROM metrics 
        ORDER BY timestamp DESC 
        LIMIT 100
    ''')
    
    metrics = cursor.fetchall()
    
    # Generate HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Documentation Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .metric { display: inline-block; margin: 20px; padding: 20px; 
                     background: #f0f0f0; border-radius: 8px; }
            .chart { width: 100%; height: 400px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>Documentation Health Dashboard</h1>
        
        <div class="metrics">
            <div class="metric">
                <h3>Total Files</h3>
                <p style="font-size: 2em;">{}</p>
            </div>
            <div class="metric">
                <h3>Total Size</h3>
                <p style="font-size: 2em;">{:.1f} MB</p>
            </div>
            <div class="metric">
                <h3>Issues</h3>
                <p style="font-size: 2em;">{}</p>
            </div>
        </div>
        
        <div id="size-chart" class="chart"></div>
        <div id="issues-chart" class="chart"></div>
        
        <script>
            // Add Plotly charts here
        </script>
    </body>
    </html>
    """.format(
        metrics[0][1],  # total_files
        metrics[0][2] / 1024 / 1024,  # total_size in MB
        metrics[0][5]   # issues
    )
    
    with open("dashboard.html", "w") as f:
        f.write(html)
    
    conn.close()

# Schedule metrics collection
schedule.every(1).hours.do(collect_metrics)
schedule.every(1).hours.do(generate_dashboard)

# Run immediately
collect_metrics()
generate_dashboard()

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Workflow 6: Smart Content Migration

### Scenario
Migrating documentation between different formats or structures.

### Migration Script

```python
#!/usr/bin/env python3
# migrate-docs.py

import os
import shutil
from pathlib import Path
import subprocess
import yaml

class DocumentationMigrator:
    def __init__(self, source_dir, target_dir, config_file):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file):
        """Load migration configuration."""
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def migrate(self):
        """Execute migration workflow."""
        
        # Step 1: Analyze source
        print("Analyzing source documentation...")
        self.analyze_source()
        
        # Step 2: Create target structure
        print("Creating target structure...")
        self.create_target_structure()
        
        # Step 3: Process and migrate
        print("Processing documentation...")
        self.process_documentation()
        
        # Step 4: Validate migration
        print("Validating migration...")
        self.validate_migration()
        
        # Step 5: Generate migration report
        print("Generating report...")
        self.generate_report()
    
    def analyze_source(self):
        """Analyze source documentation."""
        
        result = subprocess.run([
            "trapper-keeper", "analyze", 
            str(self.source_dir),
            "--detailed", "--format", "json"
        ], capture_output=True, text=True)
        
        self.source_analysis = json.loads(result.stdout)
    
    def create_target_structure(self):
        """Create organized target structure."""
        
        # Create category directories
        for category in self.config['categories']:
            cat_dir = self.target_dir / category['name'].lower().replace(" ", "-")
            cat_dir.mkdir(parents=True, exist_ok=True)
    
    def process_documentation(self):
        """Process and migrate documentation."""
        
        for category in self.config['categories']:
            print(f"Processing {category['name']}...")
            
            # Extract category content
            subprocess.run([
                "trapper-keeper", "process",
                str(self.source_dir),
                "-c", category['emoji'] + " " + category['name'],
                "--min-importance", str(category.get('min_importance', 0.5)),
                "-o", str(self.target_dir / category['output_dir']),
                "--format", category.get('format', 'markdown')
            ])
    
    def validate_migration(self):
        """Validate migrated documentation."""
        
        # Check structure
        subprocess.run([
            "trapper-keeper", "validate",
            str(self.target_dir),
            "--check-structure",
            "--check-references",
            "--fix"
        ])
    
    def generate_report(self):
        """Generate migration report."""
        
        report = f"""# Documentation Migration Report
        
## Summary
- Source: {self.source_dir}
- Target: {self.target_dir}
- Files Processed: {self.source_analysis['statistics']['total_files']}
- Categories Migrated: {len(self.config['categories'])}

## Migration Details
"""
        
        # Add category details
        for category in self.config['categories']:
            cat_dir = self.target_dir / category['output_dir']
            files = list(cat_dir.glob("*.md"))
            
            report += f"""
### {category['emoji']} {category['name']}
- Files: {len(files)}
- Location: {category['output_dir']}
"""
        
        with open(self.target_dir / "migration-report.md", "w") as f:
            f.write(report)

# Migration configuration example
migration_config = """
categories:
  - name: Architecture
    emoji: 🏗️
    output_dir: architecture
    min_importance: 0.7
    format: markdown
    
  - name: API Documentation
    emoji: 🌐
    output_dir: api
    min_importance: 0.6
    format: json
    
  - name: Security
    emoji: 🔐
    output_dir: security
    min_importance: 0.8
    format: markdown

migration_rules:
  - source_pattern: "*/api/*"
    target_category: "API Documentation"
    
  - source_pattern: "*/security/*"
    target_category: "Security"
"""

if __name__ == "__main__":
    # Save config
    with open("migration-config.yaml", "w") as f:
        f.write(migration_config)
    
    # Run migration
    migrator = DocumentationMigrator(
        "./old-docs",
        "./new-docs",
        "migration-config.yaml"
    )
    
    migrator.migrate()
```

## Best Practices for Advanced Workflows

### 1. Error Handling

Always include error handling in scripts:

```python
try:
    result = subprocess.run(["trapper-keeper", "process", file], 
                          capture_output=True, text=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error processing {file}: {e.stderr}")
    # Log error, continue with next file
```

### 2. Progress Tracking

For long-running operations:

```python
from tqdm import tqdm

files = list(Path("./docs").rglob("*.md"))
for file in tqdm(files, desc="Processing files"):
    # Process file
```

### 3. Parallel Processing

For better performance:

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def process_file(file_path):
    subprocess.run(["trapper-keeper", "process", file_path])

with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
    executor.map(process_file, file_list)
```

### 4. Configuration Management

Use environment-specific configs:

```yaml
# config.development.yaml
extends: config.base.yaml
output:
  default_dir: ./dev-output
logging:
  level: DEBUG

# config.production.yaml
extends: config.base.yaml
output:
  default_dir: /var/docs/organized
logging:
  level: WARNING
```

### 5. Monitoring and Alerting

Set up alerts for documentation issues:

```python
def check_documentation_health():
    """Check documentation health and send alerts."""
    
    issues = []
    
    # Check file sizes
    large_files = find_large_files("./docs", max_size=100000)
    if large_files:
        issues.append(f"Large files found: {large_files}")
    
    # Check organization
    result = subprocess.run(["trapper-keeper", "validate", "./docs"], 
                          capture_output=True, text=True)
    if "error" in result.stdout.lower():
        issues.append("Validation errors found")
    
    # Send alerts
    if issues:
        send_alert(issues)

def send_alert(issues):
    """Send alert via webhook, email, etc."""
    # Implementation depends on your notification system
    pass
```

## Next Steps

- [Integration Guide](./integration-guide.md) - Integrate with other tools
- [Custom Categories](./custom-categories.md) - Create domain-specific categories
- [Plugin Development](../development/plugin-development.md) - Extend functionality