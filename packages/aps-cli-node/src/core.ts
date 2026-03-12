// Core platform/tool detection and loading logic for APS CLI

import { randomUUID } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { existsSync, type Dirent } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { parseAdaptorMd, getString, getStringArray } from './parsers/adaptor.js';

export const APS_PAYLOAD_SKILL_DIR = 'skill/agnostic-prompt-standard';
export const SKILL_ID = 'agnostic-prompt-standard' as const;

/**
 * Determine if a path exists.
 */
export async function pathExists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

/**
 * Determine if a path is a directory.
 */
export async function isDirectory(p: string): Promise<boolean> {
  try {
    const stat = await fs.stat(p);
    return stat.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Resolve the APS skill directory.
 *
 * Resolution order:
 * 1) Bundled package payload (works for `npx @agnostic-prompt/aps ...`)
 * 2) Monorepo dev layout relative to cwd
 */
export async function resolvePayloadSkillDir(): Promise<string> {
  // Packaged payload (dist/.. -> payload/<skill>)
  const here = path.dirname(fileURLToPath(import.meta.url));
  const packaged = path.resolve(here, '..', 'payload', SKILL_ID);
  if (await isDirectory(packaged)) return packaged;

  // Monorepo/dev fallback: look relative to where the user invoked the CLI.
  const cwd = process.cwd();
  const candidate = path.join(cwd, APS_PAYLOAD_SKILL_DIR);
  if (await isDirectory(candidate)) return candidate;

  const up = path.resolve(cwd, '..', '..', APS_PAYLOAD_SKILL_DIR);
  if (await isDirectory(up)) return up;

  throw new Error(`Cannot locate payload skill directory. Tried: ${packaged}, ${candidate}, ${up}`);
}

/**
 * Get default personal skill path for a given platform.
 */
export function defaultPersonalSkillPath(opts: { claude?: boolean } = {}): string {
  if (opts.claude) return path.join(os.homedir(), '.claude', 'skills', 'agnostic-prompt-standard');
  return path.join(os.homedir(), '.copilot', 'skills', 'agnostic-prompt-standard');
}

/**
 * Get default project skill path for a given workspace root.
 */
export function defaultProjectSkillPath(workspaceRoot: string, opts: { claude?: boolean } = {}): string {
  if (opts.claude) return path.join(workspaceRoot, '.claude', 'skills', 'agnostic-prompt-standard');
  return path.join(workspaceRoot, '.github', 'skills', 'agnostic-prompt-standard');
}

/**
 * Check if a platform uses Claude-specific install paths.
 */
export function isClaudePlatform(platformId: string): boolean {
  return platformId === 'claude-code';
}

/**
 * Check if a platform is install-family neutral.
 */
export function isGenericPlatform(platformId: string): boolean {
  return platformId === 'generic';
}

/**
 * Compute which install families are required for a selection of platform adapters.
 * Neutral adapters such as `generic` do not force a concrete install family.
 */
export function computeInstallFamilies(
  selectedPlatforms: readonly string[]
): { includeClaude: boolean; includeNonClaude: boolean } {
  const concretePlatforms = selectedPlatforms.filter((p) => !isGenericPlatform(p));
  const wantsClaude = concretePlatforms.some((p) => isClaudePlatform(p));
  const wantsNonClaude = concretePlatforms.some((p) => !isClaudePlatform(p));

  return {
    includeClaude: wantsClaude,
    includeNonClaude: wantsNonClaude || concretePlatforms.length === 0,
  };
}

/**
 * Infer a platform adapter from workspace markers.
 */
export function inferPlatformId(workspaceRoot: string): 'vscode-copilot' | null {
  const prompts = path.join(workspaceRoot, '.github', 'prompts');
  if (existsSync(prompts)) return 'vscode-copilot';
  return null;
}

/**
 * Pick the workspace root. Uses a provided path or attempts to infer from cwd.
 */
export async function pickWorkspaceRoot(root?: string): Promise<string | null> {
  if (root) return path.resolve(expandHome(root));
  return findRepoRoot(process.cwd());
}

/**
 * Information about a platform adapter.
 */
export interface PlatformInfo {
  platformId: string;
  dirName: string;
  adaptorPath: string;
  displayName: string;
  adapterVersion: string | null;
  mcpConfigPaths: string[];
}

export type PlatformLoadIssueKind =
  | 'missing_adaptor'
  | 'parse_error'
  | 'missing_required_constant'
  | 'id_mismatch';

export interface PlatformLoadIssue {
  dirName: string;
  kind: PlatformLoadIssueKind;
  message: string;
}

export interface LoadPlatformsResult {
  platforms: PlatformInfo[];
  issues: PlatformLoadIssue[];
}

/**
 * Loads all platform adapters from the skill's platforms directory.
 */
