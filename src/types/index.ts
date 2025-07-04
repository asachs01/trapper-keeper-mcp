export interface DocumentCategory {
  emoji: string;
  label: string;
  description: string;
  keywords: string[];
}

export interface DocumentReference {
  path: string;
  category: string;
  emoji: string;
  title: string;
  critical?: boolean;
  description?: string;
}

export interface TrapperKeeperConfig {
  thresholds: {
    claudeMdMaxLines: number;
    extractAtLines: number;
  };
  organization: {
    docsFolder: string;
    useEmojis: boolean;
    autoReference: boolean;
  };
  patterns: {
    enforceCriticalSection: boolean;
    requireReadFirstFlags: boolean;
    autoTroubleshootingDocs: boolean;
  };
  monitoring: {
    watchMode: boolean;
    validateLinks: boolean;
    healthChecks: boolean;
  };
}

export interface FileAnalysis {
  path: string;
  lineCount: number;
  references: DocumentReference[];
  categories: Map<string, number>;
  needsExtraction: boolean;
  suggestedExtractions: ExtractionSuggestion[];
}

export interface ExtractionSuggestion {
  contentType: string;
  category: string;
  startLine: number;
  endLine: number;
  suggestedFileName: string;
  reason: string;
}

export interface OrganizationResult {
  success: boolean;
  extractedFiles: string[];
  updatedReferences: DocumentReference[];
  errors?: string[];
}