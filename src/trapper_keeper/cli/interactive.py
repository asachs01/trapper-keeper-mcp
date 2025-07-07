"""Interactive mode for Trapper Keeper CLI."""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
import click

from .display import (
    display_categories, display_extraction_suggestions,
    display_file_monitor_status, display_validation_results,
    display_analysis_results, display_config, create_file_tree,
    display_extraction_results
)
from .prompts import (
    prompt_for_file, prompt_for_categories, prompt_for_output_dir,
    prompt_for_extraction_options, prompt_for_monitor_options
)
from ..core.config import get_config_manager
from ..mcp.orchestrator import ProcessingOrchestrator
from ..core.base import EventBus

console = Console()


class InteractiveSession:
    """Interactive session manager for Trapper Keeper."""
    
    def __init__(self, ctx: click.Context):
        self.ctx = ctx
        self.config = ctx.obj['config']
        self.config_manager = ctx.obj['config_manager']
        self.event_bus = EventBus()
        self.orchestrator = None
        
    async def start(self):
        """Start the interactive session."""
        # Welcome message
        self._display_welcome()
        
        # Initialize orchestrator
        self.orchestrator = ProcessingOrchestrator(self.config, self.event_bus)
        await self.orchestrator.initialize()
        await self.orchestrator.start()
        
        try:
            while True:
                # Display main menu
                choice = self._display_main_menu()
                
                if choice == 'q':
                    break
                    
                # Handle menu choice
                await self._handle_menu_choice(choice)
                
                # Ask if user wants to continue
                if not Confirm.ask("\n[cyan]Continue with another operation?[/cyan]"):
                    break
                    
        finally:
            if self.orchestrator:
                await self.orchestrator.stop()
            
        console.print("\n[bold green]Thank you for using Trapper Keeper![/bold green]")
    
    def _display_welcome(self):
        """Display welcome message."""
        welcome_text = """[bold cyan]Welcome to Trapper Keeper Interactive Mode![/bold cyan]
        
Trapper Keeper helps you organize and extract content from large documentation files.
You can organize documents, extract specific sections, monitor file changes, and more.

[dim]Use the menu below to select an operation.[/dim]"""
        
        console.print(Panel(welcome_text, box=box.DOUBLE_EDGE, title="🗂️ Trapper Keeper"))
        console.print()
    
    def _display_main_menu(self) -> str:
        """Display main menu and get user choice."""
        menu_items = [
            ("1", "📋 Organize Documentation", "Extract and organize content from files"),
            ("2", "🔍 Extract Content", "Extract specific sections from documents"),
            ("3", "👁️ Monitor Files", "Watch files for changes and growth"),
            ("4", "✅ Validate Structure", "Check document structure and references"),
            ("5", "📊 Analyze Documents", "Get insights and statistics about documents"),
            ("6", "⚙️ Configure Settings", "Manage Trapper Keeper configuration"),
            ("7", "📚 View Categories", "List available extraction categories"),
            ("8", "🚀 Quick Start", "Run the quick start wizard"),
            ("q", "❌ Quit", "Exit interactive mode")
        ]
        
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Key", style="cyan", width=4)
        table.add_column("Option", style="white", width=25)
        table.add_column("Description", style="dim", width=45)
        
        for key, option, desc in menu_items:
            table.add_row(key, option, desc)
        
        console.print(Panel(table, title="Main Menu", box=box.ROUNDED))
        
        return Prompt.ask(
            "\n[bold cyan]Select an option[/bold cyan]",
            choices=[item[0] for item in menu_items],
            default="1"
        )
    
    async def _handle_menu_choice(self, choice: str):
        """Handle main menu choice."""
        if choice == "1":
            await self._organize_documentation()
        elif choice == "2":
            await self._extract_content()
        elif choice == "3":
            await self._monitor_files()
        elif choice == "4":
            await self._validate_structure()
        elif choice == "5":
            await self._analyze_documents()
        elif choice == "6":
            await self._configure_settings()
        elif choice == "7":
            display_categories()
        elif choice == "8":
            await self._quick_start()
    
    async def _organize_documentation(self):
        """Interactive organize documentation flow."""
        console.print("\n[bold cyan]Organize Documentation[/bold cyan]")
        console.print("[dim]This will analyze your documentation and suggest content to extract.[/dim]\n")
        
        # Get file path
        file_path = prompt_for_file("Enter the path to your documentation file")
        if not file_path:
            return
        
        # Analyze file
        with console.status("[cyan]Analyzing document...[/cyan]"):
            from ..mcp.tools.organize import OrganizeDocumentationTool, OrganizeDocumentationRequest
            
            tool = OrganizeDocumentationTool(self.config, self.event_bus)
            await tool.initialize()
            
            # First, do a dry run to get suggestions
            request = OrganizeDocumentationRequest(
                file_path=str(file_path),
                dry_run=True
            )
            
            response = await tool.execute(request)
        
        if not response.success:
            console.print(f"[red]Error: {response.errors[0]}[/red]")
            return
        
        # Display suggestions
        if response.suggestions:
            display_extraction_suggestions(
                [s.model_dump() for s in response.suggestions],
                str(file_path)
            )
            
            # Ask if user wants to proceed
            if Confirm.ask("\n[cyan]Proceed with extraction?[/cyan]"):
                # Get extraction options
                options = prompt_for_extraction_options()
                
                # Get output directory
                output_dir = prompt_for_output_dir()
                
                # Perform actual extraction
                with console.status("[cyan]Extracting content...[/cyan]"):
                    request = OrganizeDocumentationRequest(
                        file_path=str(file_path),
                        dry_run=False,
                        output_dir=str(output_dir),
                        categories=options.get('categories'),
                        min_importance=options.get('min_importance', 0.5),
                        create_references=options.get('create_references', True)
                    )
                    
                    response = await tool.execute(request)
                
                if response.success:
                    console.print(f"\n[green]✓ Successfully extracted {response.extracted_count} items![/green]")
                    console.print(f"Output files: {', '.join(response.output_files)}")
                else:
                    console.print(f"[red]Extraction failed: {response.errors[0]}[/red]")
        else:
            console.print("[yellow]No extraction suggestions found.[/yellow]")
    
    async def _extract_content(self):
        """Interactive extract content flow."""
        console.print("\n[bold cyan]Extract Content[/bold cyan]")
        console.print("[dim]Extract specific sections from your documents.[/dim]\n")
        
        # Get file path
        file_path = prompt_for_file("Enter the document path")
        if not file_path:
            return
        
        # Parse document to show sections
        with console.status("[cyan]Loading document...[/cyan]"):
            from ..parser import get_parser
            
            parser = get_parser(file_path, self.event_bus)
            if not parser:
                console.print("[red]No parser available for this file type.[/red]")
                return
                
            await parser.initialize()
            content = file_path.read_text(encoding='utf-8')
            document = await parser.parse(content, file_path)
        
        # Display document structure
        console.print(f"\n[cyan]Document: {document.id}[/cyan]")
        console.print(f"Sections: {len(document.sections)}\n")
        
        # Show section tree
        tree = create_file_tree(file_path.parent, [file_path.name])
        console.print(tree)
        
        # Get extraction method
        method = Prompt.ask(
            "\nExtraction method",
            choices=["sections", "patterns", "categories", "all"],
            default="categories"
        )
        
        section_ids = None
        patterns = None
        categories = None
        
        if method == "sections":
            # Show sections and let user select
            table = Table(title="Document Sections", box=box.SIMPLE)
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Level", style="green")
            
            for section in document.sections[:20]:  # Show first 20
                table.add_row(section.id, section.title[:50], str(section.level))
            
            console.print(table)
            
            ids_input = Prompt.ask("Enter section IDs (comma-separated)")
            section_ids = [id.strip() for id in ids_input.split(",")]
            
        elif method == "patterns":
            pattern_input = Prompt.ask("Enter regex patterns (comma-separated)")
            patterns = [p.strip() for p in pattern_input.split(",")]
            
        elif method == "categories":
            categories = prompt_for_categories()
        
        # Get output directory
        output_dir = prompt_for_output_dir()
        
        # Perform extraction
        with console.status("[cyan]Extracting content...[/cyan]"):
            from ..mcp.tools.extract import ExtractContentTool, ExtractContentRequest
            
            tool = ExtractContentTool(self.config, self.event_bus)
            await tool.initialize()
            
            request = ExtractContentRequest(
                file_path=str(file_path),
                section_ids=section_ids,
                patterns=patterns,
                categories=categories,
                output_dir=str(output_dir),
                preserve_context=Confirm.ask("Preserve surrounding context?", default=True),
                update_references=Confirm.ask("Update references in source?", default=True),
                dry_run=False
            )
            
            response = await tool.execute(request)
        
        if response.success:
            console.print(f"\n[green]✓ Extracted {response.total_extracted} sections![/green]")
            
            # Show extraction results
            table = Table(title="Extracted Content", box=box.SIMPLE)
            table.add_column("Section", style="cyan")
            table.add_column("Category", style="green")
            table.add_column("Output File", style="blue")
            
            for section in response.extracted_sections[:10]:  # Show first 10
                table.add_row(
                    section.title[:40],
                    section.category,
                    Path(section.output_file).name if section.output_file else "N/A"
                )
            
            console.print(table)
        else:
            console.print(f"[red]Extraction failed: {response.errors[0]}[/red]")
    
    async def _monitor_files(self):
        """Interactive file monitoring flow."""
        console.print("\n[bold cyan]Monitor Files[/bold cyan]")
        console.print("[dim]Watch files for changes and growth patterns.[/dim]\n")
        
        # Get monitoring options
        options = prompt_for_monitor_options()
        
        if not options:
            return
        
        # Create monitoring task
        console.print("\n[cyan]Starting file monitor...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop monitoring.[/dim]\n")
        
        from ..monitoring import DirectoryWatcher
        from ..core.types import WatchConfig
        
        watch_config = WatchConfig(
            paths=options['paths'],
            patterns=options['patterns'],
            recursive=options['recursive']
        )
        
        watcher = DirectoryWatcher(watch_config, self.event_bus, process_existing=False)
        await watcher.initialize()
        await watcher.start()
        
        try:
            # Monitor loop
            while True:
                # Get current status
                monitored_files = []
                for path in options['paths']:
                    if path.is_file():
                        stat = path.stat()
                        monitored_files.append({
                            'path': path,
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'growth_rate': 0  # Would calculate from history
                        })
                
                # Display status
                console.clear()
                display_file_monitor_status(monitored_files)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping monitor...[/yellow]")
        finally:
            await watcher.stop()
            console.print("[green]Monitor stopped.[/green]")
    
    async def _validate_structure(self):
        """Interactive structure validation flow."""
        console.print("\n[bold cyan]Validate Structure[/bold cyan]")
        console.print("[dim]Check document structure and find broken references.[/dim]\n")
        
        # Get root directory
        root_dir = Prompt.ask(
            "Enter root directory to validate",
            default=str(Path.cwd())
        )
        
        root_path = Path(root_dir)
        if not root_path.exists():
            console.print("[red]Directory not found.[/red]")
            return
        
        # Get validation options
        check_references = Confirm.ask("Check for broken references?", default=True)
        check_orphans = Confirm.ask("Find orphaned documents?", default=True)
        check_structure = Confirm.ask("Verify directory structure?", default=True)
        
        # Perform validation
        with console.status("[cyan]Validating structure...[/cyan]"):
            from ..mcp.tools.validate import ValidateStructureTool, ValidateStructureRequest
            
            tool = ValidateStructureTool(self.config, self.event_bus)
            await tool.initialize()
            
            request = ValidateStructureRequest(
                root_dir=str(root_path),
                check_references=check_references,
                check_orphans=check_orphans,
                check_structure=check_structure
            )
            
            response = await tool.execute(request)
        
        if response.success:
            # Display results
            display_validation_results(response.model_dump())
            
            # Offer to fix issues
            if response.issues and Confirm.ask("\n[cyan]Would you like to fix some issues?[/cyan]"):
                console.print("[yellow]Issue fixing not yet implemented.[/yellow]")
        else:
            console.print(f"[red]Validation failed: {response.errors[0]}[/red]")
    
    async def _analyze_documents(self):
        """Interactive document analysis flow."""
        console.print("\n[bold cyan]Analyze Documents[/bold cyan]")
        console.print("[dim]Get insights and statistics about your documents.[/dim]\n")
        
        # Get file path
        file_path = prompt_for_file("Enter document to analyze")
        if not file_path:
            return
        
        # Get analysis options
        include_statistics = Confirm.ask("Include detailed statistics?", default=True)
        include_growth = Confirm.ask("Analyze growth patterns?", default=True)
        include_recommendations = Confirm.ask("Generate recommendations?", default=True)
        
        # Perform analysis
        with console.status("[cyan]Analyzing document...[/cyan]"):
            from ..mcp.tools.analyze import AnalyzeDocumentTool, AnalyzeDocumentRequest
            
            tool = AnalyzeDocumentTool(self.config, self.event_bus)
            await tool.initialize()
            
            request = AnalyzeDocumentRequest(
                file_path=str(file_path),
                include_statistics=include_statistics,
                include_growth=include_growth,
                include_recommendations=include_recommendations
            )
            
            response = await tool.execute(request)
        
        if response.success:
            # Display results
            display_analysis_results(response.model_dump())
            
            # Export option
            if Confirm.ask("\n[cyan]Export analysis report?[/cyan]"):
                export_path = Prompt.ask(
                    "Export path",
                    default=str(file_path.with_suffix('.analysis.json'))
                )
                
                import json
                Path(export_path).write_text(
                    json.dumps(response.model_dump(), indent=2, default=str)
                )
                console.print(f"[green]✓ Report exported to {export_path}[/green]")
        else:
            console.print(f"[red]Analysis failed: {response.errors[0]}[/red]")
    
    async def _configure_settings(self):
        """Interactive configuration management."""
        console.print("\n[bold cyan]Configure Settings[/bold cyan]")
        console.print("[dim]Manage Trapper Keeper configuration.[/dim]\n")
        
        # Display current config
        display_config(self.config.model_dump())
        
        # Configuration menu
        config_menu = [
            ("1", "Edit processing settings"),
            ("2", "Edit organization settings"),
            ("3", "Edit monitoring settings"),
            ("4", "Save configuration to file"),
            ("5", "Load configuration from file"),
            ("6", "Reset to defaults"),
            ("b", "Back to main menu")
        ]
        
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Key", style="cyan", width=4)
        table.add_column("Option", style="white", width=40)
        
        for key, option in config_menu:
            table.add_row(key, option)
        
        console.print(table)
        
        choice = Prompt.ask(
            "\nSelect option",
            choices=[item[0] for item in config_menu],
            default="b"
        )
        
        if choice == "1":
            # Edit processing settings
            self.config.processing.min_importance = IntPrompt.ask(
                "Minimum importance (0-100)",
                default=int(self.config.processing.min_importance * 100)
            ) / 100.0
            
            if Confirm.ask("Update extraction categories?"):
                self.config.processing.extract_categories = prompt_for_categories()
            
        elif choice == "2":
            # Edit organization settings
            output_dir = prompt_for_output_dir()
            self.config.organization.output_dir = output_dir
            
            self.config.organization.group_by_category = Confirm.ask(
                "Group by category?",
                default=self.config.organization.group_by_category
            )
            
        elif choice == "3":
            # Edit monitoring settings
            patterns = Prompt.ask(
                "File patterns (comma-separated)",
                default=",".join(self.config.watching.patterns)
            )
            self.config.watching.patterns = [p.strip() for p in patterns.split(",")]
            
        elif choice == "4":
            # Save configuration
            save_path = Prompt.ask("Save path", default="trapper-keeper.yaml")
            self.config_manager.save(Path(save_path))
            console.print(f"[green]✓ Configuration saved to {save_path}[/green]")
            
        elif choice == "5":
            # Load configuration
            load_path = prompt_for_file("Enter configuration file path")
            if load_path and load_path.exists():
                self.config = self.config_manager.load(load_path)
                self.ctx.obj['config'] = self.config
                console.print("[green]✓ Configuration loaded![/green]")
                
        elif choice == "6":
            # Reset to defaults
            if Confirm.ask("[red]Reset all settings to defaults?[/red]"):
                from ..core.types import TrapperKeeperConfig
                self.config = TrapperKeeperConfig()
                self.ctx.obj['config'] = self.config
                console.print("[green]✓ Configuration reset to defaults.[/green]")
    
    async def _quick_start(self):
        """Run quick start wizard."""
        from .prompts import run_quickstart_wizard
        run_quickstart_wizard(self.ctx)


def start_interactive_mode(ctx: click.Context):
    """Start the interactive mode."""
    session = InteractiveSession(ctx)
    asyncio.run(session.start())