import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { existsSync } from 'fs';
import { TrapperKeeperConfig, OrganizationResult, DocumentReference } from '../types/index.js';
import { analyzeFile } from '../utils/analyzer.js';
import { getCategoryEmoji } from '../utils/categories.js';

export async function organizeDocumentation(
  projectPath: string,
  claudeMdPath: string,
  config: TrapperKeeperConfig,
  dryRun = false
): Promise<OrganizationResult> {
  try {
    // Analyze the CLAUDE.md file
    const analysis = await analyzeFile(claudeMdPath, config);
    
    if (!analysis.needsExtraction) {
      return {
        success: true,
        extractedFiles: [],
        updatedReferences: analysis.references,
        errors: [`File is within size limits (${analysis.lineCount} lines)`]
      };
    }

    const extractedFiles: string[] = [];
    const errors: string[] = [];

    // Process each extraction suggestion
    for (const suggestion of analysis.suggestedExtractions) {
      try {
        const docPath = join(projectPath, config.organization.docsFolder, suggestion.suggestedFileName);
        
        if (!dryRun) {
          // Create docs directory if it doesn't exist
          const docsDir = dirname(docPath);
          if (!existsSync(docsDir)) {
            await mkdir(docsDir, { recursive: true });
          }

          // Extract content
          const content = await readFile(claudeMdPath, 'utf-8');
          const lines = content.split('\n');
          const extractedContent = lines.slice(suggestion.startLine, suggestion.endLine + 1).join('\n');
          
          // Write extracted content
          await writeFile(docPath, extractedContent);
          extractedFiles.push(docPath);
        } else {
          extractedFiles.push(`[DRY RUN] Would extract to: ${docPath}`);
        }
      } catch (error) {
        errors.push(`Failed to extract ${suggestion.suggestedFileName}: ${error}`);
      }
    }

    // Update CLAUDE.md with references
    if (!dryRun && extractedFiles.length > 0) {
      await updateClaudeMdWithReferences(claudeMdPath, extractedFiles, config);
    }

    return {
      success: errors.length === 0,
      extractedFiles,
      updatedReferences: analysis.references,
      errors: errors.length > 0 ? errors : undefined
    };
  } catch (error) {
    return {
      success: false,
      extractedFiles: [],
      updatedReferences: [],
      errors: [`Organization failed: ${error}`]
    };
  }
}

async function updateClaudeMdWithReferences(
  claudeMdPath: string,
  extractedFiles: string[],
  config: TrapperKeeperConfig
): Promise<void> {
  const content = await readFile(claudeMdPath, 'utf-8');
  const lines = content.split('\n');
  
  // Find or create reference section
  let referenceSectionIndex = lines.findIndex(line => 
    line.includes('Key Documentation References') || 
    line.includes('Documentation References')
  );
  
  if (referenceSectionIndex === -1) {
    // Add reference section at the beginning after the title
    const titleIndex = lines.findIndex(line => line.startsWith('#'));
    referenceSectionIndex = titleIndex + 1;
    
    lines.splice(referenceSectionIndex, 0, 
      '',
      '## 📚 Key Documentation References',
      ''
    );
  }
  
  // Add new references
  const referenceStartIndex = referenceSectionIndex + 2;
  const newReferences: string[] = [];
  
  for (const file of extractedFiles) {
    const fileName = file.split('/').pop()?.replace('.md', '') || '';
    const category = detectCategoryFromFileName(fileName);
    const emoji = getCategoryEmoji(category);
    const relativePath = file.replace(claudeMdPath.replace('/CLAUDE.md', ''), '');
    
    newReferences.push(`- **${emoji} ${fileName}**: \`${relativePath}\``);
  }
  
  lines.splice(referenceStartIndex, 0, ...newReferences);
  
  await writeFile(claudeMdPath, lines.join('\n'));
}

function detectCategoryFromFileName(fileName: string): string {
  const lowerName = fileName.toLowerCase();
  
  if (lowerName.includes('arch')) return 'architecture';
  if (lowerName.includes('db') || lowerName.includes('database')) return 'database';
  if (lowerName.includes('auth') || lowerName.includes('security')) return 'security';
  if (lowerName.includes('setup') || lowerName.includes('install')) return 'setup';
  if (lowerName.includes('api')) return 'api';
  if (lowerName.includes('trouble') || lowerName.includes('error')) return 'critical';
  
  return 'features';
}