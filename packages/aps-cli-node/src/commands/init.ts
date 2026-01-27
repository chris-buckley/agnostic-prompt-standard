import path from 'node:path';

import { confirm, select, input, checkbox } from '@inquirer/prompts';

import {
  SKILL_ID,
  copyDir,
  copyTemplateTree,
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  ensureDir,
  expandHome,
  findRepoRoot,
  homeDir,
  isDirectory,
  listFilesRecursive,
  pathExists,
  pickWorkspaceRoot,
  removeDir,
  resolvePayloadSkillDir,
} from '../core.js';
import {
  detectAdapters,
  formatDetectionLabel,
  loadPlatformsWithMarkers,
  sortPlatformsForUi,
  type AdapterDetection,
  type PlatformWithMarkers,
} from '../detection/adapters.js';

export interface InitOptions {
  root?: string;
  repo?: boolean;
  personal?: boolean;
  platform?: string[];
  yes?: boolean;
  force?: boolean;
  dryRun?: boolean;
}

type InstallScope = 'repo' | 'personal';

interface PlannedTemplateFile {
  relPath: string;
  dstPath: string;
  exists: boolean;
  willWrite: boolean;
}

interface PlannedPlatformTemplates {
  platformId: string;
  templatesDir: string;
  templateRoot: string;
  files: PlannedTemplateFile[];
}

interface PlannedSkillInstall {
  dst: string;
  exists: boolean;
}

interface InitPlan {
  scope: InstallScope;
  workspaceRoot: string | null;
  selectedPlatforms: string[];
  payloadSkillDir: string;
  skills: PlannedSkillInstall[];
  templates: PlannedPlatformTemplates[];
}

function fmtPath(p: string): string {
  const home = homeDir();
  if (p === home) return '~';
  if (p.startsWith(home + path.sep)) return `~${p.slice(home.length)}`;
  return p;
}

function selectAllChoiceLabel(): string {
  return 'Select all adapters';
}

function platformDisplayName(platformId: string, platformsById: Map<string, string>): string {
  const display = platformsById.get(platformId);
  return display ? `${display} (${platformId})` : platformId;
}

function detectionFor(platformId: string, detections: Record<string, AdapterDetection> | null): AdapterDetection | null {
  return detections?.[platformId] ?? null;
}

function normalizePlatformArgs(platformArgs: string[] | undefined): string[] | null {
  if (!platformArgs || platformArgs.length === 0) return null;

  const raw = platformArgs
    .flatMap((v) => v.split(','))
    .map((v) => v.trim())
    .filter(Boolean);

  if (raw.some((v) => v.toLowerCase() === 'none')) return [];

  const out: string[] = [];
  const seen = new Set<string>();
  for (const v of raw) {
    if (!seen.has(v)) {
      seen.add(v);
      out.push(v);
    }
  }
  return out;
}

function isClaudePlatform(platformId: string): boolean {
  return platformId === 'claude-code';
}

function computeSkillDestinations(scope: InstallScope, workspaceRoot: string | null, selectedPlatforms: string[]): string[] {
  const wantsClaude = selectedPlatforms.some((p) => isClaudePlatform(p));
  const wantsNonClaude = selectedPlatforms.some((p) => !isClaudePlatform(p)) || selectedPlatforms.length === 0;

  const out: string[] = [];
  if (scope === 'repo') {
    if (!workspaceRoot) throw new Error('workspaceRoot required for repo scope');
    if (wantsNonClaude) out.push(defaultProjectSkillPath(workspaceRoot, { claude: false }));
    if (wantsClaude) out.push(defaultProjectSkillPath(workspaceRoot, { claude: true }));
  } else {
    if (wantsNonClaude) out.push(defaultPersonalSkillPath({ claude: false }));
    if (wantsClaude) out.push(defaultPersonalSkillPath({ claude: true }));
  }
  return out;
}

function buildPlatformsById(payloadPlatforms: readonly { platformId: string; displayName: string }[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const p of payloadPlatforms) map.set(p.platformId, p.displayName);
  return map;
}

