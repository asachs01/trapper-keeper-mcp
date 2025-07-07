"""Validate command for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

from ..display import display_validation_results, create_file_tree
from ..prompts import Confirm
from ...core.base import EventBus
from ...mcp.tools.validate import ValidateStructureTool, ValidateStructureRequest

console = Console()


@click.command(name='validate')
@click.argument('root_dir', type=click.Path(exists=True), default='.')
@click.option('--source-files', '-s', multiple=True, help='Specific files to validate')
@click.option('--skip-references', is_flag=True, help='Skip reference validation')
@click.option('--skip-orphans', is_flag=True, help='Skip orphan file detection')
@click.option('--skip-structure', is_flag=True, help='Skip directory structure validation')
@click.option('--patterns', '-p', multiple=True, default=['*.md', '*.txt'], help='File patterns to validate')
@click.option('--fix', is_flag=True, help='Attempt to fix issues (interactive)')
@click.option('--report', '-r', type=click.Path(), help='Save validation report to file')
@click.option('--tree', is_flag=True, help='Show directory tree before validation')
@click.pass_context
def validate(ctx, root_dir, source_files, skip_references, skip_orphans, 
            skip_structure, patterns, fix, report, tree):
    """Validate documentation structure and references.
    
    Check for broken references, orphaned files, and structural issues
    in your documentation. Use --fix to interactively resolve issues.
    
    Examples:
        trapper-keeper validate
        trapper-keeper validate docs/ --patterns "*.md"
        trapper-keeper validate . --skip-orphans --fix
        trapper-keeper validate docs/ --report validation-report.json
    """
    config = ctx.obj['config']
    event_bus = EventBus()
    
    # Run the validate operation
    asyncio.run(_validate_structure(
        config, event_bus, root_dir, source_files, skip_references,
        skip_orphans, skip_structure, patterns, fix, report, tree
    ))


async def _validate_structure(
    config, event_bus, root_dir, source_files, skip_references,
    skip_orphans, skip_structure, patterns, fix, report, tree
):
    """Execute the structure validation operation."""
    root_path = Path(root_dir)
    
    # Show directory tree if requested
    if tree:
        console.print("\n[bold cyan]Directory Structure:[/bold cyan]")
        tree_display = create_file_tree(root_path, patterns)
        console.print(tree_display)
        console.print()
    
    # Initialize tool
    tool = ValidateStructureTool(config, event_bus)
    await tool.initialize()
    
    # Create request
    request = ValidateStructureRequest(
        root_dir=str(root_path),
        source_files=list(source_files) if source_files else None,
        check_references=not skip_references,
        check_orphans=not skip_orphans,
        check_structure=not skip_structure,
        patterns=list(patterns)
    )
    
    # Perform validation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Validating structure...", total=None)
        response = await tool.execute(request)
    
    if not response.success:
        console.print(f"[red]Error: {response.errors[0]}[/red]")
        return
    
    # Display results
    display_validation_results(response.model_dump())
    
    # Save report if requested
    if report:
        import json
        report_path = Path(report)
        report_path.write_text(
            json.dumps(response.model_dump(), indent=2, default=str)
        )
        console.print(f"\n[green]✓ Report saved to {report}[/green]")
    
    # Fix issues if requested
    if fix and response.issues:
        await _fix_issues(response, root_path, config, event_bus)
    
    # Show summary
    _show_validation_summary(response)


async def _fix_issues(response, root_path, config, event_bus):
    """Interactively fix validation issues."""
    console.print("\n[bold cyan]Fix Validation Issues[/bold cyan]")
    
    # Group issues by type
    issues_by_type = {}
    for issue in response.issues:
        issues_by_type.setdefault(issue.type, []).append(issue)
    
    # Handle each issue type
    for issue_type, issues in issues_by_type.items():
        console.print(f"\n[bold]{issue_type.replace('_', ' ').title()}[/bold]")
        console.print(f"Found {len(issues)} issue(s)")
        
        if issue_type == "broken_reference":
            await _fix_broken_references(issues, root_path)
        elif issue_type == "orphaned_file":
            await _fix_orphaned_files(issues, root_path)
        elif issue_type == "missing_category":
            await _fix_missing_categories(issues, root_path)
        else:
            console.print(f"[yellow]No automatic fix available for {issue_type}[/yellow]")


async def _fix_broken_references(issues, root_path):
    """Fix broken references."""
    console.print("\n[cyan]Broken References:[/cyan]")
    
    for issue in issues:
        console.print(f"\nFile: {issue.file_path}")
        console.print(f"Broken reference: {issue.details.get('reference', 'unknown')}")
        
        # Offer fix options
        fix_option = click.prompt(
            "Fix option",
            type=click.Choice(['skip', 'remove', 'update', 'create']),
            default='skip'
        )
        
        if fix_option == 'skip':
            continue
        elif fix_option == 'remove':
            console.print("[yellow]Reference removal not implemented yet[/yellow]")
        elif fix_option == 'update':
            new_ref = click.prompt("New reference path")
            console.print(f"[yellow]Would update reference to: {new_ref}[/yellow]")
        elif fix_option == 'create':
            console.print("[yellow]File creation not implemented yet[/yellow]")


async def _fix_orphaned_files(issues, root_path):
    """Handle orphaned files."""
    console.print("\n[cyan]Orphaned Files:[/cyan]")
    
    for issue in issues:
        file_path = Path(issue.file_path)
        console.print(f"\nOrphaned file: {file_path}")
        
        action = click.prompt(
            "Action",
            type=click.Choice(['skip', 'delete', 'create-reference', 'move']),
            default='skip'
        )
        
        if action == 'skip':
            continue
        elif action == 'delete':
            if Confirm.ask(f"[red]Delete {file_path.name}?[/red]"):
                console.print("[yellow]File deletion not implemented yet[/yellow]")
        elif action == 'create-reference':
            ref_file = click.prompt("Add reference in file")
            console.print(f"[yellow]Would add reference in: {ref_file}[/yellow]")
        elif action == 'move':
            new_location = click.prompt("Move to")
            console.print(f"[yellow]Would move to: {new_location}[/yellow]")


async def _fix_missing_categories(issues, root_path):
    """Fix missing category information."""
    console.print("\n[cyan]Missing Categories:[/cyan]")
    
    from ..prompts import prompt_for_categories
    
    for issue in issues:
        file_path = Path(issue.file_path)
        console.print(f"\nFile without category: {file_path}")
        
        if Confirm.ask("Add category information?"):
            categories = prompt_for_categories()
            console.print(f"[yellow]Would add categories: {', '.join(categories)}[/yellow]")


def _show_validation_summary(response):
    """Show validation summary with recommendations."""
    # Calculate health score
    total_files = response.total_files_checked
    issues_count = len(response.issues)
    
    if total_files > 0:
        health_score = ((total_files - response.files_with_issues) / total_files) * 100
    else:
        health_score = 100
    
    # Determine health status
    if health_score >= 90:
        health_status = "[green]Excellent[/green]"
        health_emoji = "🟢"
    elif health_score >= 70:
        health_status = "[yellow]Good[/yellow]"
        health_emoji = "🟡"
    elif health_score >= 50:
        health_status = "[orange]Fair[/orange]"
        health_emoji = "🟠"
    else:
        health_status = "[red]Poor[/red]"
        health_emoji = "🔴"
    
    # Create summary panel
    summary_text = f"""[bold]Documentation Health Score: {health_score:.1f}% {health_emoji}[/bold]
Status: {health_status}

[bold]Summary:[/bold]
• Files checked: {total_files}
• Valid files: {response.valid_files}
• Issues found: {issues_count}
• Orphaned files: {len(response.orphaned_files)}
• Broken references: {len(response.broken_references)}

[bold]Recommendations:[/bold]"""
    
    # Add recommendations based on issues
    recommendations = []
    
    if response.broken_references:
        recommendations.append("• Fix broken references to improve navigation")
    
    if response.orphaned_files:
        recommendations.append("• Review orphaned files and create references or remove them")
    
    if any(i.type == "missing_category" for i in response.issues):
        recommendations.append("• Add category metadata to improve organization")
    
    if not recommendations:
        recommendations.append("• Your documentation structure looks good!")
    
    summary_text += "\n" + "\n".join(recommendations)
    
    console.print("\n")
    console.print(Panel(
        summary_text,
        title="Validation Summary",
        box=box.DOUBLE,
        border_style="green" if health_score >= 70 else "yellow"
    ))