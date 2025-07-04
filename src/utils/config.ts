import { readFile } from 'fs/promises';
import { parse } from 'js-yaml';
import { join } from 'path';
import { TrapperKeeperConfig } from '../types/index.js';

const DEFAULT_CONFIG: TrapperKeeperConfig = {
  thresholds: {
    claudeMdMaxLines: 500,
    extractAtLines: 200
  },
  organization: {
    docsFolder: '/docs',
    useEmojis: true,
    autoReference: true
  },
  patterns: {
    enforceCriticalSection: true,
    requireReadFirstFlags: true,
    autoTroubleshootingDocs: true
  },
  monitoring: {
    watchMode: true,
    validateLinks: true,
    healthChecks: true
  }
};

export async function loadConfig(projectRoot: string): Promise<TrapperKeeperConfig> {
  try {
    const configPath = join(projectRoot, 'trapper-keeper.yml');
    const configContent = await readFile(configPath, 'utf-8');
    const userConfig = parse(configContent) as Partial<TrapperKeeperConfig>;
    
    return {
      thresholds: { ...DEFAULT_CONFIG.thresholds, ...userConfig.thresholds },
      organization: { ...DEFAULT_CONFIG.organization, ...userConfig.organization },
      patterns: { ...DEFAULT_CONFIG.patterns, ...userConfig.patterns },
      monitoring: { ...DEFAULT_CONFIG.monitoring, ...userConfig.monitoring }
    };
  } catch (error) {
    // If config file doesn't exist, use defaults
    return DEFAULT_CONFIG;
  }
}

export function getDefaultConfig(): TrapperKeeperConfig {
  return DEFAULT_CONFIG;
}