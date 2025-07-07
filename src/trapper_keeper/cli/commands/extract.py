"""Extract command for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from ..display import create_file_tree
from ..prompts import prompt_for_categories, Confirm
from ...core.base import EventBus
from ...mcp.tools.extract import ExtractContentTool, ExtractContentRequest
from ...parser import get_parser

console = Console()


@click.command(name='extract')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--sections', '-s', help='Section IDs to extract (comma-separated)')
@click.option('--patterns', '-p', multiple=True, help='Regex patterns to match content')
@click.option('--categories', '-c', multiple=True, help='Categories to extract')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--no-context', is_flag=True, help='Do not preserve surrounding context')
@click.option('--no-references', is_flag=True, help='Do not update references')
@click.option('--dry-run', is_flag=True, help='Preview extraction without changes')
@click.option('--list-sections', '-l', is_flag=True, help='List available sections')
@click.option('--interactive', '-i', is_flag=True, help='Interactive section selection')
@click.pass_context
def extract(ctx, file_path, sections, patterns, categories, output, no_context, 
           no_references, dry_run, list_sections, interactive):
    """Extract specific content sections from documents.
    
    Extract content by section IDs, patterns, or categories. Use --list-sections
    to see available sections first.
    
    Examples:
        trapper-keeper extract doc.md --list-sections
        trapper-keeper extract doc.md --sections "1.2,2.3,4.1"
        trapper-keeper extract doc.md --patterns "TODO|FIXME" --output tasks/
        trapper-keeper extract doc.md --categories "API,Security" -o api-docs/
    """
    config = ctx.obj['config']
    event_bus = EventBus()
    
    # Run the extract operation
    asyncio.run(_extract_content(
        config, event_bus, file_path, sections, patterns, categories,
        output, no_context, no_references, dry_run, list_sections, interactive
    ))


async def _extract_content(
    config, event_bus, file_path, sections, patterns, categories,
    output, no_context, no_references, dry_run, list_sections, interactive
):
    """Execute the extract content operation."""
    file_path = Path(file_path)
    
    # Parse document first
    parser = get_parser(file_path, event_bus)
    if not parser:
        console.print(f"[red]No parser available for {file_path}[/red]")
        return
    
    await parser.initialize()
    content = file_path.read_text(encoding='utf-8')
    document = await parser.parse(content, file_path)
    
    # List sections if requested
    if list_sections:
        _display_sections(document)
        return
    
    # Interactive mode
    if interactive:
        sections = await _interactive_section_selection(document)
        if not sections:
            console.print("[yellow]No sections selected.[/yellow]")
            return
    
    # Parse section IDs if provided as string
    section_ids = None
    if sections:
        if isinstance(sections, str):
            section_ids = [s.strip() for s in sections.split(",")]
        else:
            section_ids = list(sections)
    
    # Convert patterns tuple to list
    pattern_list = list(patterns) if patterns else None
    
    # Convert categories tuple to list or prompt
    category_list = None
    if categories:
        category_list = list(categories)
    elif not section_ids and not pattern_list:
        # No specific extraction criteria, prompt for categories
        if interactive or Confirm.ask("No extraction criteria specified. Select by categories?"):
            category_list = prompt_for_categories()
    
    # Get output directory
    output_dir = Path(output) if output else config.organization.output_dir
    
    # Initialize tool
    tool = ExtractContentTool(config, event_bus)
    await tool.initialize()
    
    # Create request
    request = ExtractContentRequest(
        file_path=str(file_path),
        section_ids=section_ids,
        patterns=pattern_list,
        categories=category_list,
        preserve_context=not no_context,
        update_references=not no_references,
        dry_run=dry_run,
        output_dir=str(output_dir)
    )
    
    # Execute extraction
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Extracting content...", total=None)
        response = await tool.execute(request)
    
    if not response.success:
        console.print(f"[red]Error: {response.errors[0]}[/red]")
        return
    
    # Display results
    if response.extracted_sections:
        console.print(f"\n[green]✓ Extracted {response.total_extracted} sections![/green]\n")
        
        # Show extraction summary
        table = Table(
            title="Extracted Content",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Section", style="white", width=40)
        table.add_column("Category", style="green", width=20)
        table.add_column("Size", style="yellow", width=10)
        if not dry_run:
            table.add_column("Output File", style="blue", width=30)
        
        for section in response.extracted_sections:
            row = [
                section.title[:40] + ("..." if len(section.title) > 40 else ""),
                section.category,
                f"{len(section.content)} chars"
            ]
            if not dry_run and section.output_file:
                row.append(Path(section.output_file).name)
            
            table.add_row(*row)
        
        console.print(table)
        
        if dry_run:
            console.print("\n[dim]This was a dry run. No files were created.[/dim]")
        else:
            # Show output files
            if response.output_files:
                console.print("\n[bold]Created files:[/bold]")
                for file in response.output_files:
                    console.print(f"  • {file}")
            
            if response.references_updated:
                console.print(f"\n[dim]References updated in {file_path}[/dim]")
    else:
        console.print("[yellow]No content matched the extraction criteria.[/yellow]")
    
    # Show processing time
    console.print(f"\n[dim]Processing time: {response.processing_time:.2f}s[/dim]")


def _display_sections(document):
    """Display available sections in the document."""
    console.print(f"\n[bold cyan]Document Sections: {document.id}[/bold cyan]\n")
    
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Level", style="green", width=6)
    table.add_column("Title", style="white", width=50)
    table.add_column("Size", style="yellow", width=10)
    
    for section in document.sections:
        indent = "  " * (section.level - 1)
        table.add_row(
            section.id,
            str(section.level),
            f"{indent}{section.title}",
            f"{len(section.content)} chars"
        )
    
    console.print(table)
    console.print(f"\n[dim]Total sections: {len(document.sections)}[/dim]")


async def _interactive_section_selection(document):
    """Interactive section selection."""
    console.print("\n[bold cyan]Interactive Section Selection[/bold cyan]")
    console.print("[dim]Select sections to extract (enter section IDs)[/dim]\n")
    
    # Display sections
    _display_sections(document)
    
    # Get user selection
    console.print("\n[cyan]Enter section IDs to extract:[/cyan]")
    console.print("[dim]Format: 1.1,2.3,4 or 'all' for all sections[/dim]")
    
    selection = console.input("> ")
    
    if selection.lower() == 'all':
        return [s.id for s in document.sections]
    
    # Parse selection
    selected_ids = []
    for id_str in selection.split(','):
        id_str = id_str.strip()
        if any(s.id == id_str for s in document.sections):
            selected_ids.append(id_str)
        else:
            console.print(f"[yellow]Warning: Section '{id_str}' not found[/yellow]")
    
    return selected_ids