export async function loadPlatformsDetailed(skillDir: string): Promise<LoadPlatformsResult> {
  const platformsDir = path.join(skillDir, 'platforms');
  let entries: Dirent[];

  try {
    entries = await fs.readdir(platformsDir, { withFileTypes: true });
  } catch {
    return { platforms: [], issues: [] };
  }

  const platforms: PlatformInfo[] = [];
  const issues: PlatformLoadIssue[] = [];

  const platformDirs = entries.filter((e) => e.isDirectory() && !e.name.startsWith('_'));

  for (const entry of platformDirs) {
    const dirName = entry.name;
    const platformDir = path.join(platformsDir, dirName);
    const adaptorPath = path.join(platformDir, 'adaptor.md');

    if (!(await pathExists(adaptorPath))) {
      issues.push({ dirName, kind: 'missing_adaptor', message: 'adaptor.md is missing.' });
      continue;
    }

    let data: Awaited<ReturnType<typeof parseAdaptorMd>>;
    try {
      data = await parseAdaptorMd(adaptorPath);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      issues.push({
        dirName,
        kind: 'parse_error',
        message: `Failed to parse adaptor.md: ${msg}`,
      });
      continue;
    }

    const rawPlatformId = getString(data.constants, 'PLATFORM_ID', '').trim();
    const rawDisplayName = getString(data.constants, 'DISPLAY_NAME', '').trim();
    const adapterVersion = getString(data.constants, 'ADAPTER_VERSION', '').trim() || null;
    const mcpConfigPaths = getStringArray(data.constants, 'MCP_CONFIG_PATHS');

    if (rawPlatformId && rawPlatformId !== dirName) {
      issues.push({
        dirName,
        kind: 'id_mismatch',
        message: 'PLATFORM_ID does not match directory name; keep them aligned.',
      });
    }

    if (!rawPlatformId) {
      issues.push({
        dirName,
        kind: 'missing_required_constant',
        message: 'PLATFORM_ID is missing; fallback to directory name.',
      });
    }
    if (!rawDisplayName) {
      issues.push({
        dirName,
        kind: 'missing_required_constant',
        message: 'DISPLAY_NAME is missing; fallback to directory name.',
      });
    }

    platforms.push({
      platformId: rawPlatformId || dirName,
      dirName,
      adaptorPath,
      displayName: rawDisplayName || dirName,
      adapterVersion,
      mcpConfigPaths,
    });
  }

  platforms.sort((a, b) => a.displayName.localeCompare(b.displayName));
  return { platforms, issues };
}

/**
 * Loads all platform adapters from the skill's platforms directory.
 */
export async function loadPlatforms(skillDir: string): Promise<PlatformInfo[]> {
  const { platforms } = await loadPlatformsDetailed(skillDir);
  return platforms;
}

/**
 * Recursively copy a directory.
 */
export async function copyDir(src: string, dest: string): Promise<void> {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });
  for (const entry of entries) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      await copyDir(s, d);
    } else {
      await fs.copyFile(s, d);
    }
  }
}

/**
 * Ensure a directory exists.
 */
export async function ensureDir(p: string): Promise<void> {
  await fs.mkdir(p, { recursive: true });
}

/**
 * Read a text file if it exists.
 */
export async function readFileIfExists(p: string): Promise<string | null> {
  try {
    return await fs.readFile(p, 'utf8');
  } catch {
    return null;
  }
}

/**
 * Write a text file if it does not exist or force is true.
 */
export async function writeFileIfAllowed(
  p: string,
  content: string,
  opts: { force: boolean }
): Promise<boolean> {
  if (!opts.force && existsSync(p)) return false;
  await ensureDir(path.dirname(p));
  await fs.writeFile(p, content, 'utf8');
  return true;
}

/**
 * List files in a directory recursively.
 */
export async function listFilesRecursive(dir: string): Promise<string[]> {
  const out: string[] = [];
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...(await listFilesRecursive(full)));
    } else {
      out.push(full);
    }
  }
  return out;
}

/**
 * Returns the current user's home directory.
 */
export function homeDir(): string {
  return os.homedir();
}

/**
 * Expand a leading `~` to the user's home directory.
 */
export function expandHome(p: string): string {
  if (!p) return p;
  if (p === '~') return homeDir();
  if (p.startsWith('~/') || p.startsWith('~\\')) {
    return path.join(homeDir(), p.slice(2));
  }
  return p;
}

/**
 * Walk up from `startDir` to find the nearest directory containing `.git`.
 */
