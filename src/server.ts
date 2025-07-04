import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { join } from 'path';
import { organizeDocumentation } from './tools/organize.js';
import { extractContent } from './tools/extract.js';
import { createReference } from './tools/reference.js';
import { validateStructure } from './tools/validate.js';
import { suggestImprovements } from './tools/suggest.js';
import { trackCriticalDocs } from './tools/critical.js';
import { loadConfig } from './utils/config.js';

const server = new Server(
  {
    name: 'trapper-keeper-mcp',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool parameter schemas
const OrganizeSchema = z.object({
  projectPath: z.string().describe('Path to the project to organize'),
  claudeMdPath: z.string().optional().describe('Path to CLAUDE.md file (defaults to project root)'),
  dryRun: z.boolean().optional().describe('Preview changes without applying them')
});

const ExtractSchema = z.object({
  projectPath: z.string().describe('Path to the project'),
  claudeMdPath: z.string().describe('Path to CLAUDE.md file'),
  contentType: z.string().optional().describe('Type of content to extract (e.g., "architecture", "database")'),
  startLine: z.number().optional().describe('Starting line number for extraction'),
  endLine: z.number().optional().describe('Ending line number for extraction')
});

const CreateReferenceSchema = z.object({
  projectPath: z.string().describe('Path to the project'),
  documentPath: z.string().describe('Path to the document to reference'),
  title: z.string().describe('Title for the reference'),
  category: z.string().optional().describe('Category for the document'),
  critical: z.boolean().optional().describe('Mark as critical documentation')
});

const ValidateSchema = z.object({
  projectPath: z.string().describe('Path to the project to validate')
});

const SuggestSchema = z.object({
  projectPath: z.string().describe('Path to the project'),
  claudeMdPath: z.string().optional().describe('Path to CLAUDE.md file')
});

const TrackCriticalSchema = z.object({
  projectPath: z.string().describe('Path to the project'),
  claudeMdPath: z.string().optional().describe('Path to CLAUDE.md file')
});

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'organize_documentation',
        description: 'Automatically reorganize project documentation using the reference pattern',
        inputSchema: OrganizeSchema
      },
      {
        name: 'extract_content',
        description: 'Extract content from CLAUDE.md based on type and size thresholds',
        inputSchema: ExtractSchema
      },
      {
        name: 'create_reference',
        description: 'Create a properly formatted reference link with emoji categorization',
        inputSchema: CreateReferenceSchema
      },
      {
        name: 'validate_structure',
        description: 'Validate documentation structure and check for broken references',
        inputSchema: ValidateSchema
      },
      {
        name: 'suggest_improvements',
        description: 'Analyze documentation and suggest organizational improvements',
        inputSchema: SuggestSchema
      },
      {
        name: 'track_critical_docs',
        description: 'Maintain critical documentation pattern and prevent context loss',
        inputSchema: TrackCriticalSchema
      }
    ]
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'organize_documentation': {
        const params = OrganizeSchema.parse(args);
        const config = await loadConfig(params.projectPath);
        const result = await organizeDocumentation(
          params.projectPath,
          params.claudeMdPath || join(params.projectPath, 'CLAUDE.md'),
          config,
          params.dryRun
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      }

      case 'extract_content': {
        const params = ExtractSchema.parse(args);
        const config = await loadConfig(params.projectPath);
        const result = await extractContent(
          params.claudeMdPath,
          params.projectPath,
          config,
          {
            contentType: params.contentType,
            startLine: params.startLine,
            endLine: params.endLine
          }
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      }

      case 'create_reference': {
        const params = CreateReferenceSchema.parse(args);
        const reference = await createReference(
          params.documentPath,
          params.title,
          params.projectPath,
          params.category,
          params.critical
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(reference, null, 2)
            }
          ]
        };
      }

      case 'validate_structure': {
        const params = ValidateSchema.parse(args);
        const config = await loadConfig(params.projectPath);
        const result = await validateStructure(params.projectPath, config);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      }

      case 'suggest_improvements': {
        const params = SuggestSchema.parse(args);
        const config = await loadConfig(params.projectPath);
        const suggestions = await suggestImprovements(
          params.projectPath,
          params.claudeMdPath || join(params.projectPath, 'CLAUDE.md'),
          config
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(suggestions, null, 2)
            }
          ]
        };
      }

      case 'track_critical_docs': {
        const params = TrackCriticalSchema.parse(args);
        const config = await loadConfig(params.projectPath);
        const result = await trackCriticalDocs(
          params.projectPath,
          params.claudeMdPath || join(params.projectPath, 'CLAUDE.md'),
          config
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      }

      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`
        );
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Invalid parameters: ${error.errors.map(e => e.message).join(', ')}`
      );
    }
    throw error;
  }
});

export async function startServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Trapper Keeper MCP server started');
}