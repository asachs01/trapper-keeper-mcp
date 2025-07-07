"""Watch command for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box
import humanize

from ..display import display_file_monitor_status
from ...core.base import EventBus
from ...core.types import WatchConfig, EventType
from ...monitoring import DirectoryWatcher
from ...mcp.orchestrator import ProcessingOrchestrator

console = Console()


@click.command(name='watch')
@click.argument('paths', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--patterns', '-p', multiple=True, default=['*.md', '*.txt'], help='File patterns to watch')
@click.option('--recursive/--no-recursive', default=True, help='Watch subdirectories')
@click.option('--process-existing/--no-process-existing', default=True, help='Process existing files')
@click.option('--auto-extract', is_flag=True, help='Automatically extract from modified files')
@click.option('--growth-threshold', type=int, default=20, help='Growth alert threshold (%)')
@click.option('--interval', type=int, default=5, help='Status update interval (seconds)')
@click.option('--output', '-o', type=click.Path(), help='Output directory for extractions')
@click.pass_context
def watch(ctx, paths, patterns, recursive, process_existing, auto_extract, growth_threshold, interval, output):
    """Monitor files and directories for changes.
    
    Watch one or more paths for file modifications, additions, and deletions.
    Can automatically process changed files based on your configuration.
    
    Examples:
        trapper-keeper watch docs/
        trapper-keeper watch README.md CHANGELOG.md --patterns "*.md"
        trapper-keeper watch . --recursive --auto-extract -o output/
        trapper-keeper watch project/ --growth-threshold 10
    """
    config = ctx.obj['config']
    
    # Update config if output specified
    if output:
        config.organization.output_dir = Path(output)
    
    # Convert paths to Path objects
    watch_paths = [Path(p) for p in paths]
    
    # Create watch configuration
    watch_config = WatchConfig(
        paths=watch_paths,
        patterns=list(patterns),
        recursive=recursive
    )
    
    # Run the watch operation
    asyncio.run(_watch_files(
        config, watch_config, process_existing, auto_extract,
        growth_threshold, interval
    ))


async def _watch_files(
    config, watch_config, process_existing, auto_extract,
    growth_threshold, interval
):
    """Execute the file watching operation."""
    event_bus = EventBus()
    
    # Initialize components
    watcher = DirectoryWatcher(watch_config, event_bus, process_existing)
    orchestrator = ProcessingOrchestrator(config, event_bus) if auto_extract else None
    
    # Initialize
    await watcher.initialize()
    if orchestrator:
        await orchestrator.initialize()
    
    # Start components
    await watcher.start()
    if orchestrator:
        await orchestrator.start()
    
    # Subscribe to events
    created_queue = event_bus.subscribe(EventType.FILE_CREATED)
    modified_queue = event_bus.subscribe(EventType.FILE_MODIFIED)
    deleted_queue = event_bus.subscribe(EventType.FILE_DELETED)
    threshold_queue = event_bus.subscribe(EventType.FILE_THRESHOLD_EXCEEDED)
    
    if auto_extract:
        completed_queue = event_bus.subscribe(EventType.PROCESSING_COMPLETED)
        failed_queue = event_bus.subscribe(EventType.PROCESSING_FAILED)
    else:
        completed_queue = None
        failed_queue = None
    
    # Display initial status
    console.print(Panel(
        f"[bold cyan]Monitoring {len(watch_config.paths)} path(s)[/bold cyan]\n"
        f"Patterns: {', '.join(watch_config.patterns)}\n"
        f"Recursive: {watch_config.recursive}\n"
        f"Auto-extract: {auto_extract}\n"
        f"Growth threshold: {growth_threshold}%",
        title="File Monitor Started",
        box=box.DOUBLE
    ))
    
    console.print("[dim]Press Ctrl+C to stop monitoring.[/dim]\n")
    
    # Track file statistics
    file_stats = {}
    events_log = []
    
    try:
        # Create layout for live display
        layout = Layout()
        layout.split_column(
            Layout(name="status", size=3),
            Layout(name="files", size=15),
            Layout(name="events", size=10)
        )
        
        with Live(layout, refresh_per_second=1) as live:
            while True:
                # Update status
                status_text = f"[bold cyan]File Monitor[/bold cyan] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                layout["status"].update(Panel(status_text, box=box.SIMPLE))
                
                # Check for events (non-blocking)
                try:
                    # Check created events
                    while True:
                        event = await asyncio.wait_for(created_queue.get(), timeout=0.01)
                        path = Path(event.data['path'])
                        events_log.append(f"[green]+ Created: {path.name}[/green]")
                        file_stats[str(path)] = {
                            'path': path,
                            'size': path.stat().st_size,
                            'modified': datetime.now(),
                            'growth_rate': 0,
                            'status': '🟢 New'
                        }
                except asyncio.TimeoutError:
                    pass
                
                try:
                    # Check modified events
                    while True:
                        event = await asyncio.wait_for(modified_queue.get(), timeout=0.01)
                        path = Path(event.data['path'])
                        events_log.append(f"[yellow]~ Modified: {path.name}[/yellow]")
                        
                        # Update file stats
                        if str(path) in file_stats:
                            old_size = file_stats[str(path)]['size']
                            new_size = path.stat().st_size
                            growth = ((new_size - old_size) / old_size * 100) if old_size > 0 else 0
                            
                            file_stats[str(path)].update({
                                'size': new_size,
                                'modified': datetime.now(),
                                'growth_rate': growth,
                                'status': '🟡 Modified'
                            })
                            
                            # Check growth threshold
                            if growth > growth_threshold:
                                events_log.append(f"[red]⚠ {path.name} grew by {growth:.1f}%![/red]")
                except asyncio.TimeoutError:
                    pass
                
                try:
                    # Check deleted events
                    while True:
                        event = await asyncio.wait_for(deleted_queue.get(), timeout=0.01)
                        path = event.data['path']
                        events_log.append(f"[red]- Deleted: {Path(path).name}[/red]")
                        file_stats.pop(str(path), None)
                except asyncio.TimeoutError:
                    pass
                
                try:
                    # Check threshold events
                    while True:
                        event = await asyncio.wait_for(threshold_queue.get(), timeout=0.01)
                        path = event.data['path']
                        growth = event.data['growth_percentage']
                        events_log.append(f"[red]🚨 {Path(path).name} exceeded threshold: {growth:.1f}% growth![/red]")
                except asyncio.TimeoutError:
                    pass
                
                # Check processing events if auto-extract enabled
                if auto_extract:
                    try:
                        while True:
                            event = await asyncio.wait_for(completed_queue.get(), timeout=0.01)
                            path = event.data['path']
                            count = event.data['extracted_count']
                            events_log.append(f"[green]✓ Processed {Path(path).name} ({count} items)[/green]")
                    except asyncio.TimeoutError:
                        pass
                    
                    try:
                        while True:
                            event = await asyncio.wait_for(failed_queue.get(), timeout=0.01)
                            path = event.data['path']
                            error = event.data['error']
                            events_log.append(f"[red]✗ Failed: {Path(path).name} - {error}[/red]")
                    except asyncio.TimeoutError:
                        pass
                
                # Update file stats display
                if file_stats:
                    table = Table(
                        title="Monitored Files",
                        box=box.SIMPLE,
                        show_header=True,
                        header_style="bold cyan"
                    )
                    
                    table.add_column("File", style="white", width=30)
                    table.add_column("Size", style="green", width=10)
                    table.add_column("Growth", style="yellow", width=10)
                    table.add_column("Modified", style="blue", width=15)
                    table.add_column("Status", style="magenta", width=12)
                    
                    for stats in sorted(file_stats.values(), key=lambda x: x['modified'], reverse=True)[:10]:
                        growth_str = f"+{stats['growth_rate']:.1f}%" if stats['growth_rate'] > 0 else ""
                        table.add_row(
                            stats['path'].name,
                            humanize.naturalsize(stats['size']),
                            growth_str,
                            humanize.naturaltime(stats['modified']),
                            stats['status']
                        )
                    
                    layout["files"].update(table)
                else:
                    layout["files"].update(Panel("[dim]No files being monitored yet[/dim]", box=box.SIMPLE))
                
                # Update events log
                if events_log:
                    # Keep only last 8 events
                    events_log = events_log[-8:]
                    events_text = "\n".join(events_log)
                    layout["events"].update(Panel(events_text, title="Recent Events", box=box.SIMPLE))
                else:
                    layout["events"].update(Panel("[dim]No events yet[/dim]", title="Recent Events", box=box.SIMPLE))
                
                # Wait for interval
                await asyncio.sleep(interval)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping file monitor...[/yellow]")
    finally:
        # Stop components
        await watcher.stop()
        if orchestrator:
            await orchestrator.stop()
        
        console.print("[green]File monitor stopped.[/green]")
        
        # Show final statistics
        if file_stats:
            console.print(f"\n[bold]Final Statistics:[/bold]")
            console.print(f"Files monitored: {len(file_stats)}")
            console.print(f"Total events: {len(events_log)}")
            
            # Find file with highest growth
            if any(stats['growth_rate'] > 0 for stats in file_stats.values()):
                max_growth = max(file_stats.values(), key=lambda x: x['growth_rate'])
                console.print(f"Highest growth: {max_growth['path'].name} ({max_growth['growth_rate']:.1f}%)")