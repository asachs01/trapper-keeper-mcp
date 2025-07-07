"""End-to-end tests for complete workflows."""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
import pytest
import pytest_asyncio

from trapper_keeper.core.orchestrator import TrapperKeeperOrchestrator
from trapper_keeper.core.types import TrapperKeeperConfig


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest_asyncio.fixture
    async def orchestrator(self, temp_dir):
        """Create and initialize orchestrator."""
        config = TrapperKeeperConfig(
            processing={
                "min_importance": 0.3,
                "extract_categories": None,  # All categories
            },
            watching={
                "paths": [temp_dir],
                "patterns": ["*.md", "*.txt"],
                "recursive": True,
                "debounce_seconds": 0.1,
            },
            organization={
                "output_dir": temp_dir / "output",
                "group_by_category": True,
                "create_index": True,
            },
            enable_metrics=True,
            max_concurrent_processing=5,
        )
        
        orchestrator = TrapperKeeperOrchestrator(config)
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_document_processing_workflow(self, orchestrator, temp_dir, create_test_files):
        """Test complete document processing workflow."""
        # Create test documents
        docs = [
            ("project/README.md", """# Project Overview

## Architecture

The system uses a microservices architecture with:
- API Gateway for routing
- Service mesh for inter-service communication
- Event-driven messaging with RabbitMQ

## Database Design

PostgreSQL with the following main tables:
- users: User accounts and profiles
- sessions: Active user sessions
- audit_log: System audit trail

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
"""),
            ("project/docs/api.md", """# API Documentation

## Authentication Endpoints

### POST /auth/login
Login with email and password.

### POST /auth/refresh
Refresh access token.

## User Endpoints

### GET /users
List all users (admin only).

### GET /users/:id
Get user details.
"""),
            ("project/docs/setup.md", """# Setup Guide

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Redis 6+

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure database
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`
"""),
        ]
        
        for path, content in docs:
            file_path = temp_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Start orchestrator
        await orchestrator.start()
        
        # Process all documents
        results = []
        for path, _ in docs:
            result = await orchestrator.process_file(temp_dir / path)
            results.append(result)
        
        # Verify processing results
        assert all(r.success for r in results)
        assert all(len(r.extracted_contents) > 0 for r in results)
        
        # Check extracted categories
        all_categories = set()
        for result in results:
            for content in result.extracted_contents:
                all_categories.add(content.category)
        
        assert "🏗️ Architecture" in all_categories
        assert "🗄️ Database" in all_categories
        assert "🔐 Security" in all_categories
        assert "🌐 API" in all_categories
        assert "📋 Setup" in all_categories
        
        # Get metrics
        metrics = orchestrator.get_metrics()
        assert metrics["documents_processed"] == 3
        assert metrics["total_extracted"] > 0
    
    @pytest.mark.asyncio
    async def test_file_monitoring_workflow(self, orchestrator, temp_dir):
        """Test file monitoring and auto-processing workflow."""
        await orchestrator.start()
        
        # Enable file monitoring
        await orchestrator.start_monitoring()
        
        # Create initial file
        initial_file = temp_dir / "initial.md"
        initial_file.write_text("# Initial Document\n\nSome content")
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify file was detected and processed
        metrics = orchestrator.get_metrics()
        assert metrics["files_monitored"] > 0
        
        # Modify file
        initial_file.write_text("# Updated Document\n\nUpdated content with security notes")
        
        # Wait for change detection
        await asyncio.sleep(0.5)
        
        # Create new file
        new_file = temp_dir / "new_doc.md"
        new_file.write_text("# New Document\n\nDatabase schema information")
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Check updated metrics
        updated_metrics = orchestrator.get_metrics()
        assert updated_metrics["documents_processed"] > metrics["documents_processed"]
    
    @pytest.mark.asyncio
    async def test_content_organization_workflow(self, orchestrator, temp_dir, create_test_files):
        """Test content extraction and organization workflow."""
        # Create diverse content
        files = [
            ("architecture.md", """# System Architecture
            
Microservices with API Gateway pattern.

## Service Communication
Event-driven architecture using message queues.
"""),
            ("security.md", """# Security Implementation

## Authentication
JWT tokens with refresh mechanism.

## Critical Vulnerabilities
URGENT: SQL injection in user input validation!
"""),
            ("database.md", """# Database Schema

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10,2)
);
```
"""),
            ("features.md", """# Feature List

## Completed Features
- User authentication
- Product catalog
- Shopping cart

## Planned Features
- Payment integration
- Order tracking
"""),
        ]
        
        create_test_files(files)
        await orchestrator.start()
        
        # Process all files
        for filename, _ in files:
            await orchestrator.process_file(temp_dir / filename)
        
        # Organize content
        await orchestrator.organize_content()
        
        # Verify organization structure
        output_dir = temp_dir / "output"
        assert output_dir.exists()
        
        # Check category directories
        expected_dirs = ["Architecture", "Security", "Database", "Features"]
        for dir_name in expected_dirs:
            category_dir = output_dir / dir_name
            assert category_dir.exists()
            assert any(category_dir.iterdir())  # Has files
        
        # Check index file
        index_file = output_dir / "index.md"
        assert index_file.exists()
        
        index_content = index_file.read_text()
        assert "# Extracted Content Index" in index_content
        assert all(cat in index_content for cat in expected_dirs)
        
        # Check critical content is highlighted
        security_dir = output_dir / "Security"
        security_files = list(security_dir.glob("*.md"))
        assert len(security_files) > 0
        
        # Critical vulnerability should be extracted
        critical_found = False
        for file in security_files:
            if "SQL injection" in file.read_text():
                critical_found = True
                break
        assert critical_found
    
    @pytest.mark.asyncio
    async def test_large_scale_processing(self, orchestrator, temp_dir):
        """Test processing many documents efficiently."""
        # Create many documents
        num_docs = 50
        for i in range(num_docs):
            doc_path = temp_dir / f"doc_{i}.md"
            doc_path.write_text(f"""# Document {i}

## Section 1
Content about topic {i % 5}.

## Section 2
More content with category {i % 3}.
""")
        
        await orchestrator.start()
        
        # Process all documents concurrently
        start_time = time.time()
        
        tasks = []
        for i in range(num_docs):
            task = orchestrator.process_file(temp_dir / f"doc_{i}.md")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify all processed successfully
        assert all(r.success for r in results)
        
        # Check performance (should process quickly with concurrency)
        assert processing_time < 10  # Should process 50 docs in under 10 seconds
        
        # Check metrics
        metrics = orchestrator.get_metrics()
        assert metrics["documents_processed"] == num_docs
        assert metrics["total_extracted"] > num_docs  # Multiple extractions per doc
        
        # Verify concurrent processing worked
        assert metrics["max_concurrent_processing"] > 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, orchestrator, temp_dir):
        """Test error handling and recovery."""
        await orchestrator.start()
        
        # Create valid document
        valid_doc = temp_dir / "valid.md"
        valid_doc.write_text("# Valid Document\n\nGood content")
        
        # Create invalid document (will cause parsing issues)
        invalid_doc = temp_dir / "invalid.md"
        invalid_doc.write_text("\x00\x01\x02Binary content that's not text")
        
        # Process both
        valid_result = await orchestrator.process_file(valid_doc)
        invalid_result = await orchestrator.process_file(invalid_doc)
        
        # Valid should succeed
        assert valid_result.success
        assert len(valid_result.extracted_contents) > 0
        
        # Invalid should fail gracefully
        assert not invalid_result.success
        assert len(invalid_result.errors) > 0
        
        # System should still be operational
        metrics = orchestrator.get_metrics()
        assert metrics["errors"] > 0
        assert metrics["documents_processed"] >= 1
        
        # Can still process new documents
        new_doc = temp_dir / "new.md"
        new_doc.write_text("# New Document\n\nAfter error")
        
        new_result = await orchestrator.process_file(new_doc)
        assert new_result.success
    
    @pytest.mark.asyncio
    async def test_cross_reference_workflow(self, orchestrator, temp_dir, create_test_files):
        """Test cross-reference detection and organization."""
        # Create interconnected documents
        files = [
            ("index.md", """# Project Index

See [Architecture](architecture.md) for system design.
Check [API Docs](api.md) for endpoints.
Review [Security](security.md) for auth details.
"""),
            ("architecture.md", """# Architecture

As mentioned in [Index](index.md), this describes the system.
API design follows patterns in [API Docs](api.md).
Security considerations in [Security](security.md).
"""),
            ("api.md", """# API Documentation

Refer back to [Architecture](architecture.md) for context.
Authentication described in [Security](security.md).
"""),
            ("security.md", """# Security

Part of system described in [Architecture](architecture.md).
Protects APIs documented in [API Docs](api.md).
"""),
        ]
        
        create_test_files(files)
        await orchestrator.start()
        
        # Process all files
        for filename, _ in files:
            await orchestrator.process_file(temp_dir / filename)
        
        # Generate reference map
        reference_map = await orchestrator.analyze_references()
        
        # Verify cross-references detected
        assert "index.md" in reference_map
        assert "architecture.md" in reference_map["index.md"]["references"]
        assert "api.md" in reference_map["index.md"]["references"]
        assert "security.md" in reference_map["index.md"]["references"]
        
        # Check circular references
        assert "architecture.md" in reference_map["api.md"]["references"]
        assert "api.md" in reference_map["architecture.md"]["references"]
    
    @pytest.mark.asyncio
    async def test_incremental_processing_workflow(self, orchestrator, temp_dir):
        """Test incremental processing of changed content."""
        await orchestrator.start()
        
        # Create and process initial document
        doc_path = temp_dir / "evolving.md"
        doc_path.write_text("""# Initial Version

Basic content here.
""")
        
        result1 = await orchestrator.process_file(doc_path)
        assert result1.success
        initial_count = len(result1.extracted_contents)
        
        # Update document with more content
        doc_path.write_text("""# Updated Version

Basic content here.

## New Section

Additional important content:
- Database schema changes
- API endpoint updates
- Security patch required
""")
        
        # Process updated document
        result2 = await orchestrator.process_file(doc_path)
        assert result2.success
        updated_count = len(result2.extracted_contents)
        
        # Should extract more content
        assert updated_count > initial_count
        
        # Check new categories detected
        categories = {c.category for c in result2.extracted_contents}
        assert len(categories) > 1  # Multiple categories from expanded content
    
    @pytest.mark.asyncio
    async def test_metrics_and_monitoring(self, orchestrator, temp_dir, create_test_files):
        """Test metrics collection and monitoring."""
        # Create test files
        files = [
            ("doc1.md", "# Doc 1\n\nContent"),
            ("doc2.md", "# Doc 2\n\nMore content"),
            ("doc3.md", "# Doc 3\n\nEven more content"),
        ]
        create_test_files(files)
        
        await orchestrator.start()
        
        # Get initial metrics
        initial_metrics = orchestrator.get_metrics()
        
        # Process documents
        for filename, _ in files:
            await orchestrator.process_file(temp_dir / filename)
        
        # Get updated metrics
        final_metrics = orchestrator.get_metrics()
        
        # Verify metrics updated correctly
        assert final_metrics["documents_processed"] == 3
        assert final_metrics["total_extracted"] > 0
        assert final_metrics["processing_time_avg"] > 0
        assert final_metrics["processing_time_total"] > 0
        
        # Check category distribution
        assert "category_distribution" in final_metrics
        assert len(final_metrics["category_distribution"]) > 0
        
        # Check performance metrics
        assert "memory_usage" in final_metrics
        assert "cpu_usage" in final_metrics