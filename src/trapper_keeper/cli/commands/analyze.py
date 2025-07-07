"""Analyze command for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.charts import BarChart
from rich import box
import json

from ..display import display_analysis_results
from ..prompts import Confirm
from ...core.base import EventBus
from ...mcp.tools.analyze import AnalyzeDocumentTool, AnalyzeDocumentRequest

console = Console()


@click.command(name='analyze')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--no-statistics', is_flag=True, help='Skip detailed statistics')
@click.option('--no-growth', is_flag=True, help='Skip growth pattern analysis')
@click.option('--no-recommendations', is_flag=True, help='Skip extraction recommendations')
@click.option('--days', type=int, default=30, help='Days to analyze for growth patterns')
@click.option('--export', '-e', type=click.Path(), help='Export analysis to file')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'html']), default='json', help='Export format')
@click.option('--compare', '-c', type=click.Path(exists=True), help='Compare with another document')
@click.option('--visualize', '-v', is_flag=True, help='Show visualizations')
@click.pass_context
def analyze(ctx, file_path, no_statistics, no_growth, no_recommendations, 
           days, export, format, compare, visualize):
    """Analyze documents for insights and statistics.
    
    Get detailed analysis including statistics, growth patterns, category
    distribution, and extraction recommendations for your documentation.
    
    Examples:
        trapper-keeper analyze README.md
        trapper-keeper analyze docs/manual.md --export analysis.json
        trapper-keeper analyze CLAUDE.md --days 90 --visualize
        trapper-keeper analyze doc1.md --compare doc2.md
    """
    config = ctx.obj['config']
    event_bus = EventBus()
    
    # Run the analyze operation
    asyncio.run(_analyze_document(
        config, event_bus, file_path, no_statistics, no_growth,
        no_recommendations, days, export, format, compare, visualize
    ))


async def _analyze_document(
    config, event_bus, file_path, no_statistics, no_growth,
    no_recommendations, days, export, format, compare, visualize
):
    """Execute the document analysis operation."""
    file_path = Path(file_path)
    
    # Initialize tool
    tool = AnalyzeDocumentTool(config, event_bus)
    await tool.initialize()
    
    # Create request
    request = AnalyzeDocumentRequest(
        file_path=str(file_path),
        include_statistics=not no_statistics,
        include_growth=not no_growth,
        include_recommendations=not no_recommendations,
        days_for_growth=days
    )
    
    # Perform analysis
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Analyzing document...", total=None)
        response = await tool.execute(request)
    
    if not response.success:
        console.print(f"[red]Error: {response.errors[0]}[/red]")
        return
    
    # Display results
    display_analysis_results(response.model_dump())
    
    # Show visualizations if requested
    if visualize and response.statistics:
        _show_visualizations(response)
    
    # Compare with another document if requested
    if compare:
        await _compare_documents(file_path, Path(compare), tool)
    
    # Export results if requested
    if export:
        _export_analysis(response, export, format)
    
    # Show actionable summary
    _show_actionable_summary(response, file_path)


def _show_visualizations(response):
    """Show visual representations of the analysis."""
    console.print("\n[bold cyan]Visualizations[/bold cyan]\n")
    
    # Category distribution chart
    if response.category_distribution:
        console.print("[bold]Category Distribution:[/bold]")
        
        # Create simple bar chart using text
        max_percentage = max(cat.percentage for cat in response.category_distribution)
        
        for cat in response.category_distribution:
            bar_length = int((cat.percentage / max_percentage) * 40)
            bar = "█" * bar_length
            console.print(f"{cat.category:20} {bar} {cat.percentage:.1f}%")
        
        console.print()
    
    # Section depth distribution
    if response.statistics and response.statistics.section_depth_distribution:
        console.print("[bold]Section Depth Distribution:[/bold]")
        
        for level, count in sorted(response.statistics.section_depth_distribution.items()):
            bar = "▪" * count
            console.print(f"Level {level}: {bar} ({count})")
        
        console.print()
    
    # Growth visualization
    if response.growth_patterns:
        growth = response.growth_patterns
        console.print("[bold]Growth Pattern:[/bold]")
        
        # Simple growth indicator
        if growth.growth_rate > 20:
            indicator = "📈 Rapid growth"
            color = "red"
        elif growth.growth_rate > 10:
            indicator = "📊 Steady growth"
            color = "yellow"
        else:
            indicator = "📉 Slow growth"
            color = "green"
        
        console.print(f"[{color}]{indicator}: {growth.growth_rate:.1f}% over {growth.period_days} days[/{color}]")
        console.print(f"Lines added: ~{growth.lines_added}")
        console.print(f"Sections added: ~{growth.sections_added}")
        console.print()


async def _compare_documents(file1: Path, file2: Path, tool):
    """Compare two documents."""
    console.print(f"\n[bold cyan]Comparing Documents[/bold cyan]")
    console.print(f"Document 1: {file1.name}")
    console.print(f"Document 2: {file2.name}\n")
    
    # Analyze second document
    request2 = AnalyzeDocumentRequest(
        file_path=str(file2),
        include_statistics=True,
        include_growth=False,
        include_recommendations=False
    )
    
    with console.status("[cyan]Analyzing comparison document...[/cyan]"):
        response2 = await tool.execute(request2)
    
    if not response2.success:
        console.print(f"[red]Failed to analyze {file2}: {response2.errors[0]}[/red]")
        return
    
    # Compare statistics
    if response2.statistics:
        comparison_data = [
            ("Total Size", f"{response2.statistics.total_size:,} bytes"),
            ("Total Lines", f"{response2.statistics.total_lines:,}"),
            ("Total Sections", str(response2.statistics.total_sections)),
            ("Code Blocks", str(response2.statistics.code_block_count)),
            ("Links", str(response2.statistics.link_count)),
        ]
        
        console.print("[bold]Comparison Statistics:[/bold]")
        for metric, value in comparison_data:
            console.print(f"  {metric}: {value}")
    
    # Compare categories
    if response2.category_distribution:
        console.print("\n[bold]Category Distribution:[/bold]")
        for cat in response2.category_distribution[:5]:
            console.print(f"  {cat.category}: {cat.percentage:.1f}%")


def _export_analysis(response, export_path: str, format: str):
    """Export analysis results to file."""
    export_file = Path(export_path)
    
    if format == 'json':
        export_file.write_text(
            json.dumps(response.model_dump(), indent=2, default=str)
        )
    elif format == 'yaml':
        import yaml
        export_file.write_text(
            yaml.dump(response.model_dump(), default_flow_style=False)
        )
    elif format == 'html':
        # Generate HTML report
        html_content = _generate_html_report(response)
        export_file.write_text(html_content)
    
    console.print(f"\n[green]✓ Analysis exported to {export_path}[/green]")


def _generate_html_report(response):
    """Generate an HTML report from analysis results."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Document Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        .metric {{ background: #f0f0f0; padding: 10px; margin: 5px 0; }}
        .recommendation {{ background: #fffacd; padding: 10px; margin: 5px 0; }}
        .insight {{ background: #e6f3ff; padding: 10px; margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Document Analysis Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Document: {response.file_path}</p>
    
    <h2>Statistics</h2>"""
    
    if response.statistics:
        stats = response.statistics
        html += f"""
    <div class="metric">Total Size: {stats.total_size:,} bytes</div>
    <div class="metric">Total Lines: {stats.total_lines:,}</div>
    <div class="metric">Total Sections: {stats.total_sections}</div>
    <div class="metric">Code Blocks: {stats.code_block_count}</div>
    <div class="metric">Links: {stats.link_count}</div>"""
    
    if response.insights:
        html += "\n    <h2>Insights</h2>"
        for insight in response.insights:
            html += f'\n    <div class="insight">{insight}</div>'
    
    if response.recommendations:
        html += "\n    <h2>Recommendations</h2>"
        for rec in response.recommendations:
            html += f'\n    <div class="recommendation"><strong>{rec.title}</strong>: {rec.reason}</div>'
    
    html += "\n</body>\n</html>"
    return html


def _show_actionable_summary(response, file_path: Path):
    """Show actionable summary and next steps."""
    summary_parts = []
    
    # Determine main action based on analysis
    if response.statistics and response.statistics.total_lines > 1000:
        main_action = "Consider breaking down this large document"
        action_command = f"trapper-keeper organize {file_path} --interactive"
    elif response.recommendations and len(response.recommendations) > 3:
        main_action = "Multiple extraction opportunities found"
        action_command = f"trapper-keeper extract {file_path} --interactive"
    elif response.growth_patterns and response.growth_patterns.growth_rate > 20:
        main_action = "Monitor this rapidly growing document"
        action_command = f"trapper-keeper watch {file_path} --auto-extract"
    else:
        main_action = "Document is well-structured"
        action_command = None
    
    summary_text = f"""[bold]Analysis Summary[/bold]

📊 {main_action}

[bold]Key Findings:[/bold]"""
    
    # Add key findings
    if response.statistics:
        summary_text += f"\n• Document size: {response.statistics.total_lines:,} lines"
    
    if response.category_distribution:
        top_category = response.category_distribution[0]
        summary_text += f"\n• Primary content: {top_category.category} ({top_category.percentage:.1f}%)"
    
    if response.growth_patterns:
        summary_text += f"\n• Growth rate: {response.growth_patterns.growth_rate:.1f}% over {response.growth_patterns.period_days} days"
    
    if action_command:
        summary_text += f"\n\n[bold]Recommended Action:[/bold]\n[cyan]{action_command}[/cyan]"
    
    console.print("\n")
    console.print(Panel(
        summary_text,
        title="Next Steps",
        box=box.DOUBLE,
        border_style="green"
    ))