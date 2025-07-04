import { DocumentCategory } from '../types/index.js';

export const DOCUMENT_CATEGORIES: Record<string, DocumentCategory> = {
  architecture: {
    emoji: '🏗️',
    label: 'Architecture',
    description: 'System design, technical architecture',
    keywords: ['architecture', 'design', 'system', 'structure', 'components', 'diagram']
  },
  database: {
    emoji: '🗄️',
    label: 'Database',
    description: 'Schemas, migrations, data models',
    keywords: ['database', 'schema', 'migration', 'model', 'sql', 'table', 'column']
  },
  security: {
    emoji: '🔐',
    label: 'Security',
    description: 'Auth, permissions, security protocols',
    keywords: ['security', 'auth', 'authentication', 'authorization', 'permission', 'token', 'jwt']
  },
  features: {
    emoji: '✅',
    label: 'Features',
    description: 'Specifications, requirements',
    keywords: ['feature', 'specification', 'requirement', 'story', 'use case', 'functionality']
  },
  monitoring: {
    emoji: '📊',
    label: 'Monitoring',
    description: 'Health checks, analytics, logging',
    keywords: ['monitoring', 'health', 'analytics', 'logging', 'metrics', 'telemetry', 'observability']
  },
  critical: {
    emoji: '🚨',
    label: 'Critical',
    description: 'Troubleshooting, emergency procedures',
    keywords: ['critical', 'emergency', 'troubleshooting', 'error', 'fix', 'issue', 'problem', 'solution']
  },
  setup: {
    emoji: '📋',
    label: 'Setup',
    description: 'Installation, deployment guides',
    keywords: ['setup', 'install', 'deployment', 'configuration', 'environment', 'getting started']
  },
  api: {
    emoji: '🌐',
    label: 'API',
    description: 'Endpoints, integrations, documentation',
    keywords: ['api', 'endpoint', 'integration', 'rest', 'graphql', 'webhook', 'service']
  }
};

export function detectCategory(content: string): string {
  const lowercaseContent = content.toLowerCase();
  let bestMatch = { category: 'features', score: 0 };

  for (const [key, category] of Object.entries(DOCUMENT_CATEGORIES)) {
    let score = 0;
    for (const keyword of category.keywords) {
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
      const matches = lowercaseContent.match(regex);
      if (matches) {
        score += matches.length;
      }
    }
    
    if (score > bestMatch.score) {
      bestMatch = { category: key, score };
    }
  }

  return bestMatch.category;
}

export function getCategoryEmoji(category: string): string {
  return DOCUMENT_CATEGORIES[category]?.emoji || '📄';
}

export function getCategoryLabel(category: string): string {
  return DOCUMENT_CATEGORIES[category]?.label || 'Document';
}