export async function findRepoRoot(startDir: string): Promise<string | null> {
  let cur = path.resolve(startDir);
  while (true) {
    const gitDir = path.join(cur, '.git');
    if (existsSync(gitDir)) return cur;
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

/**
 * Remove a directory recursively.
 */
export async function removeDir(p: string): Promise<void> {
  await fs.rm(p, { recursive: true, force: true });
}

export interface ReplaceDirWithCopyResult {
  replacedExisting: boolean;
  leftoverBackupPath: string | null;
}

export type ReplaceDirWithCopyErrorKind =
  | 'stage-copy-failed'
  | 'target-busy'
  | 'activate-failed'
  | 'rollback-failed';

export class ReplaceDirWithCopyError extends Error {
  readonly kind: ReplaceDirWithCopyErrorKind;
  readonly targetPath: string;
  readonly backupPath: string | null;

  constructor(
    kind: ReplaceDirWithCopyErrorKind,
    targetPath: string,
    message: string,
    opts: { cause?: unknown; backupPath?: string | null } = {}
  ) {
    super(message, opts.cause !== undefined ? { cause: opts.cause } : undefined);
    this.name = 'ReplaceDirWithCopyError';
    this.kind = kind;
    this.targetPath = targetPath;
    this.backupPath = opts.backupPath ?? null;
  }
}

async function cleanupPathIfExists(p: string): Promise<void> {
  try {
    await fs.rm(p, { recursive: true, force: true });
  } catch {
    // Best-effort cleanup only.
  }
}

function tempArtifactPath(dest: string, label: 'staging' | 'backup'): string {
  const parent = path.dirname(dest);
  const base = path.basename(dest);
  return path.join(parent, `.${base}.aps-${label}-${process.pid}-${Date.now()}-${randomUUID()}`);
}

export async function replaceDirWithCopy(src: string, dest: string): Promise<ReplaceDirWithCopyResult> {
  const stagingPath = tempArtifactPath(dest, 'staging');
  const backupPath = tempArtifactPath(dest, 'backup');

  await ensureDir(path.dirname(dest));

  try {
    await copyDir(src, stagingPath);
  } catch (err) {
    await cleanupPathIfExists(stagingPath);
    throw new ReplaceDirWithCopyError(
      'stage-copy-failed',
      dest,
      `Cannot prepare APS files for ${dest}.`,
      { cause: err }
    );
  }

  const hadExisting = await pathExists(dest);

  if (hadExisting) {
    try {
      await fs.rename(dest, backupPath);
    } catch (err) {
      await cleanupPathIfExists(stagingPath);
      throw new ReplaceDirWithCopyError(
        'target-busy',
        dest,
        `Cannot replace APS files at ${dest}. The existing installation is busy or locked. Close any program that has files open in this skill directory, then run the command again.`,
        { cause: err }
      );
    }
  }

  try {
    await fs.rename(stagingPath, dest);
  } catch (err) {
    await cleanupPathIfExists(stagingPath);

    if (hadExisting) {
      try {
        await fs.rename(backupPath, dest);
      } catch (rollbackErr) {
        throw new ReplaceDirWithCopyError(
          'rollback-failed',
          dest,
          `Cannot activate the updated APS files at ${dest}, and the previous installation could not be restored automatically. The previous files remain at ${backupPath}.`,
          { cause: rollbackErr, backupPath }
        );
      }
    }

    throw new ReplaceDirWithCopyError(
      'activate-failed',
      dest,
      `Cannot activate the updated APS files at ${dest}. The previous installation was restored.`,
      { cause: err }
    );
  }

  let leftoverBackupPath: string | null = null;

  if (hadExisting) {
    try {
      await fs.rm(backupPath, { recursive: true, force: true });
    } catch {
      leftoverBackupPath = backupPath;
    }
  }

  return {
    replacedExisting: hadExisting,
    leftoverBackupPath,
  };
}

function toPosixPath(p: string): string {
  return p.split(path.sep).join('/');
}

/**
 * Options for copying template files from a source directory into a destination root.
 */
export interface CopyTemplateTreeOptions {
  force?: boolean;
  filter?: (relPath: string) => boolean;
}

/**
 * Copy template files from `srcDir` into `dstRoot`, preserving relative paths.
 * Returns the list of relative paths that were actually written.
 */
export async function copyTemplateTree(
  srcDir: string,
  dstRoot: string,
  opts: CopyTemplateTreeOptions = {}
): Promise<string[]> {
  const { force = false, filter = () => true } = opts;
  const files = await listFilesRecursive(srcDir);
  const copied: string[] = [];

  for (const srcFile of files) {
    const relPath = toPosixPath(path.relative(srcDir, srcFile));
    if (!filter(relPath)) continue;

    const dstFile = path.join(dstRoot, relPath);
    const dstExists = await pathExists(dstFile);
    if (dstExists && !force) continue;

    await ensureDir(path.dirname(dstFile));
    await fs.cp(srcFile, dstFile, { force: true, preserveTimestamps: true });
    copied.push(relPath);
  }

  return copied;
}