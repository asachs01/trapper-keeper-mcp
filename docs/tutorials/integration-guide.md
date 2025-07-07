# Integration Guide

This guide shows how to integrate Trapper Keeper MCP with various tools and platforms.

## IDE Integrations

### VS Code Integration

#### Extension Setup

Create a VS Code extension for Trapper Keeper:

```json
// .vscode/extensions/trapper-keeper/package.json
{
  "name": "trapper-keeper-vscode",
  "displayName": "Trapper Keeper",
  "version": "1.0.0",
  "engines": {
    "vscode": "^1.74.0"
  },
  "main": "./extension.js",
  "contributes": {
    "commands": [
      {
        "command": "trapperKeeper.processFile",
        "title": "Trapper Keeper: Process Current File"
      },
      {
        "command": "trapperKeeper.organizeWorkspace",
        "title": "Trapper Keeper: Organize Workspace Documentation"
      }
    ],
    "menus": {
      "editor/context": [
        {
          "command": "trapperKeeper.processFile",
          "when": "resourceExtname == .md",
          "group": "trapperKeeper"
        }
      ]
    },
    "configuration": {
      "title": "Trapper Keeper",
      "properties": {
        "trapperKeeper.minImportance": {
          "type": "number",
          "default": 0.5,
          "description": "Minimum importance threshold"
        },
        "trapperKeeper.outputDir": {
          "type": "string",
          "default": "./tk-output",
          "description": "Output directory for organized content"
        }
      }
    }
  }
}
```

#### Extension Code

```javascript
// extension.js
const vscode = require('vscode');
const { exec } = require('child_process');
const path = require('path');

function activate(context) {
    // Process current file command
    let processFile = vscode.commands.registerCommand('trapperKeeper.processFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        
        const filePath = editor.document.fileName;
        const config = vscode.workspace.getConfiguration('trapperKeeper');
        
        const command = `trapper-keeper process "${filePath}" --min-importance ${config.minImportance} -o "${config.outputDir}"`;
        
        exec(command, (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage(`Trapper Keeper Error: ${stderr}`);
                return;
            }
            
            vscode.window.showInformationMessage('Document processed successfully!');
            
            // Open output in new panel
            const outputPath = path.join(config.outputDir, 'index.md');
            vscode.workspace.openTextDocument(outputPath).then(doc => {
                vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
            });
        });
    });
    
    context.subscriptions.push(processFile);
}

module.exports = { activate };
```

### JetBrains IDE Integration

Create a plugin for IntelliJ-based IDEs:

```kotlin
// TrapperKeeperAction.kt
package com.trapperkeeper.intellij

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import java.io.BufferedReader
import java.io.InputStreamReader

class ProcessDocumentAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project: Project = e.project ?: return
        val file: VirtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
        
        if (file.extension != "md") {
            return
        }
        
        val command = arrayOf(
            "trapper-keeper",
            "process",
            file.path,
            "--min-importance",
            "0.5"
        )
        
        try {
            val process = Runtime.getRuntime().exec(command)
            val reader = BufferedReader(InputStreamReader(process.inputStream))
            
            val output = reader.readLines().joinToString("\n")
            
            // Show notification
            showNotification(project, "Document processed successfully")
            
        } catch (ex: Exception) {
            showError(project, "Error: ${ex.message}")
        }
    }
    
    override fun update(e: AnActionEvent) {
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE)
        e.presentation.isEnabled = file?.extension == "md"
    }
}
```

## Git Integration

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if any markdown files are being committed
MD_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$')

if [ -n "$MD_FILES" ]; then
    echo "Running Trapper Keeper validation..."
    
    # Validate structure
    for file in $MD_FILES; do
        trapper-keeper validate "$file" --strict
        if [ $? -ne 0 ]; then
            echo "Validation failed for $file"
            exit 1
        fi
    done
    
    # Check if files need organization
    for file in $MD_FILES; do
        SIZE=$(wc -c < "$file")
        if [ $SIZE -gt 50000 ]; then
            echo "Warning: $file is large (${SIZE} bytes)"
            echo "Consider running: trapper-keeper organize $file"
        fi
    done
fi

exit 0
```

### Git Attributes

```gitattributes
# .gitattributes
*.md filter=trapper-keeper-clean
*.md diff=trapper-keeper-diff
```

Setup filters:

```bash
# Clean filter - run before staging
git config filter.trapper-keeper-clean.clean 'trapper-keeper validate --fix --quiet -'

