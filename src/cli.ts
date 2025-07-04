#!/usr/bin/env node

import { Command } from 'commander';
import { readFile, writeFile } from 'fs/promises';
import { join } from 'path';
import chalk from 'chalk';
import { watch } from 'chokidar';
import { loadConfig, getDefaultConfig } from './utils/config.js';
import { organizeDocumentation } from './tools/organize.js';
import { extractContent } from './tools/extract.js';
import { validateStructure } from './tools/validate.js';
import { suggestImprovements } from './tools/suggest.js';
import { trackCriticalDocs } from './tools/critical.js';

export function startCLI() {
  const program = new Command();

  program
    .name('trapper-keeper')
    .description('Keep your AI context organized like a boss')
    .version('0.1.0');

  program
    .command('init')
    .description('Initialize Trapper Keeper in your project')
    .action(async () => {
      try {
        const configPath = join(process.cwd(), 'trapper-keeper.yml');
        const config = getDefaultConfig();
        
        // Create config file
        const yamlContent = `# Trapper Keeper Configuration
thresholds:
  claudeMdMaxLines: ${config.thresholds.claudeMdMaxLines}
  extractAtLines: ${config.thresholds.extractAtLines}
  
organization:
  docsFolder: "${config.organization.docsFolder}"
  useEmojis: ${config.organization.useEmojis}
  autoReference: ${config.organization.autoReference}
  
patterns:
  enforceCriticalSection: ${config.patterns.enforceCriticalSection}
  requireReadFirstFlags: ${config.patterns.requireReadFirstFlags}
  autoTroubleshootingDocs: ${config.patterns.autoTroubleshootingDocs}

monitoring:
  watchMode: ${config.monitoring.watchMode}
  validateLinks: ${config.monitoring.validateLinks}
  healthChecks: ${config.monitoring.healthChecks}
`;
        
        await writeFile(configPath, yamlContent);
        console.log(chalk.green('✅ Trapper Keeper initialized!'));
        console.log(chalk.gray(`Configuration saved to: ${configPath}`));
      } catch (error) {
        console.error(chalk.red('Failed to initialize:'), error);
        process.exit(1);
      }
    });

  program
    .command('organize')
    .description('Auto-organize existing CLAUDE.md')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-f, --file <path>', 'CLAUDE.md file path')
    .option('--dry-run', 'Preview changes without applying them')
    .action(async (options) => {
      try {
        const projectPath = options.project;
        const claudeMdPath = options.file || join(projectPath, 'CLAUDE.md');
        const config = await loadConfig(projectPath);
        
        console.log(chalk.blue('🗂️  Organizing documentation...'));
        
        const result = await organizeDocumentation(
          projectPath,
          claudeMdPath,
          config,
          options.dryRun
        );
        
        if (result.success) {
          console.log(chalk.green('✅ Organization complete!'));
          if (result.extractedFiles.length > 0) {
            console.log(chalk.gray('\nExtracted files:'));
            result.extractedFiles.forEach(file => {
              console.log(chalk.gray(`  - ${file}`));
            });
          }
        } else {
          console.error(chalk.red('❌ Organization failed:'));
          result.errors?.forEach(err => console.error(chalk.red(`  - ${err}`)));
        }
      } catch (error) {
        console.error(chalk.red('Error:'), error);
        process.exit(1);
      }
    });

  program
    .command('extract')
    .description('Extract specific content type from CLAUDE.md')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-f, --file <path>', 'CLAUDE.md file path')
    .option('-t, --type <type>', 'Content type to extract')
    .option('--start <line>', 'Starting line number', parseInt)
    .option('--end <line>', 'Ending line number', parseInt)
    .action(async (options) => {
      try {
        const projectPath = options.project;
        const claudeMdPath = options.file || join(projectPath, 'CLAUDE.md');
        const config = await loadConfig(projectPath);
        
        console.log(chalk.blue('📤 Extracting content...'));
        
        const result = await extractContent(
          claudeMdPath,
          projectPath,
          config,
          {
            contentType: options.type,
            startLine: options.start,
            endLine: options.end
          }
        );
        
        if (result.success) {
          console.log(chalk.green('✅ Extraction complete!'));
          console.log(chalk.gray(`Extracted to: ${result.extractedFile}`));
          if (result.reference) {
            console.log(chalk.gray(`Reference added: ${result.reference}`));
          }
        } else {
          console.error(chalk.red('❌ Extraction failed:'), result.error);
        }
      } catch (error) {
        console.error(chalk.red('Error:'), error);
        process.exit(1);
      }
    });

  program
    .command('validate')
    .description('Validate documentation structure')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .action(async (options) => {
      try {
        const projectPath = options.project;
        const config = await loadConfig(projectPath);
        
        console.log(chalk.blue('🔍 Validating documentation structure...'));
        
        const result = await validateStructure(projectPath, config);
        
        if (result.valid) {
          console.log(chalk.green('✅ Documentation structure is valid!'));
        } else {
          console.log(chalk.yellow('⚠️  Issues found:'));
          result.issues.forEach(issue => {
            const icon = issue.type === 'broken_reference' ? '🔗' : 
                        issue.type === 'oversized_file' ? '📏' :
                        issue.type === 'missing_file' ? '❌' : '⚠️';
            console.log(chalk.yellow(`  ${icon} ${issue.message}`));
            if (issue.line) {
              console.log(chalk.gray(`     Line ${issue.line}`));
            }
          });
        }
        
        console.log(chalk.gray('\nStatistics:'));
        console.log(chalk.gray(`  Total files: ${result.stats.totalFiles}`));
        console.log(chalk.gray(`  Total references: ${result.stats.totalReferences}`));
        console.log(chalk.gray(`  Broken references: ${result.stats.brokenReferences}`));
        console.log(chalk.gray(`  Oversized files: ${result.stats.oversizedFiles}`));
        console.log(chalk.gray(`  Critical docs: ${result.stats.criticalDocs}`));
      } catch (error) {
        console.error(chalk.red('Error:'), error);
        process.exit(1);
      }
    });

  program
    .command('suggest')
    .description('Get improvement suggestions')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-f, --file <path>', 'CLAUDE.md file path')
    .action(async (options) => {
      try {
        const projectPath = options.project;
        const claudeMdPath = options.file || join(projectPath, 'CLAUDE.md');
        const config = await loadConfig(projectPath);
        
        console.log(chalk.blue('💡 Analyzing documentation...'));
        
        const result = await suggestImprovements(projectPath, claudeMdPath, config);
        
        if (result.suggestions.length === 0) {
          console.log(chalk.green('✅ Documentation looks great!'));
        } else {
          console.log(chalk.yellow('📋 Suggestions:'));
          result.suggestions.forEach((suggestion, index) => {
            const icon = suggestion.priority === 'high' ? '🔴' :
                        suggestion.priority === 'medium' ? '🟡' : '🟢';
            console.log(chalk.yellow(`\n${index + 1}. ${icon} ${suggestion.message}`));
            if (suggestion.details) {
              console.log(chalk.gray(`   ${suggestion.details}`));
            }
            if (suggestion.action) {
              console.log(chalk.cyan(`   → ${suggestion.action}`));
            }
          });
        }
        
        console.log(chalk.gray('\n📊 Metrics:'));
        console.log(chalk.gray(`  File size: ${result.metrics.fileSize} lines`));
        console.log(chalk.gray(`  References: ${result.metrics.referenceCount}`));
        console.log(chalk.gray(`  Categories: ${result.metrics.categoryCoverage.join(', ')}`));
      } catch (error) {
        console.error(chalk.red('Error:'), error);
        process.exit(1);
      }
    });

  program
    .command('watch')
    .description('Monitor and maintain documentation')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .action(async (options) => {
      try {
        const projectPath = options.project;
        const config = await loadConfig(projectPath);
        
        console.log(chalk.blue('👀 Watching for changes...'));
        
        const watcher = watch(['**/*.md'], {
          cwd: projectPath,
          ignored: ['node_modules/**', 'dist/**', '.git/**'],
          persistent: true
        });
        
        watcher.on('change', async (path) => {
          console.log(chalk.gray(`\n📝 Changed: ${path}`));
          
          if (path === 'CLAUDE.md' || path.endsWith('/CLAUDE.md')) {
            const claudeMdPath = join(projectPath, path);
            const suggestions = await suggestImprovements(projectPath, claudeMdPath, config);
            
            if (suggestions.suggestions.some(s => s.priority === 'high')) {
              console.log(chalk.yellow('⚠️  High priority suggestions detected!'));
              suggestions.suggestions
                .filter(s => s.priority === 'high')
                .forEach(s => console.log(chalk.yellow(`  - ${s.message}`)));
            }
          }
        });
        
        console.log(chalk.gray('Press Ctrl+C to stop watching'));
      } catch (error) {
        console.error(chalk.red('Error:'), error);
        process.exit(1);
      }
    });

  program.parse();
}