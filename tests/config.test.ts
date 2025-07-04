import { describe, it, expect } from 'vitest';
import { getDefaultConfig } from '../src/utils/config';

describe('Configuration', () => {
  it('should return default configuration', () => {
    const config = getDefaultConfig();
    
    expect(config.thresholds.claudeMdMaxLines).toBe(500);
    expect(config.thresholds.extractAtLines).toBe(200);
    expect(config.organization.docsFolder).toBe('/docs');
    expect(config.organization.useEmojis).toBe(true);
    expect(config.organization.autoReference).toBe(true);
    expect(config.patterns.enforceCriticalSection).toBe(true);
    expect(config.patterns.requireReadFirstFlags).toBe(true);
    expect(config.patterns.autoTroubleshootingDocs).toBe(true);
    expect(config.monitoring.watchMode).toBe(true);
    expect(config.monitoring.validateLinks).toBe(true);
    expect(config.monitoring.healthChecks).toBe(true);
  });
});