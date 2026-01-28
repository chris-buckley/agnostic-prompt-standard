import { Command } from 'commander';
import { createRequire } from 'node:module';
import process from 'node:process';

import { runDoctor } from './commands/doctor.js';
import { runInit } from './commands/init.js';
import { runPlatforms } from './commands/platforms.js';

const require = createRequire(import.meta.url);
const pkg = require('../package.json') as { version: string };

const EXIT_USAGE = 2;

export async function main(argv: string[]): Promise<void> {
  const program = new Command();
  program.name('aps').description('Install and manage the Agnostic Prompt Standard (APS) skill.').version(pkg.version);

  program
    .command('init')
    .description('Install APS skill')
    .option('--root <path>', 'Workspace root path (defaults to git repo root if found)')
    .option('--repo', 'Install as a project skill (under .github/skills or .claude/skills)')
    .option('--personal', 'Install as a personal skill (under ~/.copilot/skills or ~/.claude/skills)')
    .option('--platform <id...>', 'Platform adapter(s) to apply (e.g. vscode-copilot, claude-code). Use "none" to skip.')
    .option('-y, --yes', 'Non-interactive; accept defaults', false)
    .option('-f, --force', 'Overwrite existing files', false)
    .option('--dry-run', 'Print planned actions without writing', false)
    .action((opts) =>
      runInit(opts).catch((e: unknown) => {
        const message = e instanceof Error ? e.message : String(e);
        console.error(`Error: ${message}`);
        process.exit(1);
      })
    );

  program
    .command('doctor')
    .description('Check APS installation status + basic platform detection')
    .option('--root <path>', 'Workspace root path (defaults to git repo root if found)')
    .option('--json', 'Output JSON format', false)
    .action((opts) =>
      runDoctor(opts).catch((e: unknown) => {
        const message = e instanceof Error ? e.message : String(e);
        console.error(`Error: ${message}`);
        process.exit(1);
      })
    );

  program
    .command('platforms')
    .description('List available platform adapters')
    .action(() =>
      runPlatforms().catch((e: unknown) => {
        const message = e instanceof Error ? e.message : String(e);
        console.error(`Error: ${message}`);
        process.exit(1);
      })
    );

  program
    .command('version')
    .description('Print CLI version')
    .action(() => {
      console.log(pkg.version);
    });

  await program.parseAsync(argv);

  // If no command was provided, show help and exit with usage.
  if (!program.args.length) {
    program.help({ error: true });
    process.exit(EXIT_USAGE);
  }
}
