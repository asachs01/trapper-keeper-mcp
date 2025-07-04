import { readFile, access } from 'fs/promises';
import { join } from 'path';
import { glob } from 'glob';
import { TrapperKeeperConfig } from '../types/index.js';

interface ValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
  stats: ValidationStats;
}

interface ValidationIssue {
  type: 'missing_file' | 'broken_reference' | 'oversized_file' | 'missing_critical_section';
  file: string;
  message: string;
  line?: number;
}

interface ValidationStats {
  totalFiles: number;
  totalReferences: number;
  brokenReferences: number;
  oversizedFiles: number;
  criticalDocs: number;
}

export async function validateStructure(
  projectPath: string,
  config: TrapperKeeperConfig
): Promise<ValidationResult> {
  const issues: ValidationIssue[] = [];
  const stats: ValidationStats = {
    totalFiles: 0,
    totalReferences: 0,
    brokenReferences: 0,
    oversizedFiles: 0,
    criticalDocs: 0
  };

  try {
    // Find all markdown files
    const mdFiles = await glob('**/*.md', { 
      cwd: projectPath,
      ignore: ['node_modules/**', 'dist/**', '.git/**']
    });
    
    stats.totalFiles = mdFiles.length;

    // Check each file
    for (const file of mdFiles) {
      const filePath = join(projectPath, file);
      await validateFile(filePath, projectPath, config, issues, stats);
    }

    // Check for CLAUDE.md specifically
    const claudeMdPath = join(projectPath, 'CLAUDE.md');
    try {
      await access(claudeMdPath);
      await validateClaudeMd(claudeMdPath, config, issues, stats);
    } catch {
      issues.push({
        type: 'missing_file',
        file: 'CLAUDE.md',
        message: 'CLAUDE.md file not found in project root'
      });
    }

    return {
      valid: issues.length === 0,
      issues,
      stats
    };
  } catch (error) {
    return {
      valid: false,
      issues: [{
        type: 'missing_file',
        file: projectPath,
        message: `Failed to validate project: ${error}`
      }],
      stats
    };
  }
}

async function validateFile(
  filePath: string,
  projectPath: string,
  config: TrapperKeeperConfig,
  issues: ValidationIssue[],
  stats: ValidationStats
): Promise<void> {
  const content = await readFile(filePath, 'utf-8');
  const lines = content.split('\n');
  
  // Check file size
  if (lines.length > config.thresholds.claudeMdMaxLines) {
    stats.oversizedFiles++;
    issues.push({
      type: 'oversized_file',
      file: filePath,
      message: `File has ${lines.length} lines (max: ${config.thresholds.claudeMdMaxLines})`
    });
  }
  
  // Check references
  const referencePattern = /`([^`]+\.(md|txt|yml|yaml|json))`/g;
  let match;
  let lineNum = 0;
  
  for (const line of lines) {
    lineNum++;
    while ((match = referencePattern.exec(line)) !== null) {
      stats.totalReferences++;
      const referencedPath = match[1];
      
      // Check if referenced file exists
      try {
        const fullPath = join(projectPath, referencedPath);
        await access(fullPath);
      } catch {
        stats.brokenReferences++;
        issues.push({
          type: 'broken_reference',
          file: filePath,
          message: `Broken reference to "${referencedPath}"`,
          line: lineNum
        });
      }
    }
  }
}

async function validateClaudeMd(
  claudeMdPath: string,
  config: TrapperKeeperConfig,
  issues: ValidationIssue[],
  stats: ValidationStats
): Promise<void> {
  const content = await readFile(claudeMdPath, 'utf-8');
  const lines = content.split('\n');
  
  // Check for critical documentation section
  if (config.patterns.enforceCriticalSection) {
    const hasCriticalSection = lines.some(line => 
      line.includes('CRITICAL DOCUMENTATION') || 
      line.includes('Critical Documentation')
    );
    
    if (!hasCriticalSection) {
      issues.push({
        type: 'missing_critical_section',
        file: claudeMdPath,
        message: 'Missing "CRITICAL DOCUMENTATION" section'
      });
    }
  }
  
  // Count critical docs
  stats.criticalDocs = lines.filter(line => 
    line.includes('READ THIS FIRST!')
  ).length;
  
  // Check for reference section
  const hasReferenceSection = lines.some(line => 
    line.includes('Documentation References') || 
    line.includes('Key Documentation')
  );
  
  if (!hasReferenceSection && stats.totalFiles > 1) {
    issues.push({
      type: 'missing_critical_section',
      file: claudeMdPath,
      message: 'Missing documentation references section'
    });
  }
}