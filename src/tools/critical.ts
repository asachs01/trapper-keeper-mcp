import { readFile, writeFile } from 'fs/promises';
import { join } from 'path';
import { glob } from 'glob';
import { TrapperKeeperConfig, DocumentReference } from '../types/index.js';
import { analyzeFile } from '../utils/analyzer.js';
import { formatReference } from './reference.js';

interface CriticalTrackingResult {
  success: boolean;
  criticalDocs: DocumentReference[];
  updated: boolean;
  message: string;
}

export async function trackCriticalDocs(
  projectPath: string,
  claudeMdPath: string,
  config: TrapperKeeperConfig
): Promise<CriticalTrackingResult> {
  try {
    // Find all critical documentation
    const criticalDocs = await findCriticalDocumentation(projectPath, config);
    
    // Read current CLAUDE.md
    const content = await readFile(claudeMdPath, 'utf-8');
    const lines = content.split('\n');
    
    // Find or create critical documentation section
    let criticalSectionIndex = lines.findIndex(line => 
      line.includes('CRITICAL DOCUMENTATION PATTERN') ||
      line.includes('Critical Documentation Pattern')
    );
    
    let updated = false;
    
    if (criticalSectionIndex === -1 && config.patterns.enforceCriticalSection) {
      // Add critical section
      const referenceSectionIndex = lines.findIndex(line => 
        line.includes('Documentation References')
      );
      
      const insertIndex = referenceSectionIndex !== -1 
        ? referenceSectionIndex + lines.slice(referenceSectionIndex).findIndex(line => line.trim() === '') + 1
        : lines.findIndex(line => line.startsWith('#')) + 2;
      
      lines.splice(insertIndex, 0,
        '',
        '## 📋 CRITICAL DOCUMENTATION PATTERN',
        '',
        'The following documentation is critical for system operation and troubleshooting:',
        ''
      );
      
      criticalSectionIndex = insertIndex + 1;
      updated = true;
    }
    
    if (criticalSectionIndex !== -1) {
      // Update critical docs list
      const sectionStart = criticalSectionIndex + 3;
      let sectionEnd = sectionStart;
      
      // Find end of critical section
      while (sectionEnd < lines.length && lines[sectionEnd].trim() !== '' && !lines[sectionEnd].startsWith('#')) {
        sectionEnd++;
      }
      
      // Remove old critical docs
      if (sectionEnd > sectionStart) {
        lines.splice(sectionStart, sectionEnd - sectionStart);
      }
      
      // Add updated critical docs
      const criticalRefs = criticalDocs.map(doc => formatReference(doc));
      lines.splice(sectionStart, 0, ...criticalRefs);
      
      updated = true;
    }
    
    // Ensure critical docs are marked in reference section
    const analysis = await analyzeFile(claudeMdPath, config);
    let referencesUpdated = false;
    
    for (const criticalDoc of criticalDocs) {
      const existingRef = analysis.references.find(r => r.path === criticalDoc.path);
      if (existingRef && !existingRef.critical) {
        // Update reference to mark as critical
        const refLineIndex = lines.findIndex(line => 
          line.includes(criticalDoc.path) && line.includes('**')
        );
        
        if (refLineIndex !== -1 && !lines[refLineIndex].includes('READ THIS FIRST!')) {
          lines[refLineIndex] += ' 🚨 READ THIS FIRST!';
          referencesUpdated = true;
        }
      }
    }
    
    if (updated || referencesUpdated) {
      await writeFile(claudeMdPath, lines.join('\n'));
    }
    
    return {
      success: true,
      criticalDocs,
      updated: updated || referencesUpdated,
      message: `Tracked ${criticalDocs.length} critical documents${updated ? ' and updated CLAUDE.md' : ''}`
    };
  } catch (error) {
    return {
      success: false,
      criticalDocs: [],
      updated: false,
      message: `Failed to track critical docs: ${error}`
    };
  }
}

async function findCriticalDocumentation(
  projectPath: string,
  config: TrapperKeeperConfig
): Promise<DocumentReference[]> {
  const criticalDocs: DocumentReference[] = [];
  const criticalPatterns = [
    'troubleshooting',
    'emergency',
    'critical',
    'error',
    'problem',
    'solution',
    'setup',
    'getting.?started',
    'quick.?start',
    'installation',
    'deployment'
  ];
  
  // Search for critical documentation
  const docFiles = await glob('**/*.md', {
    cwd: projectPath,
    ignore: ['node_modules/**', 'dist/**', '.git/**']
  });
  
  for (const file of docFiles) {
    const filePath = join(projectPath, file);
    const fileName = file.toLowerCase();
    const content = await readFile(filePath, 'utf-8').catch(() => '');
    
    // Check if file matches critical patterns
    let isCritical = false;
    let matchedPattern = '';
    
    for (const pattern of criticalPatterns) {
      const regex = new RegExp(pattern, 'i');
      if (regex.test(fileName) || regex.test(content.slice(0, 500))) {
        isCritical = true;
        matchedPattern = pattern;
        break;
      }
    }
    
    // Check for explicit critical markers
    if (content.includes('CRITICAL') || 
        content.includes('IMPORTANT') || 
        content.includes('READ THIS FIRST')) {
      isCritical = true;
      matchedPattern = 'explicit marker';
    }
    
    if (isCritical) {
      // Extract title from file
      const lines = content.split('\n');
      const titleLine = lines.find(line => line.startsWith('#'));
      const title = titleLine 
        ? titleLine.replace(/^#+\s*/, '').trim()
        : file.replace('.md', '').replace(/[_-]/g, ' ');
      
      criticalDocs.push({
        path: `/${file}`,
        category: 'critical',
        emoji: '🚨',
        title,
        critical: true,
        description: `Critical documentation (${matchedPattern})`
      });
    }
  }
  
  return criticalDocs;
}