#!/usr/bin/env python3
"""
Example script showing how to use Trapper Keeper MCP Python API
to organize documentation files programmatically.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# Add trapper_keeper to path if running from examples directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from trapper_keeper.organizer import DocumentOrganizer
from trapper_keeper.core.config import Config
from trapper_keeper.core.types import ProcessingOptions, ExtractionCategory
from trapper_keeper.monitoring import FileMonitor
from trapper_keeper.utils.metrics import MetricsCollector


async def process_single_file(file_path: str):
    """Process a single documentation file."""
    
    print(f"Processing {file_path}...")
    
    # Load configuration
    config = Config.load()
    
    # Create organizer
    organizer = DocumentOrganizer(config)
    
    # Set processing options
    options = ProcessingOptions(
        categories=[
            ExtractionCategory.ARCHITECTURE,
            ExtractionCategory.SECURITY,
            ExtractionCategory.API
        ],
        min_importance=0.6,
        create_references=True,
        dry_run=False
    )
    
    # Process document
    result = await organizer.process_document(
        file_path=Path(file_path),
        options=options
    )
    
    # Display results
    if result.success:
        print(f"✅ Successfully processed {file_path}")
        print(f"   Extracted {len(result.extracted_content)} sections")
        print(f"   Categories: {result.categories_found}")
        print(f"   Output files: {result.output_files}")
    else:
        print(f"❌ Failed to process {file_path}")
        for error in result.errors:
            print(f"   Error: {error}")


async def process_directory(directory_path: str, patterns: List[str]):
    """Process all matching files in a directory."""
    
    print(f"Processing directory {directory_path}...")
    
    # Load configuration
    config = Config.load()
    
    # Create organizer
    organizer = DocumentOrganizer(config)
    
    # Process directory
    results = await organizer.process_directory(
        directory_path=Path(directory_path),
        patterns=patterns,
        recursive=True,
        parallel=True
    )
    
    # Summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    print(f"\nProcessing Summary:")
    print(f"  Total files: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    
    # Generate index
    if successful > 0:
        index_content = organizer.generate_index(results)
        index_path = Path(config.output.default_dir) / "index.md"
        index_path.write_text(index_content)
        print(f"  Index created: {index_path}")


async def watch_directory(directory_path: str):
    """Watch a directory for changes and process automatically."""
    
    print(f"Watching {directory_path} for changes...")
    print("Press Ctrl+C to stop")
    
    # Load configuration
    config = Config.load()
    
    # Create organizer and monitor
    organizer = DocumentOrganizer(config)
    monitor = FileMonitor(config)
    
    # Define callback for file changes
    async def on_file_change(event):
        file_path = Path(event.data["file_path"])
        print(f"\n📝 File changed: {file_path}")
        
        # Process the changed file
        result = await organizer.process_document(file_path)
        
        if result.success:
            print(f"✅ Processed successfully")
        else:
            print(f"❌ Processing failed")
    
    # Subscribe to file events
    monitor.event_bus.subscribe("file.modified")(on_file_change)
    monitor.event_bus.subscribe("file.created")(on_file_change)
    
    # Start monitoring
    await monitor.watch_directory(
        path=Path(directory_path),
        patterns=["*.md", "*.txt"],
        recursive=True
    )
    
    # Keep running
    try:
        await monitor.start()
        await asyncio.Event().wait()  # Run forever
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        await monitor.stop()


async def analyze_documentation(file_path: str):
    """Analyze a documentation file and show insights."""
    
    print(f"Analyzing {file_path}...")
    
    # Load configuration
    config = Config.load()
    
    # Create organizer
    organizer = DocumentOrganizer(config)
    
    # Analyze document
    analysis = await organizer.analyze_document(Path(file_path))
    
    # Display analysis
    print(f"\n📊 Document Analysis: {file_path}")
    print(f"{'=' * 50}")
    
    print(f"\n📈 Statistics:")
    print(f"  Size: {analysis.statistics.total_size:,} bytes")
    print(f"  Lines: {analysis.statistics.total_lines}")
    print(f"  Sections: {analysis.statistics.total_sections}")
    print(f"  Code blocks: {analysis.statistics.code_block_count}")
    print(f"  Links: {analysis.statistics.link_count}")
    
    print(f"\n📂 Category Distribution:")
    for cat in analysis.category_distribution:
        bar = "█" * int(cat.percentage / 2)
        print(f"  {cat.category}: {bar} {cat.percentage:.1f}%")
    
    print(f"\n💡 Insights:")
    for insight in analysis.insights:
        print(f"  • {insight}")
    
    print(f"\n📝 Recommendations:")
    for rec in analysis.recommendations:
        print(f"  • {rec}")


async def custom_workflow():
    """Example of a custom documentation workflow."""
    
    print("Running custom documentation workflow...")
    
    # Load configuration with custom settings
    config = Config.load()
    config.extraction.min_importance = 0.7
    config.output.group_by = "category"
    
    # Add custom category
    config.add_category(
        name="🎯 Custom Logic",
        keywords=["custom", "business", "logic", "rule"],
        patterns=[".*business logic.*", ".*custom rule.*"],
        importance_boost=0.3
    )
    
    # Create components
    organizer = DocumentOrganizer(config)
    metrics = MetricsCollector()
    
    # Process multiple files with metrics
    files = [
        "CLAUDE.md",
        "README.md",
        "docs/architecture.md"
    ]
    
    for file_path in files:
        if not Path(file_path).exists():
            continue
            
        # Start metrics
        start_time = asyncio.get_event_loop().time()
        
        # Process file
        result = await organizer.process_document(Path(file_path))
        
        # Record metrics
        duration = asyncio.get_event_loop().time() - start_time
        metrics.record_processing(
            duration=duration,
            status="success" if result.success else "failure"
        )
        
        # Custom post-processing
        if result.success:
            for content in result.extracted_content:
                if content.category == "🎯 Custom Logic":
                    print(f"Found custom logic: {content.title}")
                    # Additional processing...
    
    # Display metrics
    print(f"\n📊 Processing Metrics:")
    print(f"  Files processed: {metrics.files_processed_total}")
    print(f"  Average duration: {metrics.average_duration:.2f}s")


async def main():
    """Main function with example usage."""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python organize_documentation.py process <file>")
        print("  python organize_documentation.py process-dir <directory> [patterns...]")
        print("  python organize_documentation.py watch <directory>")
        print("  python organize_documentation.py analyze <file>")
        print("  python organize_documentation.py custom")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "process" and len(sys.argv) >= 3:
        await process_single_file(sys.argv[2])
        
    elif command == "process-dir" and len(sys.argv) >= 3:
        directory = sys.argv[2]
        patterns = sys.argv[3:] if len(sys.argv) > 3 else ["*.md", "*.txt"]
        await process_directory(directory, patterns)
        
    elif command == "watch" and len(sys.argv) >= 3:
        await watch_directory(sys.argv[2])
        
    elif command == "analyze" and len(sys.argv) >= 3:
        await analyze_documentation(sys.argv[2])
        
    elif command == "custom":
        await custom_workflow()
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())