import { Command } from 'commander';
import path from 'node:path';
import process from 'node:process';
import {
  checkbox,
  confirm,
  input,
  select,
} from '@inquirer/prompts';

import {
  SKILL_ID,
  copyDir,
  copyTemplates,
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  ensureDir,
  findRepoRoot,
  inferPlatformId,
  isDirectory,
  pathExists,
  removeDir,
  resolvePayloadSkillDir,
  loadPlatforms,
} from './core.js';

const EXIT_USAGE = 2;

function isTTY() {
  return Boolean(process.stdout.isTTY && process.stdin.isTTY);
}

function normalizePlatform(value) {
  if (!value) return undefined;
  if (value === 'none') return null;
  return value;
}

async function pickWorkspaceRoot(cliRoot) {
  if (cliRoot) return path.resolve(cliRoot);
  const repo = await findRepoRoot(process.cwd());
  return repo;
}

function fmtPath(p) {
  return p.replace(process.env.HOME ?? '', '~');
}

async function runInit(options) {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const repoRoot = await findRepoRoot(process.cwd());
  const guessedWorkspaceRoot = await pickWorkspaceRoot(options.root);

  // Determine scope
  let installScope = options.personal ? 'personal' : options.repo ? 'repo' : undefined;

  // Determine workspace root
  let workspaceRoot = guessedWorkspaceRoot;

  // Determine platform
  const detectedPlatform = workspaceRoot ? inferPlatformId(workspaceRoot) : null;
  let platformId = normalizePlatform(options.platform) ?? undefined;

  // Determine extras
  let installTemplates = Boolean(options.templates);

  if (!options.yes && isTTY()) {
    // Scope prompt
    if (!installScope) {
      installScope = await select({
        message: 'Where should APS be installed?',
        default: repoRoot ? 'repo' : 'personal',
        choices: [
          {
            name: repoRoot ? `Project skill in this repo (${fmtPath(repoRoot)})` : 'Project skill (choose a workspace folder)',
            value: 'repo',
          },
          {
            name: `Personal skill for your user (${fmtPath(defaultPersonalSkillPath({ claude: options.claude }).replace(SKILL_ID, ''))})`,
            value: 'personal',
          },
        ],
      });
    }

    if (installScope === 'repo' && !workspaceRoot) {
      const rootAnswer = await input({
        message: 'Workspace root path (the folder that contains .github/):',
        default: process.cwd(),
      });
      workspaceRoot = path.resolve(rootAnswer);
    }

    if (!platformId && workspaceRoot) {
      const platforms = await loadPlatforms(payloadSkillDir);
      const choices = [
        ...(detectedPlatform ? [{ name: `Auto-detected: ${detectedPlatform}`, value: detectedPlatform }] : []),
        { name: 'None (skip platform templates)', value: null },
        ...platforms
          .filter((p) => p.platformId !== detectedPlatform)
          .map((p) => ({
            name: `${p.displayName} (${p.platformId})`,
            value: p.platformId,
          })),
      ];

      platformId = await select({
        message: 'Select a platform adapter to apply:',
        default: detectedPlatform ?? null,
        choices,
      });
    }

    if (platformId && workspaceRoot) {
      const extras = await checkbox({
        message: 'Extras to apply to the workspace:',
        choices: [
          {
            name: 'Install platform templates (e.g. VS Code agent file + AGENTS.md)',
            value: 'templates',
            checked: true,
          },
        ],
      });
      installTemplates = extras.includes('templates');
    }
  } else {
    // Non-interactive defaults
    if (!installScope) installScope = repoRoot ? 'repo' : 'personal';
    if (!platformId && workspaceRoot) platformId = detectedPlatform;
    if (platformId && !options.templates) installTemplates = true;
  }

  // Compute destinations
  let skillDest;
  if (installScope === 'repo') {
    if (!workspaceRoot) {
      throw new Error('Repo install selected but no workspace root found. Run in a git repo or pass --root <path>.');
    }
    skillDest = defaultProjectSkillPath(workspaceRoot, { claude: options.claude });
  } else {
    skillDest = defaultPersonalSkillPath({ claude: options.claude });
  }

  // Preflight
  const actions = [];
  actions.push({ kind: 'skill', from: payloadSkillDir, to: skillDest });

  let templatesDir = null;
  if (platformId && installTemplates) {
    templatesDir = path.join(payloadSkillDir, 'platforms', platformId, 'templates');
    if (!(await isDirectory(templatesDir))) {
      templatesDir = null;
    } else if (!workspaceRoot) {
      // If personal scope but we still want templates, default to current directory.
      workspaceRoot = process.cwd();
    }
    if (templatesDir && workspaceRoot) {
      actions.push({ kind: 'templates', from: templatesDir, to: workspaceRoot });
    }
  }

  if (options.dryRun) {
    console.log('Dry run — planned actions:');
    for (const a of actions) {
      console.log(`- ${a.kind}: ${a.from} -> ${a.to}`);
    }
    return;
  }

  // Execute
  for (const a of actions) {
    const destExists = await pathExists(a.to);
    if (destExists && !options.force) {
      if (!options.yes && isTTY()) {
        const ok = await confirm({
          message: `Destination already exists: ${a.to}\nOverwrite?`,
          default: false,
        });
        if (!ok) {
          console.log('Cancelled.');
          return;
        }
      } else {
        throw new Error(`Destination exists: ${a.to} (use --force to overwrite)`);
      }
    }

    if (destExists && options.force) {
      await removeDir(a.to);
    }

    await ensureDir(path.dirname(a.to));

    if (a.kind === 'skill') {
      await copyDir(a.from, a.to);
      console.log(`Installed APS skill -> ${a.to}`);
    } else if (a.kind === 'templates') {
      await copyTemplates(a.from, a.to, { force: options.force });
      console.log(`Applied platform templates -> ${a.to}`);
    }
  }

  console.log('\nNext steps (VS Code):');
  console.log('- Ensure VS Code has Agent Skills + instruction files enabled as needed.');
  console.log(`- Skill location: ${skillDest}`);
}

