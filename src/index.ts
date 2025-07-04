#!/usr/bin/env node

import { startServer } from './server.js';
import { startCLI } from './cli.js';

// Check if running as MCP server
const isMCP = process.argv.includes('--mcp') || process.env.MCP_SERVER === 'true';

if (isMCP) {
  // Start as MCP server
  startServer().catch(console.error);
} else {
  // Start as CLI
  startCLI();
}