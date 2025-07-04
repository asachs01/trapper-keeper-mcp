import { describe, it, expect } from 'vitest';
import { detectCategory, getCategoryEmoji, getCategoryLabel } from '../src/utils/categories';

describe('Category Detection', () => {
  it('should detect architecture category', () => {
    const content = 'This is about system architecture and design patterns';
    expect(detectCategory(content)).toBe('architecture');
  });

  it('should detect database category', () => {
    const content = 'Database schema and migration scripts for tables';
    expect(detectCategory(content)).toBe('database');
  });

  it('should detect security category', () => {
    const content = 'Authentication and authorization using JWT tokens';
    expect(detectCategory(content)).toBe('security');
  });

  it('should default to features category', () => {
    const content = 'Some random content without specific keywords';
    expect(detectCategory(content)).toBe('features');
  });

  it('should get correct emoji for category', () => {
    expect(getCategoryEmoji('architecture')).toBe('🏗️');
    expect(getCategoryEmoji('database')).toBe('🗄️');
    expect(getCategoryEmoji('security')).toBe('🔐');
    expect(getCategoryEmoji('unknown')).toBe('📄');
  });

  it('should get correct label for category', () => {
    expect(getCategoryLabel('architecture')).toBe('Architecture');
    expect(getCategoryLabel('database')).toBe('Database');
    expect(getCategoryLabel('security')).toBe('Security');
    expect(getCategoryLabel('unknown')).toBe('Document');
  });
});