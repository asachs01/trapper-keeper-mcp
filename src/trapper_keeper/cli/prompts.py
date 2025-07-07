"""User prompts and input utilities for Trapper Keeper CLI."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich import box
import click

from ..core.types import ExtractionCategory

console = Console()


def prompt_for_file(prompt_text: str, must_exist: bool = True) -> Optional[Path]:
    """Prompt user for a file path with validation."""
    while True:
        path_str = Prompt.ask(prompt_text)
        
        if not path_str:
            return None
            
        # Expand user home directory
        if path_str.startswith("~"):
            path_str = str(Path(path_str).expanduser())
            
        path = Path(path_str)
        
        if must_exist and not path.exists():
            console.print(f"[red]File not found: {path}[/red]")
            if not Confirm.ask("Try again?"):
                return None
            continue
            
        return path


def prompt_for_directory(prompt_text: str, create_if_missing: bool = True) -> Optional[Path]:
    """Prompt user for a directory path with validation."""
    while True:
        path_str = Prompt.ask(prompt_text)
        
        if not path_str:
            return None
            
        # Expand user home directory
        if path_str.startswith("~"):
            path_str = str(Path(path_str).expanduser())
            
        path = Path(path_str)
        
        if not path.exists():
            if create_if_missing:
                if Confirm.ask(f"[yellow]Directory doesn't exist. Create {path}?[/yellow]"):
                    path.mkdir(parents=True, exist_ok=True)
                    console.print(f"[green]✓ Created directory: {path}[/green]")
                else:
                    continue
            else:
                console.print(f"[red]Directory not found: {path}[/red]")
                if not Confirm.ask("Try again?"):
                    return None
                continue
                
        elif not path.is_dir():
            console.print(f"[red]Not a directory: {path}[/red]")
            if not Confirm.ask("Try again?"):
                return None
            continue
            
        return path


def prompt_for_categories() -> List[str]:
    """Prompt user to select extraction categories."""
    # Display available categories
    table = Table(title="Available Categories", box=box.SIMPLE)
    table.add_column("Number", style="cyan", width=6)
    table.add_column("Category", style="white", width=25)
    table.add_column("Icon", style="green", width=4)
    
    categories = list(ExtractionCategory)
    for i, cat in enumerate(categories, 1):
        icon = cat.value.split()[0]
        name = cat.value.split(maxsplit=1)[1] if ' ' in cat.value else cat.value
        table.add_row(str(i), name, icon)
    
    console.print(table)
    
    # Get user selection
    console.print("\n[cyan]Select categories:[/cyan]")
    console.print("[dim]Enter numbers separated by commas (e.g., 1,3,5) or 'all' for all categories[/dim]")
    
    selection = Prompt.ask("Categories", default="all")
    
    if selection.lower() == "all":
        return [cat.value for cat in categories]
    
    selected_categories = []
    try:
        indices = [int(x.strip()) - 1 for x in selection.split(",")]
        for idx in indices:
            if 0 <= idx < len(categories):
                selected_categories.append(categories[idx].value)
    except (ValueError, IndexError):
        console.print("[red]Invalid selection. Using all categories.[/red]")
        return [cat.value for cat in categories]
    
    return selected_categories


def prompt_for_output_dir() -> Path:
    """Prompt user for output directory."""
    default_output = Path.cwd() / "trapper-keeper-output"
    
    output_str = Prompt.ask(
        "Output directory",
        default=str(default_output)
    )
    
    output_path = Path(output_str)
    if output_str.startswith("~"):
        output_path = Path(output_str).expanduser()
    
    if not output_path.exists():
        if Confirm.ask(f"[yellow]Create directory {output_path}?[/yellow]"):
            output_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓ Created output directory[/green]")
    
    return output_path


def prompt_for_extraction_options() -> Dict[str, Any]:
    """Prompt user for extraction options."""
    options = {}
    
    # Category selection
    if Confirm.ask("Filter by categories?", default=True):
        options['categories'] = prompt_for_categories()
    
    # Importance threshold
    importance = IntPrompt.ask(
        "Minimum importance threshold (0-100)",
        default=50
    )
    options['min_importance'] = importance / 100.0
    
    # Reference creation
    options['create_references'] = Confirm.ask(
        "Create reference links in source document?",
        default=True
    )
    
    return options


def prompt_for_monitor_options() -> Optional[Dict[str, Any]]:
    """Prompt user for file monitoring options."""
    options = {}
    
    # Get paths to monitor
    console.print("[cyan]Enter paths to monitor (one per line, empty line to finish):[/cyan]")
    paths = []
    while True:
        path_str = Prompt.ask("Path", default="")
        if not path_str:
            break
            
        path = Path(path_str)
        if path_str.startswith("~"):
            path = Path(path_str).expanduser()
            
        if not path.exists():
            console.print(f"[red]Path not found: {path}[/red]")
            continue
            
        paths.append(path)
        console.print(f"[green]✓ Added: {path}[/green]")
    
    if not paths:
        console.print("[yellow]No paths selected.[/yellow]")
        return None
    
    options['paths'] = paths
    
    # Get file patterns
    patterns_str = Prompt.ask(
        "File patterns to watch (comma-separated)",
        default="*.md,*.txt"
    )
    options['patterns'] = [p.strip() for p in patterns_str.split(",")]
    
    # Recursive option
    options['recursive'] = Confirm.ask("Watch subdirectories?", default=True)
    
    # Growth threshold
    threshold = IntPrompt.ask(
        "Growth alert threshold (% increase)",
        default=20
    )
    options['growth_threshold'] = threshold
    
    return options


def run_quickstart_wizard(ctx: click.Context):
    """Run the quickstart wizard for new users."""
    console.print(Panel(
        "[bold cyan]Welcome to Trapper Keeper Quick Start![/bold cyan]\n\n"
        "This wizard will help you get started with organizing your documentation.",
        box=box.DOUBLE_EDGE
    ))
    
    # Step 1: Select a document
    console.print("\n[bold]Step 1: Select a Document[/bold]")
    console.print("[dim]Choose a documentation file to analyze (e.g., README.md, CLAUDE.md)[/dim]")
    
    file_path = prompt_for_file("Document path")
    if not file_path:
        console.print("[red]No file selected. Exiting wizard.[/red]")
        return
    
    # Step 2: Choose operation
    console.print("\n[bold]Step 2: Choose Operation[/bold]")
    operation = Prompt.ask(
        "What would you like to do?",
        choices=["analyze", "organize", "extract"],
        default="analyze"
    )
    
    # Step 3: Configure operation
    console.print(f"\n[bold]Step 3: Configure {operation.title()}[/bold]")
    
    if operation == "analyze":
        # Run analysis
        console.print("[cyan]Analyzing your document...[/cyan]")
        from ..mcp.tools.analyze import AnalyzeDocumentTool, AnalyzeDocumentRequest
        
        async def run_analysis():
            tool = AnalyzeDocumentTool(ctx.obj['config'])
            await tool.initialize()
            
            request = AnalyzeDocumentRequest(
                file_path=str(file_path),
                include_statistics=True,
                include_recommendations=True
            )
            
            response = await tool.execute(request)
            
            if response.success:
                console.print("\n[green]✓ Analysis complete![/green]")
                
                # Show key insights
                if response.insights:
                    console.print("\n[bold]Key Insights:[/bold]")
                    for insight in response.insights[:3]:
                        console.print(f"• {insight}")
                
                # Show recommendations
                if response.recommendations:
                    console.print("\n[bold]Recommendations:[/bold]")
                    for i, rec in enumerate(response.recommendations[:3], 1):
                        console.print(f"{i}. {rec.title} - {rec.reason}")
        
        import asyncio
        asyncio.run(run_analysis())
        
    elif operation == "organize":
        # Get output directory
        output_dir = prompt_for_output_dir()
        
        # Run organization
        console.print("[cyan]Organizing your document...[/cyan]")
        from ..mcp.tools.organize import OrganizeDocumentationTool, OrganizeDocumentationRequest
        
        async def run_organize():
            tool = OrganizeDocumentationTool(ctx.obj['config'])
            await tool.initialize()
            
            request = OrganizeDocumentationRequest(
                file_path=str(file_path),
                output_dir=str(output_dir),
                dry_run=False
            )
            
            response = await tool.execute(request)
            
            if response.success:
                console.print(f"\n[green]✓ Extracted {response.extracted_count} sections![/green]")
                console.print(f"Output files: {', '.join(response.output_files)}")
        
        import asyncio
        asyncio.run(run_organize())
        
    elif operation == "extract":
        # Get categories
        categories = prompt_for_categories()
        output_dir = prompt_for_output_dir()
        
        # Run extraction
        console.print("[cyan]Extracting content...[/cyan]")
        from ..mcp.tools.extract import ExtractContentTool, ExtractContentRequest
        
        async def run_extract():
            tool = ExtractContentTool(ctx.obj['config'])
            await tool.initialize()
            
            request = ExtractContentRequest(
                file_path=str(file_path),
                categories=categories,
                output_dir=str(output_dir),
                dry_run=False
            )
            
            response = await tool.execute(request)
            
            if response.success:
                console.print(f"\n[green]✓ Extracted {response.total_extracted} sections![/green]")
        
        import asyncio
        asyncio.run(run_extract())
    
    # Step 4: Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("• Use 'trapper-keeper monitor' to watch for file changes")
    console.print("• Use 'trapper-keeper validate' to check document structure")
    console.print("• Use 'trapper-keeper config' to customize settings")
    console.print("\n[dim]Run 'trapper-keeper --help' for all available commands.[/dim]")
    
    console.print("\n[bold green]Quick start complete! Happy organizing! 🎉[/bold green]")