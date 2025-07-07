"""CLI implementation for Trapper Keeper."""

import asyncio
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import structlog

from ..core.config import get_config_manager
from ..core.types import TrapperKeeperConfig, WatchConfig, EventType
from ..core.base import EventBus
from ..monitoring import DirectoryWatcher
from ..mcp.orchestrator import ProcessingOrchestrator

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()


@click.group(invoke_without_command=True)
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--interactive', '-i', is_flag=True, help='Start in interactive mode')
@click.version_option(version='1.0.0', prog_name='Trapper Keeper')
@click.pass_context
def cli(ctx, config, interactive):
    """Trapper Keeper - Intelligent document extraction and organization.
    
    A powerful tool for organizing and extracting content from large documentation files.
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    config_path = Path(config) if config else None
    config_manager = get_config_manager(config_path)
    ctx.obj['config'] = config_manager.load()
    ctx.obj['config_manager'] = config_manager
    
    # If no command specified or interactive mode, start interactive session
    if ctx.invoked_subcommand is None or interactive:
        from .interactive import start_interactive_mode
        start_interactive_mode(ctx)


# Import command groups
from .commands import organize, extract, watch as watch_cmd, validate, analyze, config as config_cmd

# Register command groups
cli.add_command(organize.organize)
cli.add_command(extract.extract)
cli.add_command(watch_cmd.watch)
cli.add_command(validate.validate)
cli.add_command(analyze.analyze)
cli.add_command(config_cmd.config)


@cli.command(name='process')
@click.argument('path', type=click.Path(exists=True))
@click.option('--categories', '-c', multiple=True, help='Categories to extract')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'yaml']), default='markdown')
@click.pass_context
def process_command(ctx, path, categories, output, format):
    """Process a file or directory (legacy command)."""
    config = ctx.obj['config']
    
    # Update config with command options
    if categories:
        config.processing.extract_categories = list(categories)
    if output:
        config.organization.output_dir = Path(output)
    config.organization.format = format
    
    # Run processing
    asyncio.run(_process_path(Path(path), config))


# Watch command moved to commands/watch.py


@cli.command()
@click.pass_context
def categories(ctx):
    """List available extraction categories."""
    from ..core.types import ExtractionCategory
    from .display import display_categories
    
    display_categories()


@cli.command()
@click.pass_context
def server(ctx):
    """Run as MCP server."""
    from ..mcp.server import main
    main()


# Config command moved to commands/config.py


async def _process_path(path: Path, config: TrapperKeeperConfig):
    """Process a file or directory."""
    event_bus = EventBus()
    orchestrator = ProcessingOrchestrator(config, event_bus)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing...", total=None)
        
        await orchestrator.initialize()
        await orchestrator.start()
        
        try:
            if path.is_file():
                progress.update(task, description=f"Processing {path.name}")
                result = await orchestrator.process_file(path)
                
                if result.success:
                    console.print(f"[green]✓ Processed {path.name}[/green]")
                    console.print(f"  Extracted {len(result.extracted_contents)} items")
                else:
                    console.print(f"[red]✗ Failed to process {path.name}[/red]")
                    for error in result.errors:
                        console.print(f"  {error}")
                        
            else:
                # Process directory
                progress.update(task, description="Scanning directory...")
                
                results = await orchestrator.process_directory(path)
                
                # Show summary
                successful = sum(1 for r in results if r.success)
                total_extracted = sum(len(r.extracted_contents) for r in results)
                
                console.print(f"\n[bold]Processing Summary:[/bold]")
                console.print(f"  Files processed: {len(results)}")
                console.print(f"  Successful: {successful}")
                console.print(f"  Failed: {len(results) - successful}")
                console.print(f"  Total items extracted: {total_extracted}")
                
                # Show failures
                failures = [r for r in results if not r.success]
                if failures:
                    console.print("\n[red]Failed files:[/red]")
                    for result in failures:
                        console.print(f"  {result.document_id}: {', '.join(result.errors)}")
                        
        finally:
            await orchestrator.stop()


async def _watch_directory(
    watch_config: WatchConfig,
    config: TrapperKeeperConfig,
    process_existing: bool
):
    """Watch a directory for changes."""
    event_bus = EventBus()
    
    # Create components
    watcher = DirectoryWatcher(watch_config, event_bus, process_existing)
    orchestrator = ProcessingOrchestrator(config, event_bus)
    
    console.print("[bold]Starting directory watcher...[/bold]")
    console.print(f"  Directory: {watch_config.paths[0]}")
    console.print(f"  Patterns: {', '.join(watch_config.patterns)}")
    console.print(f"  Recursive: {watch_config.recursive}")
    console.print(f"  Process existing: {process_existing}")
    console.print("\nPress Ctrl+C to stop watching.\n")
    
    # Initialize and start
    await watcher.initialize()
    await orchestrator.initialize()
    
    await watcher.start()
    await orchestrator.start()
    
    # Subscribe to events for console output
    created_queue = event_bus.subscribe(EventType.FILE_CREATED)
    modified_queue = event_bus.subscribe(EventType.FILE_MODIFIED)
    deleted_queue = event_bus.subscribe(EventType.FILE_DELETED)
    completed_queue = event_bus.subscribe(EventType.PROCESSING_COMPLETED)
    failed_queue = event_bus.subscribe(EventType.PROCESSING_FAILED)
    
    try:
        while True:
            # Check for events
            try:
                event = await asyncio.wait_for(created_queue.get(), timeout=0.1)
                console.print(f"[blue]+ Created: {event.data['path']}[/blue]")
            except asyncio.TimeoutError:
                pass
                
            try:
                event = await asyncio.wait_for(modified_queue.get(), timeout=0.1)
                console.print(f"[yellow]~ Modified: {event.data['path']}[/yellow]")
            except asyncio.TimeoutError:
                pass
                
            try:
                event = await asyncio.wait_for(deleted_queue.get(), timeout=0.1)
                console.print(f"[red]- Deleted: {event.data['path']}[/red]")
            except asyncio.TimeoutError:
                pass
                
            try:
                event = await asyncio.wait_for(completed_queue.get(), timeout=0.1)
                console.print(
                    f"[green]✓ Processed: {event.data['path']} "
                    f"({event.data['extracted_count']} items)[/green]"
                )
            except asyncio.TimeoutError:
                pass
                
            try:
                event = await asyncio.wait_for(failed_queue.get(), timeout=0.1)
                console.print(f"[red]✗ Failed: {event.data['path']} - {event.data['error']}[/red]")
            except asyncio.TimeoutError:
                pass
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping watcher...[/yellow]")
    finally:
        await watcher.stop()
        await orchestrator.stop()
        console.print("[green]Watcher stopped.[/green]")


@cli.command()
@click.option('--check-updates', is_flag=True, help='Check for updates')
@click.pass_context
def version(ctx, check_updates):
    """Show version information."""
    from .display import display_version_info
    display_version_info(check_updates)


@cli.command()
@click.pass_context
def quickstart(ctx):
    """Interactive quickstart guide."""
    from .prompts import run_quickstart_wizard
    run_quickstart_wizard(ctx)


if __name__ == "__main__":
    cli()