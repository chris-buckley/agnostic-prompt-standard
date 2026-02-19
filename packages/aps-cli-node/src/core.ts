import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { safeParseSkillFrontmatter } from './schemas/index.js';
import { parseAdaptorMd, getString } from './parsers/adaptor.js';

/** The unique identifier for the APS skill. */
export const SKILL_ID = 'agnostic-prompt-standard' as const;

/**
 * Information about a platform adapter.
 */
export interface PlatformInfo {
  platformId: string;
  displayName: string;
  adapterVersion: string | null;
}

/**
 * Returns the user's home directory path.
 */
export function homeDir(): string {
  return os.homedir();
}

/**
 * Expands a leading ~ in a path to the user's home directory.
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
 * Checks if a path exists (file or directory).
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
 * Checks if a path is a directory.
 */
export async function isDirectory(p: string): Promise<boolean> {
  try {
    const st = await fs.stat(p);
    return st.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Finds the root of a git repository by walking up from the start directory.
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
 * Resolves the workspace root directory from a CLI option or auto-detects it.
 */
export async function pickWorkspaceRoot(cliRoot: string | undefined): Promise<string | null> {
  if (cliRoot) return path.resolve(expandHome(cliRoot));
  return findRepoRoot(process.cwd());
}

/**
 * Returns the default project skill installation path.
 */
export function defaultProjectSkillPath(repoRoot: string, opts: { claude?: boolean } = {}): string {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(repoRoot, '.claude', 'skills', SKILL_ID)
    : path.join(repoRoot, '.github', 'skills', SKILL_ID);
}

/**
 * Returns the default personal skill installation path.
 */
export function defaultPersonalSkillPath(opts: { claude?: boolean } = {}): string {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(homeDir(), '.claude', 'skills', SKILL_ID)
    : path.join(homeDir(), '.copilot', 'skills', SKILL_ID);
}

/**
 * Infers the platform ID based on workspace directory structure.
 * @deprecated Use detectAdapters from detection/adapters.ts instead.
 */
export function inferPlatformId(workspaceRoot: string): 'vscode-copilot' | null {
  const gh = path.join(workspaceRoot, '.github');
  const hasAgents = existsSync(path.join(gh, 'agents'));
  const hasPrompts = existsSync(path.join(gh, 'prompts'));
  const hasInstructions =
    existsSync(path.join(gh, 'copilot-instructions.md')) || existsSync(path.join(gh, 'instructions'));
  if (hasAgents || hasPrompts || hasInstructions) return 'vscode-copilot';
  return null;
}

/** Skill frontmatter parsed from SKILL.md YAML header. */
export type SkillFrontmatter = Record<string, string>;

/**
 * Reads and parses the frontmatter from a SKILL.md file.
 */
export async function readSkillFrontmatter(skillDir: string): Promise<SkillFrontmatter | null> {
  const skillPath = path.join(skillDir, 'SKILL.md');
  const raw = await fs.readFile(skillPath, 'utf8');
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const yaml = match[1] ?? '';
  const out: Record<string, string> = {};

  for (const line of yaml.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf(':');
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let val = trimmed.slice(idx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }

  const result = safeParseSkillFrontmatter(out);
  if (!result.success) {
    console.warn(`Warning: Invalid skill frontmatter in ${skillPath}: ${result.error.message}`);
  }

  return out;
}

/**
 * Loads a platform from its adaptor.md file.
 * @param platformDir - Absolute path to the platform directory.
 * @param dirName - Directory name (used as fallback platformId).
 * @returns PlatformInfo or null if adaptor.md is missing/invalid.
 */
async function loadPlatformFromAdaptor(platformDir: string, dirName: string): Promise<PlatformInfo | null> {
  const adaptorPath = path.join(platformDir, 'adaptor.md');
  if (!(await pathExists(adaptorPath))) return null;

  try {
    const data = await parseAdaptorMd(adaptorPath);
    return {
      platformId: getString(data.constants, 'PLATFORM_ID', dirName),
      displayName: getString(data.constants, 'DISPLAY_NAME', dirName),
      adapterVersion: getString(data.constants, 'ADAPTER_VERSION') || null,
    };
  } catch {
    return null;
  }
}

/**
 * Loads all platform adapters from the skill's platforms directory.
 * @param skillDir - The skill directory containing a platforms/ subdirectory.
 * @returns An array of platform information, sorted by display name.
 */
export async function loadPlatforms(skillDir: string): Promise<PlatformInfo[]> {
  const platformsDir = path.join(skillDir, 'platforms');
  const entries = await fs.readdir(platformsDir, { withFileTypes: true });
  const platformDirs = entries.filter((e) => e.isDirectory() && !e.name.startsWith('_'));

  const loadResults = await Promise.allSettled(
    platformDirs.map(async (e) => {
      const fullPath = path.join(platformsDir, e.name);
      return loadPlatformFromAdaptor(fullPath, e.name);
    })
  );

  const platforms: PlatformInfo[] = [];
  for (const result of loadResults) {
    if (result.status === 'fulfilled' && result.value !== null) {
      platforms.push(result.value);
    }
  }

  platforms.sort((a, b) => a.displayName.localeCompare(b.displayName));
  return platforms;
}

/**
 * Resolves the directory containing the current module.
 */
export function resolveThisDir(): string {
  return path.dirname(fileURLToPath(import.meta.url));
}

/**
 * Resolves the path to the APS skill payload directory.
 */
export async function resolvePayloadSkillDir(): Promise<string> {
  const thisDir = resolveThisDir();
  const packaged = path.resolve(thisDir, '..', 'payload', SKILL_ID);
  if (await isDirectory(packaged)) return packaged;
  const dev = path.resolve(thisDir, '..', '..', '..', 'skill', SKILL_ID);
  if (await isDirectory(dev)) return dev;
  throw new Error('APS payload not found (payload directory missing).');
}

/**
 * Ensures a directory exists, creating it recursively if needed.
 */
export async function ensureDir(p: string): Promise<void> {
  await fs.mkdir(p, { recursive: true });
}

/**
 * Removes a directory recursively.
 */
export async function removeDir(p: string): Promise<void> {
  await fs.rm(p, { recursive: true, force: true });
}

/**
 * Copies a directory recursively.
 */
export async function copyDir(src: string, dst: string): Promise<void> {
  await fs.cp(src, dst, {
    recursive: true,
    force: true,
    preserveTimestamps: true,
  });
}

function toPosixPath(p: string): string {
  return p.split(path.sep).join('/');
}

/**
 * Recursively lists all files in a directory.
 */
export async function listFilesRecursive(rootDir: string): Promise<string[]> {
  const results: string[] = [];

  async function walk(dir: string): Promise<void> {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else {
        results.push(fullPath);
      }
    }
  }

  await walk(rootDir);
  return results;
}

/**
 * Options for copying template files.
 */
export interface CopyTemplateTreeOptions {
  force?: boolean;
  filter?: (relPath: string) => boolean;
}

/**
 * Copies template files from a source directory to a destination root.
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