# Diff filter - better diffs for organized docs
git config diff.trapper-keeper-diff.textconv 'trapper-keeper analyze --format text'
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/documentation.yml
name: Documentation Management

on:
  push:
    paths:
      - '**.md'
  pull_request:
    paths:
      - '**.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Trapper Keeper
        run: |
          pip install trapper-keeper-mcp
          trapper-keeper --version
      
      - name: Validate Documentation
        run: |
          trapper-keeper validate . \
            --check-references \
            --check-structure \
            --strict
      
      - name: Check Organization Needs
        id: check
        run: |
          LARGE_FILES=$(find . -name "*.md" -size +50k | wc -l)
          echo "large_files=$LARGE_FILES" >> $GITHUB_OUTPUT
      
      - name: Comment PR
        if: github.event_name == 'pull_request' && steps.check.outputs.large_files > 0
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '⚠️ Large documentation files detected. Consider running `trapper-keeper organize` to split them into manageable sections.'
            })

  organize:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Trapper Keeper
        run: pip install trapper-keeper-mcp
      
      - name: Organize Documentation
        run: |
          trapper-keeper process . \
            -r \
            --min-importance 0.6 \
            -o ./organized-docs \
            --create-index
      
      - name: Deploy to Documentation Site
        run: |
          # Deploy organized docs to your documentation platform
          echo "Deploying to documentation site..."
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - organize
  - deploy

validate-docs:
  stage: validate
  image: python:3.11
  script:
    - pip install trapper-keeper-mcp
    - trapper-keeper validate . --strict
  only:
    changes:
      - "**.md"

organize-docs:
  stage: organize
  image: python:3.11
  script:
    - pip install trapper-keeper-mcp
    - trapper-keeper process . -r -o ./public
  artifacts:
    paths:
      - public
  only:
    - main

pages:
  stage: deploy
  dependencies:
    - organize-docs
  script:
    - echo "Deploying to GitLab Pages"
  artifacts:
    paths:
      - public
  only:
    - main
```

## Documentation Platform Integration

### MkDocs Integration

```yaml
# mkdocs.yml
site_name: My Project Documentation
site_dir: site
docs_dir: organized-docs

plugins:
  - search
  - trapper-keeper:
      watch_original: true
      auto_organize: true
      min_importance: 0.6

nav:
  - Home: index.md
  - Architecture: !include organized-docs/architecture/
  - API: !include organized-docs/api/
  - Security: !include organized-docs/security/
```

Plugin implementation:

```python
# mkdocs_trapper_keeper/plugin.py
from mkdocs.plugins import BasePlugin
import subprocess

class TrapperKeeperPlugin(BasePlugin):
    config_scheme = (
        ('watch_original', config_options.Type(bool, default=True)),
        ('auto_organize', config_options.Type(bool, default=True)),
        ('min_importance', config_options.Type(float, default=0.5)),
    )
    
    def on_pre_build(self, config):
        """Organize documentation before building."""
        if self.config['auto_organize']:
            subprocess.run([
                'trapper-keeper', 'process', 
                config['docs_dir'],
                '--min-importance', str(self.config['min_importance']),
                '-o', 'organized-docs'
            ])
    
    def on_serve(self, server, config, builder):
        """Watch for changes during development."""
        if self.config['watch_original']:
            subprocess.Popen([
                'trapper-keeper', 'watch',
                config['docs_dir'],
                '--auto-organize',
                '-o', 'organized-docs'
            ])
        return server
```

### Docusaurus Integration

```javascript
// docusaurus.config.js
module.exports = {
  title: 'My Project',
  plugins: [
    [
      './plugins/trapper-keeper',
      {
        sourceDir: './docs-source',
        outputDir: './docs',
        minImportance: 0.6,
        categories: ['🏗️ Architecture', '🌐 API', '🔐 Security']
      }
    ]
  ]
};
```

Plugin implementation:

```javascript
// plugins/trapper-keeper/index.js
const { exec } = require('child_process');
const path = require('path');