async function runDoctor(options) {
  const root = await pickWorkspaceRoot(options.root);
  const detected = root ? inferPlatformId(root) : null;

  const rows = [];

  if (root) {
    const repoSkill = defaultProjectSkillPath(root, { claude: false });
    const repoSkillClaude = defaultProjectSkillPath(root, { claude: true });
    rows.push(['repo', repoSkill, await pathExists(path.join(repoSkill, 'SKILL.md'))]);
    rows.push(['repo (claude)', repoSkillClaude, await pathExists(path.join(repoSkillClaude, 'SKILL.md'))]);
  }

  const personalSkill = defaultPersonalSkillPath({ claude: false });
  const personalSkillClaude = defaultPersonalSkillPath({ claude: true });
  rows.push(['personal', personalSkill, await pathExists(path.join(personalSkill, 'SKILL.md'))]);
  rows.push(['personal (claude)', personalSkillClaude, await pathExists(path.join(personalSkillClaude, 'SKILL.md'))]);

  console.log('APS Doctor');
  console.log('----------');
  console.log(`Workspace root: ${root ?? '(not detected)'}`);
  console.log(`Detected platform: ${detected ?? '(none)'}`);
  console.log('');
  console.log('Installed skills:');
  for (const [scope, p, ok] of rows) {
    console.log(`- ${scope}: ${p} ${ok ? '✓' : '✗'}`);
  }
}

export async function main(argv) {
  const program = new Command();
  program
    .name('aps')
    .description('Install and manage the Agnostic Prompt Standard (APS) skill.')
    .version('1.1.1');

  program
    .command('init')
    .description('Install APS skill + (optionally) platform templates')
    .option('--root <path>', 'Workspace root path (defaults to git repo root if found)')
    .option('--repo', 'Install as a project skill (under .github/skills)')
    .option('--personal', 'Install as a personal skill (under ~/.copilot/skills)')
    .option('--platform <id>', 'Platform adapter to apply (e.g. vscode-copilot). Use "none" to skip.')
    .option('--templates', 'Apply platform templates (default true when a platform is selected)')
    .option('--claude', 'Use Claude platform .claude/skills paths instead of .github/skills and ~/.copilot/skills', false)
    .option('-y, --yes', 'Non-interactive; accept defaults', false)
    .option('-f, --force', 'Overwrite existing files', false)
    .option('--dry-run', 'Print planned actions without writing', false)
    .action((opts) => runInit(opts).catch((e) => {
      console.error(`Error: ${e.message ?? e}`);
      process.exit(1);
    }));

  program
    .command('doctor')
    .description('Check APS installation status + basic platform detection')
    .option('--root <path>', 'Workspace root path (defaults to git repo root if found)')
    .action((opts) => runDoctor(opts).catch((e) => {
      console.error(`Error: ${e.message ?? e}`);
      process.exit(1);
    }));

  program
    .command('info')
    .description('Print bundled APS payload info')
    .action(async () => {
      const payloadSkillDir = await resolvePayloadSkillDir();
      const platforms = await loadPlatforms(payloadSkillDir);
      console.log(`CLI version: 1.1.1`);
      console.log(`Bundled skill path: ${payloadSkillDir}`);
      console.log('Platforms:');
      for (const p of platforms) {
        console.log(`- ${p.platformId}: ${p.displayName} (templates: ${p.hasTemplates ? 'yes' : 'no'})`);
      }
    });

  await program.parseAsync(argv);

  // If no command was provided, show help and exit with usage.
  if (!program.args.length) {
    program.help({ error: true });
    process.exit(EXIT_USAGE);
  }
}
