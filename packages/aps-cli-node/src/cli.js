import { Command } from 'commander';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import {
  confirm,
  input,
  select,
} from '@inquirer/prompts';

import {
  SKILL_ID,
  copyDir,
  copyTemplateTree,
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  ensureDir,
  findRepoRoot,
  homeDir,
  inferPlatformId,
  isDirectory,
  pathExists,
  removeDir,
  resolvePayloadSkillDir,
  loadPlatforms,
} from './core.js';

const require = createRequire(import.meta.url);
const pkg = require('../package.json');

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

function isClaudePlatform(platformId) {
  return platformId === 'claude-code';
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

  if (!options.yes && isTTY()) {
    // Platform selection (first, so platform choice can inform installation location)
    if (!platformId) {
      const platforms = await loadPlatforms(payloadSkillDir);
      const choices = [
        ...(detectedPlatform ? [{ name: `Auto-detected: ${detectedPlatform}`, value: detectedPlatform }] : []),
        { name: 'None (skip platform adapter)', value: null },
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

    // Scope prompt
    if (!installScope) {
      const claude = isClaudePlatform(platformId);
      installScope = await select({
        message: 'Where should APS be installed?',
        default: repoRoot ? 'repo' : 'personal',
        choices: [
          {
            name: repoRoot ? `Project skill in this repo (${fmtPath(repoRoot)})` : 'Project skill (choose a workspace folder)',
            value: 'repo',
          },
          {
            name: `Personal skill for your user (${fmtPath(defaultPersonalSkillPath({ claude }).replace(SKILL_ID, ''))})`,
            value: 'personal',
          },
        ],
      });
    }

    // Workspace root (only needed for repo scope)
    if (installScope === 'repo' && !workspaceRoot) {
      const rootAnswer = await input({
        message: 'Workspace root path (the folder that contains .github/):',
        default: process.cwd(),
      });
      workspaceRoot = path.resolve(rootAnswer);
    }
  } else {
    // Non-interactive defaults
    if (!installScope) installScope = repoRoot ? 'repo' : 'personal';
    if (!platformId && workspaceRoot) platformId = detectedPlatform;
  }

  // Compute destinations
  const claude = isClaudePlatform(platformId);
  let skillDest;
  if (installScope === 'repo') {
    if (!workspaceRoot) {
      throw new Error('Repo install selected but no workspace root found. Run in a git repo or pass --root <path>.');
    }
    skillDest = defaultProjectSkillPath(workspaceRoot, { claude });
  } else {
    skillDest = defaultPersonalSkillPath({ claude });
  }

  // Preflight
  const actions = [];
  actions.push({ kind: 'skill', from: payloadSkillDir, to: skillDest });

  // Determine template source if platform is set
  let templatesDir = null;
  let templateRoot = null;
  if (platformId) {
    templatesDir = path.join(payloadSkillDir, 'platforms', platformId, 'templates');
    if (await isDirectory(templatesDir)) {
      templateRoot = installScope === 'personal' ? homeDir() : workspaceRoot;
      actions.push({ kind: 'templates', from: templatesDir, to: templateRoot });
    } else {
      templatesDir = null;
    }
  }

  if (options.dryRun) {
    console.log('Dry run — planned actions:');
    for (const a of actions) {
      console.log(`- ${a.kind}: ${a.from} -> ${a.to}`);
    }
    return;
  }

  // Execute skill copy
  const skillAction = actions.find((a) => a.kind === 'skill');
  if (skillAction) {
    const destExists = await pathExists(skillAction.to);
    if (destExists && !options.force) {
      if (!options.yes && isTTY()) {
        const ok = await confirm({
          message: `Destination already exists: ${skillAction.to}\nOverwrite?`,
          default: false,
        });
        if (!ok) {
          console.log('Cancelled.');
          return;
        }
      } else {
        throw new Error(`Destination exists: ${skillAction.to} (use --force to overwrite)`);
      }
    }

    if (destExists && options.force) {
      await removeDir(skillAction.to);
    }

    await ensureDir(path.dirname(skillAction.to));
    await copyDir(skillAction.from, skillAction.to);
    console.log(`Installed APS skill -> ${skillAction.to}`);
  }

  // Copy templates (if platform has templates)
  if (templatesDir && templateRoot) {
    const filter = (relPath) => {
      // Skip .github/** for personal installs (shouldn't put .github in home dir)
      if (installScope === 'personal' && relPath.startsWith('.github')) {
        return false;
      }
      return true;
    };
    const copied = await copyTemplateTree(templatesDir, templateRoot, {
      force: options.force,
      filter,
    });
    if (copied.length > 0) {
      console.log(`Installed ${copied.length} template file(s):`);
      for (const f of copied) {
        console.log(`  - ${f}`);
      }
    }
  }

  console.log('\nNext steps:');
  console.log('- Ensure your IDE has Agent Skills enabled as needed.');
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

  const result = {
    workspace_root: root ?? null,
    detected_platform: detected ?? null,
    installations: rows.map(([scope, p, ok]) => ({ scope, path: p, installed: ok })),
  };

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

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

async function runPlatforms() {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const platforms = await loadPlatforms(payloadSkillDir);
  console.log('Available platform adapters:');
  for (const p of platforms) {
    console.log(`- ${p.platformId}: ${p.displayName} (v${p.adapterVersion ?? 'unknown'})`);
  }
}

export async function main(argv) {
  const program = new Command();
  program
    .name('aps')
    .description('Install and manage the Agnostic Prompt Standard (APS) skill.')
    .version(pkg.version);

  program
    .command('init')
    .description('Install APS skill')
    .option('--root <path>', 'Workspace root path (defaults to git repo root if found)')
    .option('--repo', 'Install as a project skill (under .github/skills or .claude/skills)')
    .option('--personal', 'Install as a personal skill (under ~/.copilot/skills or ~/.claude/skills)')
    .option('--platform <id>', 'Platform adapter to apply (e.g. vscode-copilot, claude-code). Use "none" to skip.')
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
    .option('--json', 'Output JSON format', false)
    .action((opts) => runDoctor(opts).catch((e) => {
      console.error(`Error: ${e.message ?? e}`);
      process.exit(1);
    }));

  program
    .command('platforms')
    .description('List available platform adapters')
    .action(() => runPlatforms().catch((e) => {
      console.error(`Error: ${e.message ?? e}`);
      process.exit(1);
    }));

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