async function planPlatformTemplates(
  payloadSkillDir: string,
  scope: InstallScope,
  workspaceRoot: string | null,
  selectedPlatforms: string[],
  force: boolean
): Promise<PlannedPlatformTemplates[]> {
  const templateRoot = scope === 'personal' ? homeDir() : workspaceRoot;
  if (!templateRoot) return [];

  const plans: PlannedPlatformTemplates[] = [];

  for (const platformId of selectedPlatforms) {
    const templatesDir = path.join(payloadSkillDir, 'platforms', platformId, 'templates');
    if (!(await isDirectory(templatesDir))) continue;

    const allFiles = await listFilesRecursive(templatesDir);

    const filter = (relPath: string): boolean => {
      if (scope === 'personal' && relPath.startsWith('.github')) return false;
      return true;
    };

    const files: PlannedTemplateFile[] = [];
    for (const src of allFiles) {
      const relPath = path.relative(templatesDir, src).split(path.sep).join('/');
      if (!filter(relPath)) continue;

      const dstPath = path.join(templateRoot, relPath);
      const exists = await pathExists(dstPath);
      files.push({
        relPath,
        dstPath,
        exists,
        willWrite: !exists || force,
      });
    }

    plans.push({
      platformId,
      templatesDir,
      templateRoot,
      files,
    });
  }

  return plans;
}

function renderPlan(plan: InitPlan, force: boolean): string {
  const lines: string[] = [];

  lines.push('Selected adapters:');
  if (plan.selectedPlatforms.length === 0) {
    lines.push('  (none)');
  } else {
    for (const p of plan.selectedPlatforms) lines.push(`  - ${p}`);
  }
  lines.push('');

  lines.push('Skill install destinations:');
  for (const s of plan.skills) {
    const status = s.exists ? (force ? 'overwrite' : 'overwrite (needs confirmation)') : 'create';
    lines.push(`  - ${fmtPath(s.dst)}  [${status}]`);
  }
  lines.push('');

  if (plan.templates.length === 0) {
    lines.push('Platform templates: (none)');
    return lines.join('\n');
  }

  lines.push('Platform templates:');
  for (const t of plan.templates) {
    const willWrite = t.files.filter((f) => f.willWrite).length;
    const skipped = t.files.length - willWrite;
    const skipMsg = skipped > 0 ? `, ${skipped} skipped (exists)` : '';
    lines.push(`  - ${t.platformId}: ${willWrite} file(s) to write${skipMsg}`);

    const preview = t.files.filter((f) => f.willWrite).slice(0, 30);
    for (const f of preview) lines.push(`      ${f.relPath}`);
    if (willWrite > 30) lines.push('      ...');
  }

  return lines.join('\n');
}

