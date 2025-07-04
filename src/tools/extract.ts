import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { existsSync } from 'fs';
import { TrapperKeeperConfig } from '../types/index.js';
import { detectCategory, getCategoryEmoji } from '../utils/categories.js';

interface ExtractOptions {
  contentType?: string;
  startLine?: number;
  endLine?: number;
}

interface ExtractResult {
  success: boolean;
  extractedFile?: string;
  reference?: string;
  error?: string;
}

export async function extractContent(
  claudeMdPath: string,
  projectPath: string,
  config: TrapperKeeperConfig,
  options: ExtractOptions = {}
): Promise<ExtractResult> {
  try {
    const content = await readFile(claudeMdPath, 'utf-8');
    const lines = content.split('\n');
    
    // Determine extraction range
    let startLine = options.startLine || 0;
    let endLine = options.endLine || lines.length - 1;
    
    // If contentType is specified, try to find relevant section
    if (options.contentType && !options.startLine) {
      const sectionBounds = findSectionByType(lines, options.contentType);
      if (sectionBounds) {
        startLine = sectionBounds.start;
        endLine = sectionBounds.end;
      }
    }
    
    // Extract content
    const extractedLines = lines.slice(startLine, endLine + 1);
    const extractedContent = extractedLines.join('\n');
    
    // Determine category and filename
    const category = options.contentType || detectCategory(extractedContent);
    const emoji = getCategoryEmoji(category);
    const fileName = generateFileName(extractedLines, category);
    
    // Create file path
    const docPath = join(projectPath, config.organization.docsFolder, fileName);
    const docsDir = dirname(docPath);
    
    // Create directory if needed
    if (!existsSync(docsDir)) {
      await mkdir(docsDir, { recursive: true });
    }
    
    // Write extracted content
    await writeFile(docPath, extractedContent);
    
    // Remove extracted content from original file
    lines.splice(startLine, endLine - startLine + 1);
    
    // Add reference in place of extracted content
    const relativePath = docPath.replace(projectPath, '');
    const reference = `- **${emoji} ${fileName.replace('.md', '')}**: \`${relativePath}\``;
    lines.splice(startLine, 0, reference);
    
    // Write updated CLAUDE.md
    await writeFile(claudeMdPath, lines.join('\n'));
    
    return {
      success: true,
      extractedFile: docPath,
      reference
    };
  } catch (error) {
    return {
      success: false,
      error: `Extraction failed: ${error}`
    };
  }
}

function findSectionByType(lines: string[], contentType: string): { start: number; end: number } | null {
  const typeKeywords = getTypeKeywords(contentType);
  let bestMatch: { start: number; end: number; score: number } | null = null;
  
  let currentSection: { start: number; title: string } | null = null;
  
  lines.forEach((line, index) => {
    if (/^##(?!#)\s+/.test(line)) {
      // Process previous section if exists
      if (currentSection) {
        const sectionContent = lines.slice(currentSection.start, index).join('\n').toLowerCase();
        let score = 0;
        
        for (const keyword of typeKeywords) {
          if (sectionContent.includes(keyword)) {
            score++;
          }
        }
        
        if (score > 0 && (!bestMatch || score > bestMatch.score)) {
          bestMatch = {
            start: currentSection.start,
            end: index - 1,
            score
          };
        }
      }
      
      currentSection = {
        start: index,
        title: line.replace(/^##\s+/, '').trim()
      };
    }
  });
  
  // Check last section
  if (currentSection) {
    const sectionContent = lines.slice(currentSection.start).join('\n').toLowerCase();
    let score = 0;
    
    for (const keyword of typeKeywords) {
      if (sectionContent.includes(keyword)) {
        score++;
      }
    }
    
    if (score > 0 && (!bestMatch || score > bestMatch.score)) {
      bestMatch = {
        start: currentSection.start,
        end: lines.length - 1,
        score
      };
    }
  }
  
  return bestMatch ? { start: bestMatch.start, end: bestMatch.end } : null;
}

function getTypeKeywords(contentType: string): string[] {
  const keywordMap: Record<string, string[]> = {
    architecture: ['architecture', 'design', 'system', 'component', 'structure'],
    database: ['database', 'schema', 'table', 'migration', 'model'],
    security: ['security', 'auth', 'permission', 'token', 'authentication'],
    api: ['api', 'endpoint', 'route', 'request', 'response'],
    setup: ['setup', 'install', 'configuration', 'environment'],
    features: ['feature', 'requirement', 'specification', 'functionality']
  };
  
  return keywordMap[contentType.toLowerCase()] || [contentType.toLowerCase()];
}

function generateFileName(lines: string[], category: string): string {
  // Try to find a suitable title from the content
  const titleLine = lines.find(line => /^##(?!#)\s+/.test(line));
  
  if (titleLine) {
    const title = titleLine
      .replace(/^##\s+/, '')
      .trim()
      .toUpperCase()
      .replace(/[^A-Z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
    
    return `${title}.md`;
  }
  
  // Fallback to category-based name
  return `${category.toUpperCase()}_${Date.now()}.md`;
}