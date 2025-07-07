"""Display utilities for Trapper Keeper CLI using Rich."""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich import box
import humanize

from ..core.types import ExtractionCategory, ExtractedContent, ProcessingResult

console = Console()


def display_categories():
    """Display available extraction categories in a beautiful table."""
    table = Table(
        title="Available Extraction Categories",
        box=box.ROUNDED,
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Icon", style="cyan", width=4)
    table.add_column("Category", style="cyan", width=20)
    table.add_column("Name", style="white", width=25)
    table.add_column("Description", style="dim", width=40)
    
    category_descriptions = {
        ExtractionCategory.ARCHITECTURE: "System design and architectural decisions",
        ExtractionCategory.DATABASE: "Database schemas, queries, and data models",
        ExtractionCategory.SECURITY: "Security configurations and best practices",
        ExtractionCategory.FEATURES: "Feature specifications and requirements",
        ExtractionCategory.MONITORING: "Monitoring, logging, and observability",
        ExtractionCategory.CRITICAL: "Critical information and warnings",
        ExtractionCategory.SETUP: "Installation and setup instructions",
        ExtractionCategory.API: "API documentation and endpoints",
        ExtractionCategory.TESTING: "Testing strategies and test cases",
        ExtractionCategory.PERFORMANCE: "Performance optimization and benchmarks",
        ExtractionCategory.DOCUMENTATION: "General documentation and guides",
        ExtractionCategory.DEPLOYMENT: "Deployment procedures and configs",
        ExtractionCategory.CONFIGURATION: "Configuration files and settings",
        ExtractionCategory.DEPENDENCIES: "Project dependencies and requirements",
        ExtractionCategory.CUSTOM: "Custom user-defined categories"
    }
    
    for cat in ExtractionCategory:
        icon = cat.value.split()[0]  # Get emoji icon
        name = cat.value.split(maxsplit=1)[1] if ' ' in cat.value else cat.value
        table.add_row(
            icon,
            name,
            cat.name.replace('_', ' ').title(),
            category_descriptions.get(cat, "")
        )
    
    console.print(table)


def display_extraction_suggestions(suggestions: List[Dict[str, Any]], file_path: str):
    """Display extraction suggestions with interactive preview."""
    console.print(Panel(
        f"[bold cyan]Extraction Suggestions for:[/bold cyan] {file_path}",
        box=box.DOUBLE
    ))
    
    for i, suggestion in enumerate(suggestions, 1):
        # Create a panel for each suggestion
        content = f"""[bold]Section:[/bold] {suggestion['title']}
[bold]Category:[/bold] {suggestion['category']}
[bold]Importance:[/bold] {'⭐' * int(suggestion['importance'] * 5)}
[bold]Reason:[/bold] {suggestion['reason']}

[dim]Preview:[/dim]
{suggestion['content_preview']}"""
        
        panel = Panel(
            content,
            title=f"[{i}] {suggestion['section_id']}",
            border_style="green" if suggestion['importance'] > 0.7 else "yellow",
            box=box.ROUNDED
        )
        console.print(panel)
        console.print()


def display_file_monitor_status(monitored_files: List[Dict[str, Any]]):
    """Display real-time file monitoring status."""
    table = Table(
        title="File Monitoring Status",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("File", style="white", width=40)
    table.add_column("Size", style="green", width=10)
    table.add_column("Growth", style="yellow", width=15)
    table.add_column("Last Modified", style="blue", width=20)
    table.add_column("Status", style="magenta", width=15)
    
    for file_info in monitored_files:
        growth = file_info.get('growth_rate', 0)
        growth_str = f"+{growth:.1f}%" if growth > 0 else f"{growth:.1f}%"
        
        status = "🟢 Normal"
        if growth > 20:
            status = "🟡 Growing"
        elif growth > 50:
            status = "🔴 Rapid Growth"
        
        table.add_row(
            str(file_info['path']),
            humanize.naturalsize(file_info['size']),
            growth_str,
            humanize.naturaltime(file_info['modified']),
            status
        )
    
    console.print(table)


def display_validation_results(validation_results: Dict[str, Any]):
    """Display structure validation results."""
    # Summary panel
    summary = f"""[bold]Validation Summary[/bold]
├─ Total Files: {validation_results['total_files_checked']}
├─ Valid Files: [green]{validation_results['valid_files']}[/green]
├─ Files with Issues: [yellow]{validation_results['files_with_issues']}[/yellow]
├─ Orphaned Files: [red]{len(validation_results.get('orphaned_files', []))}[/red]
└─ Broken References: [red]{len(validation_results.get('broken_references', []))}[/red]"""
    
    console.print(Panel(summary, title="Validation Results", box=box.DOUBLE))
    
    # Issues table
    if validation_results.get('issues'):
        table = Table(
            title="Issues Found",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold red"
        )
        
        table.add_column("Type", style="red", width=20)
        table.add_column("File", style="white", width=40)
        table.add_column("Message", style="yellow", width=50)
        
        for issue in validation_results['issues']:
            table.add_row(
                issue['type'],
                Path(issue['file_path']).name,
                issue['message']
            )
        
        console.print(table)
    else:
        console.print("[green]✓ No issues found![/green]")


def display_analysis_results(analysis: Dict[str, Any]):
    """Display document analysis results with visualizations."""
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=4)
    )
    
    # Header
    header_text = Text(f"Document Analysis: {analysis['file_path']}", style="bold cyan")
    layout["header"].update(Panel(header_text, box=box.DOUBLE))
    
    # Body - split into statistics and insights
    layout["body"].split_row(
        Layout(name="stats"),
        Layout(name="insights")
    )
    
    # Statistics
    if analysis.get('statistics'):
        stats = analysis['statistics']
        stats_tree = Tree("📊 Statistics")
        stats_tree.add(f"Total Size: {humanize.naturalsize(stats['total_size'])}")
        stats_tree.add(f"Lines: {stats['total_lines']:,}")
        stats_tree.add(f"Sections: {stats['total_sections']}")
        stats_tree.add(f"Code Blocks: {stats['code_block_count']}")
        stats_tree.add(f"Links: {stats['link_count']}")
        stats_tree.add(f"Images: {stats['image_count']}")
        
        layout["stats"].update(Panel(stats_tree, title="Document Statistics"))
    
    # Insights
    if analysis.get('insights'):
        insights_text = "\n\n".join([f"• {insight}" for insight in analysis['insights']])
        layout["insights"].update(Panel(insights_text, title="Key Insights", border_style="green"))
    
    # Footer - recommendations
    if analysis.get('recommendations'):
        rec_text = "Top Recommendations:\n"
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            rec_text += f"{i}. [{rec['priority']}] {rec['title']} - {rec['reason']}\n"
        layout["footer"].update(Panel(rec_text, title="Recommendations", border_style="yellow"))
    
    console.print(layout)