export async function runInit(options: InitOptions): Promise<void> {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const repoRoot = await findRepoRoot(process.cwd());
  const guessedWorkspaceRoot = await pickWorkspaceRoot(options.root);

  const platformsWithMarkers = sortPlatformsForUi(await loadPlatformsWithMarkers(payloadSkillDir));
  const platformsById = buildPlatformsById(platformsWithMarkers);
  const availablePlatformIds = platformsWithMarkers.map((p) => p.platformId);

  const detections = guessedWorkspaceRoot ? await detectAdapters(guessedWorkspaceRoot, platformsWithMarkers) : null;

  const cliPlatforms = normalizePlatformArgs(options.platform);
  const yes = Boolean(options.yes);
  const force = Boolean(options.force);
  const dryRun = Boolean(options.dryRun);

  // Determine platform selection
  let selectedPlatforms: string[] = [];

  if (cliPlatforms !== null) {
    selectedPlatforms = cliPlatforms;
  } else if (!yes && process.stdout.isTTY) {
    const choices = [
      {
        name: selectAllChoiceLabel(),
        value: '__all__',
        checked: false,
      },
      ...availablePlatformIds.map((platformId) => {
        const det = detectionFor(platformId, detections);
        const label = det ? formatDetectionLabel(det) : '';
        const checked = Boolean(det?.detected);
        return {
          name: `${platformDisplayName(platformId, platformsById)}${label}`,
          value: platformId,
          checked,
        };
      }),
    ];

    const picked = await checkbox({
      message: 'Select platform adapters to apply (press <space> to select, <a> to toggle all):',
      choices,
    });

    const hasAll = picked.includes('__all__');
    const pickedPlatforms = picked.filter((p) => p !== '__all__');

    if (hasAll && pickedPlatforms.length === 0) {
      selectedPlatforms = [...availablePlatformIds];
    } else {
      selectedPlatforms = pickedPlatforms;
    }
  } else {
    if (yes && detections) {
      selectedPlatforms = availablePlatformIds.filter((platformId) => {
        const det = detectionFor(platformId, detections);
        return Boolean(det?.detected);
      });
    } else {
      selectedPlatforms = [];
    }
  }

  // Determine scope
  let installScope: InstallScope;
  if (options.personal) installScope = 'personal';
  else if (options.repo) installScope = 'repo';
  else installScope = repoRoot ? 'repo' : 'personal';

  let workspaceRoot: string | null = guessedWorkspaceRoot;

  if (!yes && process.stdout.isTTY) {
    if (!options.repo && !options.personal) {
      const personalBases = new Set<string>();
      const wantsClaude = selectedPlatforms.some((p) => isClaudePlatform(p));
      const wantsNonClaude = selectedPlatforms.some((p) => !isClaudePlatform(p)) || selectedPlatforms.length === 0;

      if (wantsNonClaude) {
        personalBases.add(fmtPath(defaultPersonalSkillPath({ claude: false }).replace(SKILL_ID, '')));
      }
      if (wantsClaude) {
        personalBases.add(fmtPath(defaultPersonalSkillPath({ claude: true }).replace(SKILL_ID, '')));
      }

      installScope = await select({
        message: 'Where should APS be installed?',
        choices: [
          {
            name: repoRoot ? `Project skill in this repo (${fmtPath(repoRoot)})` : 'Project skill (choose a workspace folder)',
            value: 'repo',
          },
          {
            name: `Personal skill for your user (${[...personalBases].sort().join(', ')})`,
            value: 'personal',
          },
        ],
        default: repoRoot ? 'repo' : 'personal',
      });
    }

    if (installScope === 'repo' && !workspaceRoot) {
      const rootAnswer = await input({
        message: 'Workspace root path (the folder that contains .github/):',
        default: process.cwd(),
      });
      workspaceRoot = path.resolve(expandHome(rootAnswer));
    }
  }

  if (installScope === 'repo' && !workspaceRoot) {
    throw new Error('Repo install selected but no workspace root found. Run in a git repo or pass --root <path>.');
  }

  const skillDests = computeSkillDestinations(installScope, workspaceRoot, selectedPlatforms);
  const skills: PlannedSkillInstall[] = await Promise.all(
    skillDests.map(async (dst) => ({
      dst,
      exists: await pathExists(dst),
    }))
  );

  const templates = await planPlatformTemplates(payloadSkillDir, installScope, workspaceRoot, selectedPlatforms, force);

  const plan: InitPlan = {
    scope: installScope,
    workspaceRoot,
    selectedPlatforms,
    payloadSkillDir,
    skills,
    templates,
  };

  if (dryRun) {
    console.log('Dry run — planned actions:\n');
    console.log(renderPlan(plan, force));
    return;
  }

  if (!yes && process.stdout.isTTY) {
    console.log(renderPlan(plan, force));
    console.log('');

    if (skills.some((s) => s.exists) && !force) {
      console.log('Note: One or more skill destinations already exist. Confirming will overwrite them.');
    }

    const ok = await confirm({ message: 'Proceed with these changes?', default: false });
    if (!ok) {
      console.log('Cancelled.');
      return;
    }
  } else {
    const conflicts = skills.filter((s) => s.exists);
    if (conflicts.length > 0 && !force) {
      throw new Error(`Destination exists: ${conflicts[0]?.dst} (use --force to overwrite)`);
    }
  }

  for (const s of skills) {
    if (s.exists) {
      if (force || (!yes && process.stdout.isTTY)) {
        await removeDir(s.dst);
      }
    }
    await ensureDir(path.dirname(s.dst));
    await copyDir(payloadSkillDir, s.dst);
    console.log(`Installed APS skill -> ${s.dst}`);
  }

  for (const t of templates) {
    const copied = await copyTemplateTree(t.templatesDir, t.templateRoot, {
      force,
      filter: (relPath) => {
        if (installScope === 'personal' && relPath.startsWith('.github')) return false;
        return true;
      },
    });

    if (copied.length > 0) {
      console.log(`Installed ${copied.length} template file(s) for ${t.platformId}:`);
      for (const f of copied) console.log(`  - ${f}`);
    }
  }

  console.log('\nNext steps:');
  console.log('- Ensure your IDE has Agent Skills enabled as needed.');
  for (const d of skillDests) console.log(`- Skill location: ${d}`);
}
