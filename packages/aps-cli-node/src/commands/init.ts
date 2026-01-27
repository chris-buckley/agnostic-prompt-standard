import path from 'node:path';
import process from 'node:process';

import { checkbox, confirm, input, select } from '@inquirer/prompts';

import {
  SKILL_ID,
  copyDir,
  copyTemplateTree,
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  ensureDir,
  findRepoRoot,
  homeDir,
  isDirectory,
  listFilesRecursive,
  loadPlatforms,
  pathExists,
  pickWorkspaceRoot,
  removeDir,
  resolvePayloadSkillDir,
} from '../core.js';
import {
  DEFAULT_ADAPTER_ORDER,
  detectAdapters,
  formatDetectionLabel,
  loadPlatformsWithMarkers,
  type AdapterDetection,
  type KnownAdapterId,
  type PlatformWithMarkers,
} from '../detection/adapters.js';

export interface InitCliOptions {
  root?: string;
  repo?: boolean;
  personal?: boolean;
  platform?: string[];
  yes: boolean;
  force: boolean;
  dryRun: boolean;
}

type InstallScope = 'repo' | 'personal';

function isTTY(): boolean {
  return Boolean(process.stdout.isTTY && process.stdin.isTTY);
}

function fmtPath(p: string): string {
  return p.replace(process.env.HOME ?? '', '~');
}

function normalizePlatformArgs(platform: string[] | undefined): string[] | undefined {
  if (!platform || platform.length === 0) return undefined;
  const raw = platform.flatMap((v) => v.split(',')).map((s) => s.trim()).filter(Boolean);
  if (raw.some((v) => v.toLowerCase() === 'none')) return [];
  // De-duplicate while preserving order
  const seen = new Set<string>();
  const out: string[] = [];
  for (const v of raw) {
    if (seen.has(v)) continue;
    seen.add(v);
    out.push(v);
  }
  return out;
}

function unique<T>(items: readonly T[]): T[] {
  const out: T[] = [];
  const seen = new Set<T>();
  for (const i of items) {
    if (seen.has(i)) continue;
    seen.add(i);
    out.push(i);
  }
  return out;
}

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

function isClaudePlatform(platformId: string): boolean {
  return platformId === 'claude-code';
}

function computeSkillDestinations(
  scope: InstallScope,
  workspaceRoot: string | null,
  selectedPlatforms: readonly string[]
): string[] {
  const wantsClaude = selectedPlatforms.some((p) => isClaudePlatform(p));
  const wantsNonClaude = selectedPlatforms.some((p) => !isClaudePlatform(p));

  // If no adapters are selected, default to non-Claude location (historical behaviour).
  const includeClaude = wantsClaude;
  const includeNonClaude = wantsNonClaude || selectedPlatforms.length === 0;

  if (scope === 'repo') {
    if (!workspaceRoot) throw new Error('Repo install selected but no workspace root found.');
    const dests: string[] = [];
    if (includeNonClaude) dests.push(defaultProjectSkillPath(workspaceRoot, { claude: false }));
    if (includeClaude) dests.push(defaultProjectSkillPath(workspaceRoot, { claude: true }));
    return unique(dests);
  }

  const dests: string[] = [];
  if (includeNonClaude) dests.push(defaultPersonalSkillPath({ claude: false }));
  if (includeClaude) dests.push(defaultPersonalSkillPath({ claude: true }));
  return unique(dests);
}

