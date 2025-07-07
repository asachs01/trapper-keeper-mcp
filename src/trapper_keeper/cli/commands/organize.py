"""Organize command for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..display import display_extraction_suggestions, display_extraction_results
from ..prompts import prompt_for_categories, prompt_for_output_dir, Confirm
from ...core.base import EventBus
from ...mcp.tools.organize import OrganizeDocumentationTool, OrganizeDocumentationRequest

console = Console()


@click.command(name='organize')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Preview without making changes')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--categories', '-c', multiple=True, help='Specific categories to extract')
@click.option('--min-importance', type=float, default=0.5, help='Minimum importance threshold (0-1)')
@click.option('--no-references', is_flag=True, help='Do not create reference links')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with suggestions')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def organize(ctx, file_path, dry_run, output, categories, min_importance, no_references, interactive, force):
    """Organize and extract content from documentation files.
    
    This command analyzes your documentation and suggests content to extract
    based on categories and importance. Use --dry-run to preview suggestions
    without making changes.
    
    Examples:
        trapper-keeper organize README.md
        trapper-keeper organize docs/CLAUDE.md --categories "Setup,API" -o output/
        trapper-keeper organize manual.md --dry-run --min-importance 0.7
    """
    config = ctx.obj['config']
    event_bus = EventBus()
    
    # Run the organize operation
    asyncio.run(_organize_documentation(
        config, event_bus, file_path, dry_run, output, categories,
        min_importance, no_references, interactive, force
    ))


async def _organize_documentation(
    config, event_bus, file_path, dry_run, output, categories,
    min_importance, no_references, interactive, force
):
    """Execute the organize documentation operation."""
    file_path = Path(file_path)
    
    # Initialize tool
    tool = OrganizeDocumentationTool(config, event_bus)
    await tool.initialize()
    
    # First, always do a dry run to get suggestions
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Analyzing document...", total=None)
        
        request = OrganizeDocumentationRequest(
            file_path=str(file_path),
            dry_run=True,
            categories=list(categories) if categories else None,
            min_importance=min_importance
        )
        
        response = await tool.execute(request)
    
    if not response.success:
        console.print(f"[red]Error: {response.errors[0]}[/red]")
        return
    
    # Display suggestions
    if response.suggestions:
        console.print(f"\n[bold cyan]Found {len(response.suggestions)} extraction suggestions:[/bold cyan]\n")
        
        if interactive or dry_run:
            # Show detailed suggestions
            display_extraction_suggestions(
                [s.model_dump() for s in response.suggestions],
                str(file_path)
            )
        else:
            # Show summary
            console.print(f"Categories found: {', '.join(response.categories_found)}")
            console.print(f"Sections to extract: {len(response.suggestions)}")
    else:
        console.print("[yellow]No content found matching the criteria.[/yellow]")
        return
    
    # If dry run, stop here
    if dry_run:
        console.print("\n[dim]This was a dry run. No changes were made.[/dim]")
        return
    
    # Ask for confirmation if not forced
    if not force and not Confirm.ask("\n[cyan]Proceed with extraction?[/cyan]"):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return
    
    # Get output directory
    if not output:
        if interactive:
            output = prompt_for_output_dir()
        else:
            output = config.organization.output_dir
    
    output_path = Path(output)
    
    # Perform actual extraction
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Extracting content...", total=len(response.suggestions))
        
        request = OrganizeDocumentationRequest(
            file_path=str(file_path),
            dry_run=False,
            output_dir=str(output_path),
            categories=list(categories) if categories else response.categories_found,
            min_importance=min_importance,
            create_references=not no_references
        )
        
        response = await tool.execute(request)
        progress.update(task, completed=len(response.suggestions))
    
    if response.success:
        console.print(f"\n[green]✓ Successfully organized {response.extracted_count} sections![/green]")
        
        if response.output_files:
            console.print("\n[bold]Output files:[/bold]")
            for file in response.output_files:
                console.print(f"  • {file}")
        
        if not no_references:
            console.print(f"\n[dim]Reference links have been added to {file_path}[/dim]")
    else:
        console.print(f"[red]Organization failed: {response.errors[0]}[/red]")
    
    # Show processing time
    console.print(f"\n[dim]Processing time: {response.processing_time:.2f}s[/dim]")