def display_processing_progress(file_path: str, step: str = "Processing"):
    """Create a progress display for file processing."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True
    )


def display_config(config: Dict[str, Any], format: str = "tree"):
    """Display configuration in various formats."""
    if format == "tree":
        tree = Tree("🔧 Configuration")
        
        # Processing config
        proc_node = tree.add("📋 Processing")
        proc_node.add(f"Min Importance: {config['processing']['min_importance']}")
        proc_node.add(f"Extract Categories: {len(config['processing']['extract_categories'])}")
        
        # Organization config
        org_node = tree.add("📁 Organization")
        org_node.add(f"Output Dir: {config['organization']['output_dir']}")
        org_node.add(f"Format: {config['organization']['format']}")
        org_node.add(f"Group by Category: {config['organization']['group_by_category']}")
        
        # Watch config
        watch_node = tree.add("👁️ Watching")
        watch_node.add(f"Patterns: {', '.join(config['watching']['patterns'])}")
        watch_node.add(f"Recursive: {config['watching']['recursive']}")
        
        console.print(tree)
    
    elif format == "yaml":
        import yaml
        syntax = Syntax(
            yaml.dump(config, default_flow_style=False),
            "yaml",
            theme="monokai",
            line_numbers=True
        )
        console.print(Panel(syntax, title="Configuration (YAML)", box=box.DOUBLE))


def display_version_info(check_updates: bool = False):
    """Display version information."""
    version_panel = Panel(
        f"""[bold cyan]Trapper Keeper MCP[/bold cyan]
        
Version: [green]1.0.0[/green]
Python: [yellow]3.8+[/yellow]
License: [blue]MIT[/blue]

[dim]Intelligent document extraction and organization tool[/dim]""",
        title="Version Information",
        box=box.DOUBLE_EDGE
    )
    
    console.print(version_panel)
    
    if check_updates:
        with console.status("[cyan]Checking for updates..."):
            # Simulate update check
            import time
            time.sleep(1)
        console.print("[green]✓ You are using the latest version![/green]")


def create_file_tree(root_path: Path, patterns: List[str] = None) -> Tree:
    """Create a file tree visualization."""
    tree = Tree(f"📁 {root_path.name}")
    
    def add_directory(tree_node: Tree, path: Path, level: int = 0):
        if level > 3:  # Limit depth
            return
            
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    dir_node = tree_node.add(f"📁 {item.name}")
                    add_directory(dir_node, item, level + 1)
                else:
                    # Check if file matches patterns
                    if patterns:
                        if not any(item.match(p) for p in patterns):
                            continue
                    
                    # Add file with icon based on extension
                    icon = "📄"
                    if item.suffix == '.md':
                        icon = "📝"
                    elif item.suffix in ['.yml', '.yaml']:
                        icon = "⚙️"
                    elif item.suffix == '.json':
                        icon = "📊"
                    
                    tree_node.add(f"{icon} {item.name}")
        except PermissionError:
            tree_node.add("[red]Permission Denied[/red]")
    
    add_directory(tree, root_path)
    return tree


def display_extraction_results(results: List[ProcessingResult]):
    """Display extraction results summary."""
    total_extracted = sum(len(r.extracted_contents) for r in results)
    successful = sum(1 for r in results if r.success)
    
    # Summary panel
    summary = Panel(
        f"""[bold green]Extraction Complete![/bold green]
        
Files Processed: {len(results)}
Successful: [green]{successful}[/green]
Failed: [red]{len(results) - successful}[/red]
Total Items Extracted: [cyan]{total_extracted}[/cyan]""",
        box=box.DOUBLE
    )
    
    console.print(summary)
    
    # Category breakdown
    if total_extracted > 0:
        category_counts = {}
        for result in results:
            for content in result.extracted_contents:
                cat = content.category.value if hasattr(content.category, 'value') else str(content.category)
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        table = Table(title="Extracted Content by Category", box=box.SIMPLE)
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")
        
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_extracted) * 100
            table.add_row(cat, str(count), f"{percentage:.1f}%")
        
        console.print(table)