import { readFile } from 'fs/promises';
import { FileAnalysis, DocumentReference, ExtractionSuggestion, TrapperKeeperConfig } from '../types/index.js';
import { detectCategory, getCategoryEmoji } from './categories.js';

export async function analyzeFile(
  filePath: string,
  config: TrapperKeeperConfig
): Promise<FileAnalysis> {
  const content = await readFile(filePath, 'utf-8');
  const lines = content.split('\n');
  const lineCount = lines.length;
  
  const references = extractReferences(lines);
  const categories = detectCategories(content);
  const needsExtraction = lineCount > config.thresholds.extractAtLines;
  const suggestedExtractions = needsExtraction ? analyzeSections(lines, config) : [];

  return {
    path: filePath,
    lineCount,
    references,
    categories,
    needsExtraction,
    suggestedExtractions
  };
}

function extractReferences(lines: string[]): DocumentReference[] {
  const references: DocumentReference[] = [];
  const referencePattern = /^-\s*\*\*([^*]+)\*\*:\s*`([^`]+)`\s*(.*)$/;
  
  for (const line of lines) {
    const match = line.match(referencePattern);
    if (match) {
      const [, title, path, rest] = match;
      const critical = rest.includes('READ THIS FIRST!');
      const emoji = rest.match(/^([\u{1F300}-\u{1F6FF}])/u)?.[0];
      
      references.push({
        path,
        category: detectCategory(title),
        emoji: emoji || getCategoryEmoji(detectCategory(title)),
        title,
        critical
      });
    }
  }
  
  return references;
}

function detectCategories(content: string): Map<string, number> {
  const categories = new Map<string, number>();
  const sections = content.split(/^#+\s+/m);
  
  for (const section of sections) {
    if (section.trim()) {
      const category = detectCategory(section);
      categories.set(category, (categories.get(category) || 0) + 1);
    }
  }
  
  return categories;
}

function analyzeSections(lines: string[], config: TrapperKeeperConfig): ExtractionSuggestion[] {
  const suggestions: ExtractionSuggestion[] = [];
  let currentSection: { title: string; startLine: number; content: string[] } | null = null;
  
  lines.forEach((line, index) => {
    // Detect section headers (## or ###)
    if (/^##(?!#)\s+/.test(line)) {
      if (currentSection && currentSection.content.length > 50) {
        const category = detectCategory(currentSection.content.join('\n'));
        suggestions.push({
          contentType: category,
          category,
          startLine: currentSection.startLine,
          endLine: index - 1,
          suggestedFileName: generateFileName(currentSection.title, category),
          reason: `Section "${currentSection.title}" has ${currentSection.content.length} lines and appears to be ${category} documentation`
        });
      }
      
      currentSection = {
        title: line.replace(/^##\s+/, '').trim(),
        startLine: index,
        content: []
      };
    } else if (currentSection) {
      currentSection.content.push(line);
    }
  });
  
  // Check last section
  if (currentSection && currentSection.content.length > 50) {
    const category = detectCategory(currentSection.content.join('\n'));
    suggestions.push({
      contentType: category,
      category,
      startLine: currentSection.startLine,
      endLine: lines.length - 1,
      suggestedFileName: generateFileName(currentSection.title, category),
      reason: `Section "${currentSection.title}" has ${currentSection.content.length} lines and appears to be ${category} documentation`
    });
  }
  
  return suggestions;
}

function generateFileName(title: string, category: string): string {
  const sanitized = title
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
  
  return `${sanitized}.md`;
}