module.exports = function(context, options) {
  return {
    name: 'docusaurus-plugin-trapper-keeper',
    
    async loadContent() {
      // Process documentation
      return new Promise((resolve, reject) => {
        const command = `trapper-keeper process "${options.sourceDir}" -o "${options.outputDir}" --min-importance ${options.minImportance}`;
        
        exec(command, (error, stdout, stderr) => {
          if (error) {
            reject(error);
            return;
          }
          resolve();
        });
      });
    },
    
    async contentLoaded({content, actions}) {
      // Create pages from organized content
      const {createData, addRoute} = actions;
      
      // Add organized documentation routes
    }
  };
};
```

## API Integration

### REST API Wrapper

```python
# trapper_keeper_api.py
from flask import Flask, request, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

@app.route('/api/process', methods=['POST'])
def process_document():
    """Process uploaded document."""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    categories = request.form.getlist('categories')
    min_importance = float(request.form.get('min_importance', 0.5))
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp:
        file.save(tmp.name)
        
        # Process with Trapper Keeper
        cmd = ['trapper-keeper', 'process', tmp.name, 
               '--min-importance', str(min_importance),
               '--format', 'json']
        
        if categories:
            for cat in categories:
                cmd.extend(['-c', cat])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up
        os.unlink(tmp.name)
        
        if result.returncode == 0:
            return jsonify(json.loads(result.stdout))
        else:
            return jsonify({'error': result.stderr}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    """Analyze document content."""
    
    content = request.json.get('content', '')
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp:
        tmp.write(content)
        tmp.flush()
        
        cmd = ['trapper-keeper', 'analyze', tmp.name, '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        os.unlink(tmp.name)
        
        if result.returncode == 0:
            return jsonify(json.loads(result.stdout))
        else:
            return jsonify({'error': result.stderr}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### GraphQL API

```python
# graphql_schema.py
import graphene
from graphene import ObjectType, String, Float, List, Field
import subprocess
import json

class Category(ObjectType):
    name = String()
    emoji = String()
    percentage = Float()

class AnalysisResult(ObjectType):
    total_size = String()
    total_lines = String()
    categories = List(Category)
    recommendations = List(String)

class Query(ObjectType):
    analyze = Field(
        AnalysisResult,
        file_path=String(required=True)
    )
    
    def resolve_analyze(self, info, file_path):
        cmd = ['trapper-keeper', 'analyze', file_path, '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return AnalysisResult(
                total_size=str(data['statistics']['total_size']),
                total_lines=str(data['statistics']['total_lines']),
                categories=[
                    Category(
                        name=cat['category'],
                        emoji=cat['category'].split()[0],
                        percentage=cat['percentage']
                    )
                    for cat in data['category_distribution']
                ],
                recommendations=data.get('recommendations', [])
            )
        return None

schema = graphene.Schema(query=Query)
```

## Database Integration

### SQLite Storage

```python
# sqlite_integration.py
import sqlite3
import subprocess
import json
from datetime import datetime

class TrapperKeeperDB:
    def __init__(self, db_path='trapper_keeper.db'):
        self.conn = sqlite3.connect(db_path)
        self.setup_tables()
    
    def setup_tables(self):
        """Create database tables."""
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                last_processed TIMESTAMP,
                size INTEGER,
                checksum TEXT
            );
            
            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY,
                document_id INTEGER,
                category TEXT,
                title TEXT,
                content TEXT,
                importance REAL,
                extracted_at TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );
            
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                document_id INTEGER,
                metric_type TEXT,
                value REAL,
                recorded_at TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );
        ''')
        self.conn.commit()
    
    def process_and_store(self, file_path):
        """Process document and store results."""
        
        # Process document
        cmd = ['trapper-keeper', 'process', file_path, '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Processing failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        
        # Store document
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO documents (file_path, last_processed, size)
            VALUES (?, ?, ?)
        ''', (file_path, datetime.now(), data['statistics']['size']))
        
        doc_id = cursor.lastrowid
        
        # Store extractions
        for extraction in data['extracted']:
            cursor.execute('''
                INSERT INTO extractions 
                (document_id, category, title, content, importance, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                doc_id,
                extraction['category'],
                extraction['title'],
                extraction['content'],
                extraction['importance'],
                datetime.now()
            ))
        
        self.conn.commit()
        return doc_id
    
    def get_document_history(self, file_path):
        """Get processing history for a document."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT d.*, COUNT(e.id) as extraction_count
            FROM documents d
            LEFT JOIN extractions e ON d.id = e.document_id
            WHERE d.file_path = ?
            GROUP BY d.id
        ''', (file_path,))
        
        return cursor.fetchone()
```

## Notification Integration

### Slack Integration

```python
# slack_integration.py
import requests
import subprocess
import json

class TrapperKeeperSlack:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def process_and_notify(self, file_path, channel='#documentation'):
        """Process document and send Slack notification."""
        
        # Analyze document
        cmd = ['trapper-keeper', 'analyze', file_path, '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.send_error(file_path, result.stderr, channel)
            return
        
        analysis = json.loads(result.stdout)
        
        # Build Slack message
        message = {
            'channel': channel,
            'attachments': [{
                'color': 'good',
                'title': f'Documentation Analysis: {file_path}',
                'fields': [
                    {
                        'title': 'Size',
                        'value': f"{analysis['statistics']['total_size']} bytes",
                        'short': True
                    },
                    {
                        'title': 'Categories',
                        'value': len(analysis['category_distribution']),
                        'short': True
                    },
                    {
                        'title': 'Top Category',
                        'value': analysis['category_distribution'][0]['category'],
                        'short': True
                    },
                    {
                        'title': 'Recommendations',
                        'value': '\n'.join(analysis.get('recommendations', ['None'])),
                        'short': False
                    }
                ]
            }]
        }
        
        # Send to Slack
        requests.post(self.webhook_url, json=message)
    
    def send_error(self, file_path, error, channel='#documentation'):
        """Send error notification to Slack."""
        message = {
            'channel': channel,
            'attachments': [{
                'color': 'danger',
                'title': f'Documentation Processing Failed: {file_path}',
                'text': error
            }]
        }
        requests.post(self.webhook_url, json=message)
```

### Email Integration

```python
# email_integration.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import json

class TrapperKeeperEmail:
    def __init__(self, smtp_host, smtp_port, username, password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_analysis_report(self, file_path, recipient):
        """Send analysis report via email."""
        
        # Generate analysis
        cmd = ['trapper-keeper', 'analyze', file_path, 
               '--format', 'json', '--detailed']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return False
        
        analysis = json.loads(result.stdout)
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Documentation Analysis: {file_path}'
        msg['From'] = self.username
        msg['To'] = recipient
        
        # Create HTML report
        html = self.create_html_report(file_path, analysis)
        
        # Attach HTML
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        # Send email
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
        
        return True
    
    def create_html_report(self, file_path, analysis):
        """Create HTML email report."""
        return f"""
        <html>
        <body>
            <h2>Documentation Analysis Report</h2>
            <p><strong>File:</strong> {file_path}</p>
            
            <h3>Statistics</h3>
            <ul>
                <li>Size: {analysis['statistics']['total_size']} bytes</li>
                <li>Lines: {analysis['statistics']['total_lines']}</li>
                <li>Sections: {analysis['statistics']['total_sections']}</li>
            </ul>
            
            <h3>Category Distribution</h3>
            <table border="1">
                <tr><th>Category</th><th>Percentage</th></tr>
                {''.join(f"<tr><td>{cat['category']}</td><td>{cat['percentage']}%</td></tr>" 
                        for cat in analysis['category_distribution'])}
            </table>
            
            <h3>Recommendations</h3>
            <ul>
                {''.join(f"<li>{rec}</li>" for rec in analysis.get('recommendations', []))}
            </ul>
        </body>
        </html>
        """
```

## Cloud Integration

### AWS S3 Integration

```python
# s3_integration.py
import boto3
import subprocess
import tempfile
import os

class TrapperKeeperS3:
    def __init__(self, bucket_name, region='us-east-1'):
        self.s3 = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
    
    def process_from_s3(self, s3_key, output_prefix='organized/'):
        """Process document from S3 and upload results."""
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp:
            self.s3.download_file(self.bucket_name, s3_key, tmp.name)
            
            # Process document
            output_dir = tempfile.mkdtemp()
            cmd = [
                'trapper-keeper', 'process', tmp.name,
                '-o', output_dir,
                '--create-index'
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                # Upload results
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        local_path = os.path.join(root, file)
                        s3_path = f"{output_prefix}{file}"
                        
                        self.s3.upload_file(
                            local_path, 
                            self.bucket_name, 
                            s3_path
                        )
                
                # Cleanup
                os.unlink(tmp.name)
                shutil.rmtree(output_dir)
                
                return True
            
            return False
```

## Next Steps

- [Custom Categories](./custom-categories.md) - Create domain-specific categories
- [Plugin Development](../development/plugin-development.md) - Extend functionality
- [API Reference](../api-reference.md) - Detailed API documentation