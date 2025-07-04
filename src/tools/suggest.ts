import { readFile } from 'fs/promises';
import { join } from 'path';
import { glob } from 'glob';
import { TrapperKeeperConfig } from '../types/index.js';
import { analyzeFile } from '../utils/analyzer.js';
import { DOCUMENT_CATEGORIES } from '../utils/categories.js';

interface Suggestion {
  type: 'extract' | 'organize' | 'reference' | 'structure';
  priority: 'high' | 'medium' | 'low';
  message: string;
  details?: string;
  action?: string;
}

interface ImprovementSuggestions {
  suggestions: Suggestion[];
  metrics: {
    fileSize: number;
    referenceCount: number;
    categoryCoverage: string[];
    missingCategories: string[];
  };
}

export async function suggestImprovements(
  projectPath: string,
  claudeMdPath: string,
  config: TrapperKeeperConfig
): Promise<ImprovementSuggestions> {
  const suggestions: Suggestion[] = [];
  
  try {
    // Analyze CLAUDE.md
    const analysis = await analyzeFile(claudeMdPath, config);
    
    // Get all docs
    const docFiles = await glob('**/*.md', {
      cwd: join(projectPath, config.organization.docsFolder),
      ignore: ['node_modules/**', 'dist/**']
    });
    
    // Analyze category coverage
    const existingCategories = new Set<string>();
    analysis.categories.forEach((_, category) => existingCategories.add(category));
    
    const allCategories = Object.keys(DOCUMENT_CATEGORIES);
    const missingCategories = allCategories.filter(cat => !existingCategories.has(cat));
    
    // Size-based suggestions
    if (analysis.lineCount > config.thresholds.claudeMdMaxLines) {
      suggestions.push({
        type: 'extract',
        priority: 'high',
        message: `CLAUDE.md is too large (${analysis.lineCount} lines)`,
        details: `File exceeds maximum of ${config.thresholds.claudeMdMaxLines} lines`,
        action: 'Run organize_documentation to automatically extract sections'
      });
    } else if (analysis.lineCount > config.thresholds.extractAtLines) {
      suggestions.push({
        type: 'extract',
        priority: 'medium',
        message: `CLAUDE.md is approaching size limit (${analysis.lineCount} lines)`,
        details: `Consider extracting sections before reaching ${config.thresholds.claudeMdMaxLines} lines`,
        action: 'Review suggested extractions and extract large sections'
      });
    }
    
    // Extraction suggestions
    if (analysis.suggestedExtractions.length > 0) {
      for (const extraction of analysis.suggestedExtractions) {
        suggestions.push({
          type: 'extract',
          priority: 'medium',
          message: `Extract "${extraction.contentType}" section`,
          details: extraction.reason,
          action: `Extract lines ${extraction.startLine}-${extraction.endLine} to ${extraction.suggestedFileName}`
        });
      }
    }
    
    // Reference organization
    if (docFiles.length > analysis.references.length) {
      suggestions.push({
        type: 'reference',
        priority: 'high',
        message: 'Missing references to documentation files',
        details: `Found ${docFiles.length} docs but only ${analysis.references.length} references`,
        action: 'Add references to all documentation files in CLAUDE.md'
      });
    }
    
    // Critical documentation
    const criticalCount = analysis.references.filter(r => r.critical).length;
    if (criticalCount === 0 && docFiles.length > 0) {
      suggestions.push({
        type: 'structure',
        priority: 'medium',
        message: 'No critical documentation marked',
        details: 'Consider marking foundational docs with "READ THIS FIRST!"',
        action: 'Identify and mark critical documentation'
      });
    }
    
    // Category coverage
    if (missingCategories.length > 0 && missingCategories.length < allCategories.length / 2) {
      suggestions.push({
        type: 'organize',
        priority: 'low',
        message: `Missing documentation for categories: ${missingCategories.join(', ')}`,
        details: 'Consider adding documentation for these areas',
        action: 'Create documentation for missing categories'
      });
    }
    
    // Structure suggestions
    const hasReferenceSection = analysis.references.length > 0 || 
      (await readFile(claudeMdPath, 'utf-8')).includes('Documentation References');
    
    if (!hasReferenceSection && docFiles.length > 0) {
      suggestions.push({
        type: 'structure',
        priority: 'high',
        message: 'Missing documentation references section',
        details: 'Add a "Key Documentation References" section to CLAUDE.md',
        action: 'Create reference section with links to all docs'
      });
    }
    
    // Critical pattern enforcement
    if (config.patterns.enforceCriticalSection) {
      const content = await readFile(claudeMdPath, 'utf-8');
      if (!content.includes('CRITICAL DOCUMENTATION')) {
        suggestions.push({
          type: 'structure',
          priority: 'high',
          message: 'Missing CRITICAL DOCUMENTATION section',
          details: 'This section helps track important operational docs',
          action: 'Add "## 📋 CRITICAL DOCUMENTATION PATTERN" section'
        });
      }
    }
    
    return {
      suggestions: suggestions.sort((a, b) => {
        const priorityOrder = { high: 0, medium: 1, low: 2 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }),
      metrics: {
        fileSize: analysis.lineCount,
        referenceCount: analysis.references.length,
        categoryCoverage: Array.from(existingCategories),
        missingCategories
      }
    };
  } catch (error) {
    return {
      suggestions: [{
        type: 'structure',
        priority: 'high',
        message: 'Failed to analyze documentation',
        details: `Error: ${error}`,
        action: 'Check file paths and permissions'
      }],
      metrics: {
        fileSize: 0,
        referenceCount: 0,
        categoryCoverage: [],
        missingCategories: []
      }
    };
  }
}