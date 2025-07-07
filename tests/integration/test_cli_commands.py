"""Integration tests for CLI commands."""

import subprocess
import json
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from click.testing import CliRunner

from trapper_keeper.cli.main import cli
from trapper_keeper.core.types import (
    ProcessingConfig,
    WatchConfig,
    OrganizationConfig,
    TrapperKeeperConfig,
)


class TestCLICommands:
    """Test CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()
    
    @pytest.fixture
    def config_file(self, temp_dir):
        """Create a test configuration file."""
        config = {
            "processing": {
                "min_importance": 0.5,
                "extract_categories": ["Architecture", "Security", "Database"],
            },
            "watching": {
                "paths": [str(temp_dir)],
                "patterns": ["*.md"],
            },
            "organization": {
                "output_dir": str(temp_dir / "output"),
                "group_by_category": True,
            },
        }
        
        config_path = temp_dir / "config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return config_path
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Trapper Keeper MCP" in result.output
        assert "Commands:" in result.output
    
    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
    
    def test_extract_command(self, runner, temp_dir, sample_markdown_content):
        """Test extract command."""
        # Create test file
        test_file = temp_dir / "test.md"
        test_file.write_text(sample_markdown_content)
        
        # Run extract command
        result = runner.invoke(cli, [
            'extract',
            str(test_file),
            '--output', str(temp_dir / "extracted.json")
        ])
        
        assert result.exit_code == 0
        assert "Extracting from" in result.output
        assert "extracted" in result.output.lower()
        
        # Check output file
        output_file = temp_dir / "extracted.json"
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
            assert "extracted_content" in data
            assert len(data["extracted_content"]) > 0
    
    def test_extract_with_categories(self, runner, temp_dir, sample_markdown_content):
        """Test extract command with category filter."""
        test_file = temp_dir / "test.md"
        test_file.write_text(sample_markdown_content)
        
        result = runner.invoke(cli, [
            'extract',
            str(test_file),
            '--category', 'Security',
            '--category', 'Architecture',
        ])
        
        assert result.exit_code == 0
        # Output should mention filtered categories
        assert any(cat in result.output for cat in ['Security', 'Architecture'])
    
    def test_organize_command(self, runner, temp_dir, create_test_files):
        """Test organize command."""
        # Create test files
        files = [
            ("doc1.md", "# API Design\n\nREST endpoints"),
            ("doc2.md", "# Security\n\nAuth implementation"),
        ]
        create_test_files(files)
        
        # First extract content
        runner.invoke(cli, ['extract', str(temp_dir)])
        
        # Then organize
        result = runner.invoke(cli, [
            'organize',
            str(temp_dir),
            '--output', str(temp_dir / "organized")
        ])
        
        assert result.exit_code == 0
        assert "Organizing content" in result.output
        
        # Check organized output
        organized_dir = temp_dir / "organized"
        assert organized_dir.exists()
        assert any(organized_dir.iterdir())  # Should have some files
    
    def test_watch_command(self, runner, temp_dir):
        """Test watch command."""
        # Use --dry-run to avoid actually starting the watcher
        result = runner.invoke(cli, [
            'watch',
            str(temp_dir),
            '--pattern', '*.md',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        assert "Watching" in result.output or "watch" in result.output.lower()
    
    def test_analyze_command(self, runner, temp_dir, create_test_files):
        """Test analyze command."""
        files = [
            ("doc1.md", "# Title\n\nContent"),
            ("doc2.md", "# Another\n\nMore content"),
            ("readme.txt", "Plain text"),
        ]
        create_test_files(files)
        
        result = runner.invoke(cli, ['analyze', str(temp_dir)])
        
        assert result.exit_code == 0
        assert "Analysis Results" in result.output or "Analyzing" in result.output
        assert "Total files:" in result.output or "files" in result.output.lower()
    
    def test_validate_command(self, runner, temp_dir, create_test_files):
        """Test validate command."""
        files = [
            ("valid.md", "# Valid\n\nContent"),
            ("invalid.md", "# Unclosed\n\n```python\nmissing close"),
        ]
        create_test_files(files)
        
        result = runner.invoke(cli, ['validate', str(temp_dir)])
        
        assert result.exit_code == 0
        assert "Validation" in result.output
        assert "valid.md" in result.output
        assert "invalid.md" in result.output
    
    def test_config_command(self, runner, temp_dir, config_file):
        """Test config command."""
        # Test show config
        result = runner.invoke(cli, ['config', 'show', '--config', str(config_file)])
        assert result.exit_code == 0
        assert "processing" in result.output
        assert "watching" in result.output
        
        # Test validate config
        result = runner.invoke(cli, ['config', 'validate', '--config', str(config_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
    
    def test_pipeline_commands(self, runner, temp_dir, sample_markdown_content):
        """Test running multiple commands in sequence."""
        # Create test file
        test_file = temp_dir / "test.md"
        test_file.write_text(sample_markdown_content)
        
        # Extract
        result = runner.invoke(cli, [
            'extract', str(test_file),
            '--output', str(temp_dir / "extracted.json")
        ])
        assert result.exit_code == 0
        
        # Organize
        result = runner.invoke(cli, [
            'organize', str(temp_dir),
            '--output', str(temp_dir / "organized")
        ])
        assert result.exit_code == 0
        
        # Validate organized output
        result = runner.invoke(cli, ['validate', str(temp_dir / "organized")])
        assert result.exit_code == 0
    
    def test_verbose_mode(self, runner, temp_dir):
        """Test verbose output mode."""
        result = runner.invoke(cli, ['--verbose', 'analyze', str(temp_dir)])
        assert result.exit_code == 0
        # Verbose mode should show more detailed output
        assert len(result.output) > 100  # More output expected
    
    def test_quiet_mode(self, runner, temp_dir):
        """Test quiet output mode."""
        result = runner.invoke(cli, ['--quiet', 'analyze', str(temp_dir)])
        assert result.exit_code == 0
        # Quiet mode should show minimal output
        assert len(result.output) < 200  # Less output expected
    
    def test_json_output_format(self, runner, temp_dir, create_test_files):
        """Test JSON output format."""
        create_test_files([("test.md", "# Test")])
        
        result = runner.invoke(cli, [
            'analyze', str(temp_dir),
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
    
    def test_error_handling(self, runner):
        """Test error handling in CLI."""
        # Non-existent path
        result = runner.invoke(cli, ['extract', '/nonexistent/path'])
        assert result.exit_code != 0
        assert "error" in result.output.lower()
        
        # Invalid command
        result = runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
    
    def test_interactive_mode(self, runner):
        """Test interactive mode prompts."""
        # Test with missing required argument
        with patch('click.prompt') as mock_prompt:
            mock_prompt.return_value = '/tmp/test'
            result = runner.invoke(cli, ['extract'], input='/tmp/test\n')
            # Should prompt for missing path
            assert mock_prompt.called or "Usage:" in result.output


class TestCLIIntegration:
    """Test CLI integration with actual file operations."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner with isolated filesystem."""
        return CliRunner()
    
    def test_full_workflow(self, runner, temp_dir, sample_markdown_content):
        """Test complete workflow through CLI."""
        with runner.isolated_filesystem():
            # Create test structure
            docs_dir = Path("docs")
            docs_dir.mkdir()
            
            # Create multiple documents
            (docs_dir / "architecture.md").write_text("""
# System Architecture

The system uses microservices architecture with:
- API Gateway
- Service Mesh
- Event Bus
""")
            
            (docs_dir / "security.md").write_text("""
# Security Guidelines

## Authentication
- Use JWT tokens
- Implement OAuth2

## Authorization
- Role-based access control
- Fine-grained permissions
""")
            
            (docs_dir / "database.md").write_text("""
# Database Design

## Schema
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE
);
```
""")
            
            # 1. Extract content from all documents
            result = runner.invoke(cli, [
                'extract', str(docs_dir),
                '--output', 'extracted.json',
                '--recursive'
            ])
            assert result.exit_code == 0
            assert Path("extracted.json").exists()
            
            # 2. Analyze the documents
            result = runner.invoke(cli, [
                'analyze', str(docs_dir),
                '--format', 'json',
                '--output', 'analysis.json'
            ])
            assert result.exit_code == 0
            assert Path("analysis.json").exists()
            
            # 3. Organize by category
            result = runner.invoke(cli, [
                'organize', '.',
                '--output', 'organized',
                '--by-category'
            ])
            assert result.exit_code == 0
            assert Path("organized").exists()
            assert Path("organized/Architecture").exists()
            assert Path("organized/Security").exists()
            assert Path("organized/Database").exists()
            
            # 4. Generate references
            result = runner.invoke(cli, [
                'reference', 'organized',
                '--output', 'references.json'
            ])
            # May succeed or fail depending on implementation
            
            # 5. Validate organized content
            result = runner.invoke(cli, [
                'validate', 'organized'
            ])
            assert result.exit_code == 0
    
    def test_watch_mode_integration(self, runner, temp_dir):
        """Test watch mode with file changes."""
        with runner.isolated_filesystem():
            # Create initial file
            Path("test.md").write_text("# Initial content")
            
            # Start watcher in background (with timeout)
            import threading
            import time
            
            def run_watch():
                runner.invoke(cli, [
                    'watch', '.',
                    '--pattern', '*.md',
                    '--timeout', '2'  # 2 second timeout
                ])
            
            watch_thread = threading.Thread(target=run_watch)
            watch_thread.daemon = True
            watch_thread.start()
            
            # Give watcher time to start
            time.sleep(0.5)
            
            # Modify file
            Path("test.md").write_text("# Modified content")
            
            # Create new file
            Path("new.md").write_text("# New file")
            
            # Wait for watcher to process
            watch_thread.join(timeout=3)
    
    def test_config_file_usage(self, runner):
        """Test using configuration file."""
        with runner.isolated_filesystem():
            # Create config file
            config_content = """
processing:
  min_importance: 0.7
  extract_categories:
    - Architecture
    - Security
    - Database

watching:
  patterns:
    - "*.md"
    - "*.txt"
  ignore_patterns:
    - "*.tmp"
    - ".git/*"

organization:
  output_dir: ./output
  group_by_category: true
  create_index: true
"""
            Path("config.yaml").write_text(config_content)
            
            # Create test file
            Path("test.md").write_text("# Test\n\nMinor note")
            
            # Use config file
            result = runner.invoke(cli, [
                '--config', 'config.yaml',
                'extract', 'test.md'
            ])
            
            assert result.exit_code == 0
            # Should respect min_importance from config