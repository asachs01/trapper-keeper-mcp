import { readFile } from 'fs/promises';
import { relative } from 'path';
import { DocumentReference } from '../types/index.js';
import { detectCategory, getCategoryEmoji } from '../utils/categories.js';

export async function createReference(
  documentPath: string,
  title: string,
  projectPath: string,
  category?: string,
  critical = false
): Promise<DocumentReference> {
  // Read document to detect category if not provided
  if (!category) {
    try {
      const content = await readFile(documentPath, 'utf-8');
      category = detectCategory(content);
    } catch {
      category = 'features';
    }
  }
  
  const relativePath = documentPath.startsWith('/') 
    ? relative(projectPath, documentPath)
    : documentPath;
  
  const emoji = getCategoryEmoji(category);
  
  return {
    path: relativePath.startsWith('/') ? relativePath : `/${relativePath}`,
    category,
    emoji,
    title,
    critical,
    description: critical ? '🚨 READ THIS FIRST!' : undefined
  };
}

export function formatReference(ref: DocumentReference): string {
  const criticalFlag = ref.critical ? ' 🚨 READ THIS FIRST!' : '';
  return `- **${ref.emoji} ${ref.title}**: \`${ref.path}\`${criticalFlag}`;
}

export function formatReferenceSection(references: DocumentReference[]): string {
  const lines: string[] = [
    '## 📚 Key Documentation References',
    ''
  ];
  
  // Group by category
  const grouped = references.reduce((acc, ref) => {
    if (!acc[ref.category]) {
      acc[ref.category] = [];
    }
    acc[ref.category].push(ref);
    return acc;
  }, {} as Record<string, DocumentReference[]>);
  
  // Sort categories with critical docs first
  const sortedCategories = Object.keys(grouped).sort((a, b) => {
    const aCritical = grouped[a].some(r => r.critical);
    const bCritical = grouped[b].some(r => r.critical);
    
    if (aCritical && !bCritical) return -1;
    if (!aCritical && bCritical) return 1;
    return 0;
  });
  
  // Format references
  for (const category of sortedCategories) {
    const refs = grouped[category];
    
    // Sort refs with critical first
    refs.sort((a, b) => {
      if (a.critical && !b.critical) return -1;
      if (!a.critical && b.critical) return 1;
      return 0;
    });
    
    for (const ref of refs) {
      lines.push(formatReference(ref));
    }
  }
  
  return lines.join('\n');
}