async function planPlatformTemplates(
  payloadSkillDir: string,
  scope: InstallScope,
  workspaceRoot: string | null,
  selectedPlatforms: readonly string[],
  opts: { force: boolean }
): Promise<PlannedPlatformTemplates[]> {
  const templateRoot = scope === 'personal' ? homeDir() : workspaceRoot;
  if (!templateRoot) return [];

  const plans: PlannedPlatformTemplates[] = [];

  for (const platformId of selectedPlatforms) {
    const templatesDir = path.join(payloadSkillDir, 'platforms', platformId, 'templates');
    if (!(await isDirectory(templatesDir))) continue;

    const allFiles = await listFilesRecursive(templatesDir);

    const filter = (relPath: string): boolean => {
      // Skip .github/** for personal installs (avoid writing repo structures into home dir).
      if (scope === 'personal' && relPath.startsWith('.github')) return false;
      return true;
    };

    const files: PlannedTemplateFile[] = [];
    for (const src of allFiles) {
      const relPath = path.relative(templatesDir, src);
      if (!filter(relPath)) continue;

      const dstPath = path.join(templateRoot, relPath);
      const exists = await pathExists(dstPath);
      files.push({
        relPath,
        dstPath,
        exists,
        willWrite: !exists || opts.force,
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

function renderPlan(plan: InitPlan, opts: { force: boolean }): string {
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
    const status = s.exists ? (opts.force ? 'overwrite' : 'overwrite (needs confirmation)') : 'create';
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
    lines.push(`  - ${t.platformId}: ${willWrite} file(s) to write${skipped > 0 ? `, ${skipped} skipped (exists)` : ''}`);

    const preview = t.files
      .filter((f) => f.willWrite)
      .slice(0, 30)
      .map((f) => `      ${path.relative(t.templateRoot, f.dstPath)}`);

    for (const p of preview) lines.push(p);
    if (willWrite > 30) lines.push('      ...');
  }

  return lines.join('\n');
}

function selectAllChoiceLabel(): string {
  return 'Select all adapters';
}

function platformDisplayName(platformId: string, platformsById: Map<string, string>): string {
  return platformsById.get(platformId) ?? platformId;
}

function buildPlatformsById(payloadPlatforms: readonly { platformId: string; displayName: string }[]): Map<string, string> {
  const m = new Map<string, string>();
  for (const p of payloadPlatforms) m.set(p.platformId, p.displayName);
  return m;
}

function sortPlatformsForUi(available: readonly string[]): string[] {
  const known = new Set(DEFAULT_ADAPTER_ORDER as readonly string[]);
  const orderedKnown = DEFAULT_ADAPTER_ORDER.filter((id) => available.includes(id));
  const remaining = available.filter((id) => !known.has(id)).sort((a, b) => a.localeCompare(b));
  return [...orderedKnown, ...remaining];
}

function detectionFor(platformId: string, detections: Record<string, AdapterDetection> | null): AdapterDetection | null {
  if (!detections) return null;
  return detections[platformId] ?? null;
}

export async function runInit(options: InitCliOptions): Promise<void> {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const repoRoot = await findRepoRoot(process.cwd());
  const guessedWorkspaceRoot = await pickWorkspaceRoot(options.root);

  const platformsWithMarkers = await loadPlatformsWithMarkers(payloadSkillDir);
  const platformsById = buildPlatformsById(platformsWithMarkers);
  const availablePlatformIds = sortPlatformsForUi(platformsWithMarkers.map((p) => p.platformId));

  const detections = guessedWorkspaceRoot ? await detectAdapters(guessedWorkspaceRoot, platformsWithMarkers) : null;

  const cliPlatforms = normalizePlatformArgs(options.platform);

  // Determine platform selection
  let selectedPlatforms: string[] = [];

  if (cliPlatforms !== undefined) {
    selectedPlatforms = cliPlatforms;
  } else if (!options.yes && isTTY()) {
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
          name: `${platformDisplayName(platformId, platformsById)} (${platformId})${label}`,
          value: platformId,
          checked,
        };
      }),
    ];

    const picked = await checkbox({
      message: 'Select platform adapters to apply (press <space> to select, <a> to toggle all):',
      choices,
      required: false,
      pageSize: Math.min(12, choices.length),
    });

    const hasAll = picked.includes('__all__');
    const pickedPlatforms = picked.filter((p) => p !== '__all__');

    if (hasAll && pickedPlatforms.length === 0) {
      selectedPlatforms = [...availablePlatformIds];
    } else {
      selectedPlatforms = pickedPlatforms;
    }
  } else {
    // Non-interactive defaults
    if (options.yes && detections) {
      selectedPlatforms = availablePlatformIds.filter((id) => {
        const det = detectionFor(id, detections);
        return Boolean(det?.detected);
      });
    } else {
      selectedPlatforms = [];
    }
  }

  // Determine scope
  let installScope: InstallScope | undefined = options.personal ? 'personal' : options.repo ? 'repo' : undefined;
  let workspaceRoot: string | null = guessedWorkspaceRoot;

  if (!options.yes && isTTY()) {
    if (!installScope) {
      const personalBases = new Set<string>();
      // Describe likely destinations based on selection.
      const wantsClaude = selectedPlatforms.some((p) => isClaudePlatform(p));
      const wantsNonClaude = selectedPlatforms.some((p) => !isClaudePlatform(p)) || selectedPlatforms.length === 0;
      if (wantsNonClaude) {
        personalBases.add(fmtPath(defaultPersonalSkillPath({ claude: false }).replace(SKILL_ID, '')));      }
      if (wantsClaude) {
        personalBases.add(fmtPath(defaultPersonalSkillPath({ claude: true }).replace(SKILL_ID, '')));      }

      installScope = await select({
        message: 'Where should APS be installed?',
        default: repoRoot ? 'repo' : 'personal',
        choices: [
          {
            name: repoRoot
              ? `Project skill in this repo (${fmtPath(repoRoot)})`
              : 'Project skill (choose a workspace folder)',
            value: 'repo',
          },
          {
            name: `Personal skill for your user (${Array.from(personalBases).join(', ')})`,
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
  } else {
    if (!installScope) installScope = repoRoot ? 'repo' : 'personal';
  }

  if (installScope === 'repo' && !workspaceRoot) {
    throw new Error('Repo install selected but no workspace root found. Run in a git repo or pass --root <path>.');
  }

  const skillDests = computeSkillDestinations(installScope, workspaceRoot, selectedPlatforms);
  const skills: PlannedSkillInstall[] = [];
  for (const dst of skillDests) {
    const exists = await pathExists(dst);
    skills.push({ dst, exists });
  }

  const templates = await planPlatformTemplates(payloadSkillDir, installScope, workspaceRoot, selectedPlatforms, {
    force: options.force,
  });

  const plan: InitPlan = {
    scope: installScope,
    workspaceRoot,
    selectedPlatforms,
    payloadSkillDir,
    skills,
    templates,
  };

  if (options.dryRun) {
    console.log('Dry run — planned actions:\n');
    console.log(renderPlan(plan, { force: options.force }));
    return;
  }

  if (!options.yes && isTTY()) {
    console.log(renderPlan(plan, { force: options.force }));
    console.log('');

    if (skills.some((s) => s.exists) && !options.force) {
      console.log('Note: One or more skill destinations already exist. Confirming will overwrite them.');
    }

    const ok = await confirm({
      message: 'Proceed with these changes?',
      default: false,
    });
    if (!ok) {
      console.log('Cancelled.');
      return;
    }
  } else {
    // Non-interactive: refuse to overwrite without --force
    const conflicts = skills.filter((s) => s.exists);
    const firstConflict = conflicts[0];
    if (firstConflict && !options.force) {
      throw new Error(`Destination exists: ${firstConflict.dst} (use --force to overwrite)`);
    }
  }

  // Execute skill copies
  for (const s of skills) {
    const dstExists = await pathExists(s.dst);

    if (dstExists) {
      if (options.force) {
        await removeDir(s.dst);
      } else if (isTTY() && !options.yes) {
        // Overwrite was confirmed in the summary prompt.
        await removeDir(s.dst);
      }
    }

    await ensureDir(path.dirname(s.dst));
    await copyDir(payloadSkillDir, s.dst);
    console.log(`Installed APS skill -> ${s.dst}`);
  }

  // Copy templates (if platform has templates)
  for (const t of templates) {
    const filter = (relPath: string): boolean => {
      if (installScope === 'personal' && relPath.startsWith('.github')) return false;
      return true;
    };

    const copied = await copyTemplateTree(t.templatesDir, t.templateRoot, {
      force: options.force,
      filter,
    });

    if (copied.length > 0) {
      console.log(`Installed ${copied.length} template file(s) for ${t.platformId}:`);
      for (const f of copied) {
        console.log(`  - ${f}`);
      }
    }
  }

  console.log('\nNext steps:');
  console.log('- Ensure your IDE has Agent Skills enabled as needed.');
  for (const d of skillDests) {
    console.log(`- Skill location: ${d}`);
  }
}