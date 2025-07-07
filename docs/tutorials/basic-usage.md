# Basic Usage Tutorial

This tutorial walks you through the basic features of Trapper Keeper MCP with practical examples.

## Prerequisites

- Trapper Keeper MCP installed
- A markdown file to practice with (we'll create one if needed)
- Basic command-line knowledge

## Tutorial 1: Your First Document Processing

### Step 1: Create a Sample Document

Let's create a sample CLAUDE.md file to work with:

```bash
cat > CLAUDE.md << 'EOF'
# Project Documentation

## 🏗️ Architecture

The system uses a microservices architecture with the following components:
- API Gateway
- Authentication Service
- User Service
- Payment Service

### Design Patterns
We implement several design patterns:
- Repository Pattern for data access
- Observer Pattern for event handling
- Factory Pattern for object creation

## 🔐 Security

### Authentication
The system uses JWT tokens for authentication:
- Tokens expire after 1 hour
- Refresh tokens last 30 days
- All tokens are signed with RS256

### Authorization
Role-based access control (RBAC):
- Admin: Full system access
- User: Limited to own resources
- Guest: Read-only access

## ✅ Features

### User Management
- User registration with email verification
- Password reset functionality
- Profile management
- Two-factor authentication

### Payment Processing
- Credit card payments via Stripe
- PayPal integration
- Subscription management
- Invoice generation

## 🌐 API

### REST Endpoints
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `GET /api/users/{id}` - Get user details
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token
- `POST /auth/register` - Register new user

## 📋 Setup

### Prerequisites
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Installation Steps
1. Clone the repository
2. Install dependencies: `npm install`
3. Set up environment variables
4. Run migrations: `npm run migrate`
5. Start the server: `npm start`

## 🧪 Testing

### Unit Tests
Run unit tests with coverage:
```bash
npm run test:unit
```

### Integration Tests
Run integration tests:
```bash
npm run test:integration
```

### E2E Tests
Run end-to-end tests:
```bash
npm run test:e2e
```
EOF
```

### Step 2: Analyze the Document

First, let's analyze what we have:

```bash
trapper-keeper analyze CLAUDE.md
```

Expected output:
```
Document Analysis: CLAUDE.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Statistics:
  • Size: 2.1 KB
  • Lines: 89
  • Sections: 6 main, 11 sub-sections
  • Code blocks: 3
  • Links: 0

📂 Category Distribution:
  • 🏗️ Architecture: 24.5% (2 sections)
  • 🔐 Security: 18.2% (2 sections)
  • ✅ Features: 22.1% (2 sections)
  • 🌐 API: 15.8% (2 sections)
  • 📋 Setup: 11.3% (1 section)
  • 🧪 Testing: 8.1% (1 section)

💡 Insights:
  • Well-structured document with clear categories
  • Good balance of technical documentation
  • Consider extracting Architecture and Features sections

📈 Growth: N/A (new file)
```

### Step 3: Process the Document

Now let's process it with default settings:

```bash
trapper-keeper process CLAUDE.md
```

This creates organized output in `./tk-output/`:
```
tk-output/
├── index.md
├── architecture.md
├── security.md
├── features.md
├── api.md
├── setup.md
└── testing.md
```

### Step 4: View the Results

Check the generated index:

```bash
cat tk-output/index.md
```

Look at an extracted category:

```bash
cat tk-output/architecture.md
```

## Tutorial 2: Selective Extraction

### Extract Specific Categories

Extract only security and API documentation:

```bash
trapper-keeper process CLAUDE.md \
  -c "🔐 Security" \
  -c "🌐 API" \
  -o ./security-api-docs
```

### Extract High-Importance Content

Extract only the most important sections:

```bash
trapper-keeper process CLAUDE.md \
  --min-importance 0.8 \
  -o ./important-docs
```

### Extract with Different Formats

Generate JSON output:

```bash
trapper-keeper process CLAUDE.md \
  -f json \
  -o ./json-output
```

Generate YAML output:

```bash
trapper-keeper process CLAUDE.md \
  -f yaml \
  -o ./yaml-output
```

## Tutorial 3: Interactive Organization

### Use Interactive Mode

Run the organize command for guided extraction:

```bash
trapper-keeper organize CLAUDE.md
```

You'll see suggestions like:
```
📋 Extraction Suggestions for CLAUDE.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🏗️ Architecture - Design Patterns
   Importance: ⭐⭐⭐⭐⭐ (0.85)
   Reason: Contains architecture patterns and design decisions
   
   Extract this section? [Y/n]: 
```

### Auto-Approve High Confidence

Automatically approve suggestions above a threshold:

```bash
trapper-keeper organize CLAUDE.md \
  --auto-approve \
  --threshold 0.8
```

## Tutorial 4: Directory Processing

### Process Multiple Files

Create more documentation files:

```bash
# Create additional files
echo "# API Documentation\n\n## Endpoints\n..." > api-docs.md
echo "# Security Guide\n\n## Best Practices\n..." > security.md
echo "# Setup Instructions\n\n## Installation\n..." > setup.md
```

Process all markdown files:

```bash
trapper-keeper process . -p "*.md" -r
```

### Process with Patterns

Process only specific files:

```bash
trapper-keeper process . \
  -p "*-docs.md" \
  -p "security.md" \
  --ignore "test-*"
```

## Tutorial 5: File Watching

### Basic Watch

Watch current directory for changes:

```bash
trapper-keeper watch .
```

Make a change to CLAUDE.md and see it process automatically.

### Watch with Auto-Organization

Watch and automatically organize new content:

```bash
trapper-keeper watch . \
  --auto-organize \
  -o ./auto-organized \
  --min-importance 0.6
```

### Advanced Watch Configuration

Watch specific patterns with custom settings:

```bash
trapper-keeper watch ./docs \
  -p "*.md" \
  -p "*.txt" \
  --ignore "*.draft.*" \
  --ignore ".git/*" \
  --recursive \
  --max-depth 3 \
  --debounce 5
```

## Tutorial 6: Content Validation

### Validate Structure

Check document structure:

```bash
trapper-keeper validate .
```

### Check References

Validate all references and links:

```bash
trapper-keeper validate . \
  --check-references \
  --check-orphans
```

### Fix Issues

Attempt to fix found issues:

```bash
trapper-keeper validate . --fix
```

## Tutorial 7: Using MCP Tools

### Setup MCP Server

Start the MCP server:

```bash
trapper-keeper server
```

### Connect from Claude

In Claude Desktop, you can now use commands like:

```
Can you analyze my CLAUDE.md file and suggest which sections to extract?
```

Claude will use the MCP tools to:
1. Analyze the document
2. Provide suggestions
3. Execute extraction if requested

### Example MCP Workflow

```
User: "Please organize my documentation file at /path/to/CLAUDE.md"

Claude uses:
1. analyze_document - to understand structure
2. organize_documentation - to suggest extractions
3. create_reference - to maintain links
```

## Tutorial 8: Advanced Workflows

### Scheduled Processing

Create a cron job for regular organization:

```bash
# Add to crontab
0 2 * * * /usr/local/bin/trapper-keeper process /docs -o /organized
```

### Git Integration

Process before commits:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Organize documentation
trapper-keeper process CLAUDE.md --min-importance 0.7

# Add organized files
git add tk-output/
```

### CI/CD Integration

Add to GitHub Actions:

```yaml
name: Organize Docs
on:
  push:
    paths:
      - '**.md'

jobs:
  organize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Trapper Keeper
        run: pip install trapper-keeper-mcp
      
      - name: Process Documentation
        run: trapper-keeper process . -r -o ./organized
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: organized-docs
          path: ./organized
```

## Practice Exercises

### Exercise 1: Custom Categories

1. Add a custom category for "🚀 Deployment"
2. Process CLAUDE.md to extract deployment information
3. Verify the extraction worked correctly

### Exercise 2: Importance Tuning

1. Process CLAUDE.md with different importance thresholds (0.3, 0.5, 0.7, 0.9)
2. Compare the outputs
3. Find the optimal threshold for your needs

### Exercise 3: Format Comparison

1. Process CLAUDE.md in all three formats (markdown, json, yaml)
2. Compare file sizes and readability
3. Choose the best format for your use case

### Exercise 4: Batch Processing

1. Create 5 different documentation files
2. Process them all with a single command
3. Generate a unified index

### Exercise 5: Watch and React

1. Set up file watching on a directory
2. Make various changes to files
3. Observe how Trapper Keeper responds
4. Tune the debounce and patterns for optimal performance

## Tips for Success

1. **Start Simple**: Begin with single file processing before moving to directories
2. **Use Dry Run**: Always test with `--dry-run` first
3. **Tune Thresholds**: Adjust importance thresholds based on your content
4. **Organize Incrementally**: Extract one category at a time
5. **Monitor Output**: Check the generated files to ensure quality
6. **Validate Regularly**: Run validation after major changes
7. **Leverage Patterns**: Use file patterns to process specific document types
8. **Automate Workflows**: Set up watching or scheduling for continuous organization

## Next Steps

- [Advanced Workflows](./advanced-workflows.md) - Complex use cases
- [Integration Guide](./integration-guide.md) - Integrate with other tools
- [Custom Categories](./custom-categories.md) - Create your own categories