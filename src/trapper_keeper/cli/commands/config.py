"""Config command for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
import yaml

from ..display import display_config
from ..prompts import prompt_for_categories, prompt_for_output_dir
from ...core.config import get_config_manager
from ...core.types import TrapperKeeperConfig, ProcessingConfig, OrganizationConfig, WatchConfig

console = Console()


@click.group(name='config')
@click.pass_context
def config(ctx):
    """Manage Trapper Keeper configuration.
    
    View, edit, and manage configuration settings for processing,
    organization, and monitoring behaviors.
    """
    pass


@config.command(name='show')
@click.option('--format', '-f', type=click.Choice(['tree', 'yaml', 'json']), default='tree', help='Output format')
@click.option('--section', '-s', type=click.Choice(['processing', 'organization', 'watching', 'system']), help='Show specific section')
@click.pass_context
def show_config(ctx, format, section):
    """Display current configuration."""
    config = ctx.obj['config']
    
    if section:
        # Show specific section
        section_config = getattr(config, section, None)
        if section_config:
            console.print(f"\n[bold cyan]{section.title()} Configuration[/bold cyan]\n")
            
            if format == 'tree':
                # Custom display for each section
                _display_section_config(section, section_config)
            else:
                # YAML/JSON display
                config_dict = {section: section_config.model_dump()}
                _display_config_format(config_dict, format)
        else:
            console.print(f"[red]Unknown section: {section}[/red]")
    else:
        # Show full config
        display_config(config.model_dump(), format)


@config.command(name='edit')
@click.option('--interactive', '-i', is_flag=True, help='Interactive configuration editor')
@click.pass_context
def edit_config(ctx):
    """Edit configuration settings."""
    if ctx.params['interactive']:
        _interactive_config_editor(ctx)
    else:
        # Open in default editor
        config_manager = ctx.obj['config_manager']
        config_path = config_manager.config_path
        
        if not config_path.exists():
            console.print("[yellow]No configuration file found. Creating default...[/yellow]")
            config_manager.save()
        
        # Open in editor
        click.edit(filename=str(config_path))
        
        # Reload configuration
        console.print("[cyan]Reloading configuration...[/cyan]")
        new_config = config_manager.load()
        ctx.obj['config'] = new_config
        console.print("[green]✓ Configuration reloaded[/green]")


@config.command(name='save')
@click.argument('path', type=click.Path(), required=False)
@click.pass_context
def save_config(ctx, path):
    """Save current configuration to file."""
    config_manager = ctx.obj['config_manager']
    
    if path:
        save_path = Path(path)
    else:
        save_path = config_manager.config_path
    
    config_manager.save(save_path)
    console.print(f"[green]✓ Configuration saved to {save_path}[/green]")


@config.command(name='load')
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def load_config(ctx, path):
    """Load configuration from file."""
    config_path = Path(path)
    
    if not config_path.exists():
        console.print(f"[red]Configuration file not found: {path}[/red]")
        return
    
    config_manager = get_config_manager(config_path)
    new_config = config_manager.load()
    
    ctx.obj['config'] = new_config
    ctx.obj['config_manager'] = config_manager
    
    console.print(f"[green]✓ Configuration loaded from {path}[/green]")


@config.command(name='reset')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
@click.pass_context
def reset_config(ctx, force):
    """Reset configuration to defaults."""
    if not force and not Confirm.ask("[red]Reset all settings to defaults?[/red]"):
        console.print("[yellow]Reset cancelled[/yellow]")
        return
    
    # Create default config
    default_config = TrapperKeeperConfig()
    
    ctx.obj['config'] = default_config
    config_manager = ctx.obj['config_manager']
    config_manager.config = default_config
    
    if Confirm.ask("Save default configuration to file?"):
        config_manager.save()
        console.print("[green]✓ Default configuration saved[/green]")
    
    console.print("[green]✓ Configuration reset to defaults[/green]")


@config.command(name='wizard')
@click.pass_context
def config_wizard(ctx):
    """Run configuration wizard."""
    console.print(Panel(
        "[bold cyan]Trapper Keeper Configuration Wizard[/bold cyan]\n\n"
        "This wizard will help you configure Trapper Keeper settings.",
        box=box.DOUBLE_EDGE
    ))
    
    config = ctx.obj['config']
    
    # Processing settings
    console.print("\n[bold]Processing Settings[/bold]")
    
    if Confirm.ask("Configure extraction categories?", default=True):
        config.processing.extract_categories = prompt_for_categories()
    
    config.processing.min_importance = IntPrompt.ask(
        "Minimum importance threshold (0-100)",
        default=int(config.processing.min_importance * 100)
    ) / 100.0
    
    config.processing.extract_code_blocks = Confirm.ask(
        "Extract code blocks?",
        default=config.processing.extract_code_blocks
    )
    
    # Organization settings
    console.print("\n[bold]Organization Settings[/bold]")
    
    if Confirm.ask("Configure output directory?", default=True):
        config.organization.output_dir = prompt_for_output_dir()
    
    config.organization.group_by_category = Confirm.ask(
        "Group output by category?",
        default=config.organization.group_by_category
    )
    
    config.organization.format = Prompt.ask(
        "Output format",
        choices=['markdown', 'json', 'yaml'],
        default=config.organization.format
    )
    
    # Watch settings
    console.print("\n[bold]Watch Settings[/bold]")
    
    patterns = Prompt.ask(
        "File patterns to watch (comma-separated)",
        default=",".join(config.watching.patterns)
    )
    config.watching.patterns = [p.strip() for p in patterns.split(",")]
    
    config.watching.recursive = Confirm.ask(
        "Watch subdirectories recursively?",
        default=config.watching.recursive
    )
    
    # Save configuration
    if Confirm.ask("\n[cyan]Save configuration?[/cyan]"):
        config_manager = ctx.obj['config_manager']
        config_manager.config = config
        config_manager.save()
        console.print("[green]✓ Configuration saved![/green]")
    
    console.print("\n[bold green]Configuration wizard complete![/bold green]")


def _interactive_config_editor(ctx):
    """Interactive configuration editor."""
    config = ctx.obj['config']
    config_manager = ctx.obj['config_manager']
    
    while True:
        # Display menu
        console.print("\n[bold cyan]Configuration Editor[/bold cyan]")
        console.print("1. Edit Processing Settings")
        console.print("2. Edit Organization Settings")
        console.print("3. Edit Watch Settings")
        console.print("4. Edit System Settings")
        console.print("5. View Current Configuration")
        console.print("6. Save Configuration")
        console.print("7. Exit")
        
        choice = Prompt.ask("\nSelect option", choices=['1', '2', '3', '4', '5', '6', '7'])
        
        if choice == '1':
            _edit_processing_settings(config)
        elif choice == '2':
            _edit_organization_settings(config)
        elif choice == '3':
            _edit_watch_settings(config)
        elif choice == '4':
            _edit_system_settings(config)
        elif choice == '5':
            display_config(config.model_dump(), 'tree')
        elif choice == '6':
            config_manager.save()
            console.print("[green]✓ Configuration saved[/green]")
        elif choice == '7':
            break


def _edit_processing_settings(config):
    """Edit processing configuration."""
    console.print("\n[bold]Processing Settings[/bold]")
    
    # Categories
    if Confirm.ask("Update extraction categories?"):
        config.processing.extract_categories = prompt_for_categories()
    
    # Importance threshold
    config.processing.min_importance = IntPrompt.ask(
        "Minimum importance (0-100)",
        default=int(config.processing.min_importance * 100)
    ) / 100.0
    
    # Toggles
    config.processing.extract_code_blocks = Confirm.ask(
        "Extract code blocks?",
        default=config.processing.extract_code_blocks
    )
    
    config.processing.extract_links = Confirm.ask(
        "Extract links?",
        default=config.processing.extract_links
    )
    
    config.processing.preserve_structure = Confirm.ask(
        "Preserve document structure?",
        default=config.processing.preserve_structure
    )
    
    console.print("[green]✓ Processing settings updated[/green]")


def _edit_organization_settings(config):
    """Edit organization configuration."""
    console.print("\n[bold]Organization Settings[/bold]")
    
    # Output directory
    config.organization.output_dir = prompt_for_output_dir()
    
    # Grouping
    config.organization.group_by_category = Confirm.ask(
        "Group by category?",
        default=config.organization.group_by_category
    )
    
    config.organization.group_by_document = Confirm.ask(
        "Group by document?",
        default=config.organization.group_by_document
    )
    
    # Format
    config.organization.format = Prompt.ask(
        "Output format",
        choices=['markdown', 'json', 'yaml'],
        default=config.organization.format
    )
    
    # Index
    config.organization.create_index = Confirm.ask(
        "Create index file?",
        default=config.organization.create_index
    )
    
    console.print("[green]✓ Organization settings updated[/green]")


def _edit_watch_settings(config):
    """Edit watch configuration."""
    console.print("\n[bold]Watch Settings[/bold]")
    
    # Patterns
    patterns = Prompt.ask(
        "File patterns (comma-separated)",
        default=",".join(config.watching.patterns)
    )
    config.watching.patterns = [p.strip() for p in patterns.split(",")]
    
    # Ignore patterns
    ignore = Prompt.ask(
        "Ignore patterns (comma-separated)",
        default=",".join(config.watching.ignore_patterns)
    )
    config.watching.ignore_patterns = [p.strip() for p in ignore.split(",")]
    
    # Options
    config.watching.recursive = Confirm.ask(
        "Watch recursively?",
        default=config.watching.recursive
    )
    
    config.watching.follow_symlinks = Confirm.ask(
        "Follow symlinks?",
        default=config.watching.follow_symlinks
    )
    
    config.watching.debounce_seconds = float(Prompt.ask(
        "Debounce seconds",
        default=str(config.watching.debounce_seconds)
    ))
    
    console.print("[green]✓ Watch settings updated[/green]")


def _edit_system_settings(config):
    """Edit system configuration."""
    console.print("\n[bold]System Settings[/bold]")
    
    # Logging
    config.log_level = Prompt.ask(
        "Log level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.log_level
    )
    
    # Concurrency
    config.max_concurrent_processing = IntPrompt.ask(
        "Max concurrent processing",
        default=config.max_concurrent_processing
    )
    
    # Metrics
    config.enable_metrics = Confirm.ask(
        "Enable metrics?",
        default=config.enable_metrics
    )
    
    if config.enable_metrics:
        config.metrics_port = IntPrompt.ask(
            "Metrics port",
            default=config.metrics_port
        )
    
    console.print("[green]✓ System settings updated[/green]")


def _display_section_config(section: str, config):
    """Display configuration section in a formatted way."""
    if section == 'processing':
        console.print(f"Min Importance: {config.min_importance}")
        console.print(f"Categories: {', '.join(config.extract_categories[:5])}...")
        console.print(f"Extract Code: {config.extract_code_blocks}")
        console.print(f"Extract Links: {config.extract_links}")
        console.print(f"Preserve Structure: {config.preserve_structure}")
    
    elif section == 'organization':
        console.print(f"Output Directory: {config.output_dir}")
        console.print(f"Group by Category: {config.group_by_category}")
        console.print(f"Format: {config.format}")
        console.print(f"Create Index: {config.create_index}")
    
    elif section == 'watching':
        console.print(f"Patterns: {', '.join(config.patterns)}")
        console.print(f"Recursive: {config.recursive}")
        console.print(f"Debounce: {config.debounce_seconds}s")
    
    elif section == 'system':
        console.print(f"Log Level: {config.log_level}")
        console.print(f"Max Concurrent: {config.max_concurrent_processing}")
        console.print(f"Metrics Enabled: {config.enable_metrics}")


def _display_config_format(config_dict: dict, format: str):
    """Display configuration in specified format."""
    if format == 'yaml':
        syntax = Syntax(
            yaml.dump(config_dict, default_flow_style=False),
            "yaml",
            theme="monokai",
            line_numbers=True
        )
        console.print(syntax)
    elif format == 'json':
        import json
        syntax = Syntax(
            json.dumps(config_dict, indent=2),
            "json",
            theme="monokai",
            line_numbers=True
        )
        console.print(syntax)