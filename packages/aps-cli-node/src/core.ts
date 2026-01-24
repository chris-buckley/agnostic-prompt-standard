import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { safeParsePlatformManifest, safeParseSkillFrontmatter } from './schemas/index.js';

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
 * @returns The home directory path.
 */
export function homeDir(): string {
  return os.homedir();
}

/**
 * Checks if a path exists (file or directory).
 * @param p - The path to check.
 * @returns True if the path exists.
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
 * @param p - The path to check.
 * @returns True if the path is a directory.
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
 * @param startDir - The directory to start searching from.
 * @returns The repository root path, or null if not found.
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
 * @param cliRoot - The root path provided via CLI option.
 * @returns The resolved workspace root, or null if not found.
 */
export async function pickWorkspaceRoot(cliRoot: string | undefined): Promise<string | null> {
  if (cliRoot) return path.resolve(cliRoot);
  return findRepoRoot(process.cwd());
}

/**
 * Returns the default project skill installation path.
 * @param repoRoot - The repository root directory.
 * @param opts - Options for skill path resolution.
 * @param opts.claude - If true, returns the Claude-specific path.
 * @returns The project skill path.
 */
export function defaultProjectSkillPath(repoRoot: string, opts: { claude?: boolean } = {}): string {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(repoRoot, '.claude', 'skills', SKILL_ID)
    : path.join(repoRoot, '.github', 'skills', SKILL_ID);
}

/**
 * Returns the default personal skill installation path.
 * @param opts - Options for skill path resolution.
 * @param opts.claude - If true, returns the Claude-specific path.
 * @returns The personal skill path.
 */
export function defaultPersonalSkillPath(opts: { claude?: boolean } = {}): string {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(homeDir(), '.claude', 'skills', SKILL_ID)
    : path.join(homeDir(), '.copilot', 'skills', SKILL_ID);
}

/**
 * Infers the platform ID based on workspace directory structure.
 * @param workspaceRoot - The workspace root directory.
 * @returns The detected platform ID, or null if none detected.
 * @deprecated Use detectAdapters from detection/adapters.ts instead.
 */
export function inferPlatformId(workspaceRoot: string): 'vscode-copilot' | null {
  // Heuristic: VS Code + Copilot convention folders/files.
  // If more platforms are added, extend this with adapter-specific heuristics.
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
 * @param skillDir - The directory containing SKILL.md.
 * @returns The parsed frontmatter, or null if not found.
 * @throws If the file cannot be read.
 */
export async function readSkillFrontmatter(skillDir: string): Promise<SkillFrontmatter | null> {
  const skillPath = path.join(skillDir, 'SKILL.md');
  const raw = await fs.readFile(skillPath, 'utf8');
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const yaml = match[1] ?? '';
  const out: Record<string, string> = {};

  // Extremely small YAML subset parser: key: "value" / key: value
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

  // Validate with Zod schema (passthrough allows additional fields)
  const result = safeParseSkillFrontmatter(out);
  if (!result.success) {
    console.warn(`Warning: Invalid skill frontmatter in ${skillPath}: ${result.error.message}`);
  }

  return out;
}

/**
 * Loads all platform adapters from the skill's platforms directory.
 * @param skillDir - The skill directory containing a platforms/ subdirectory.
 * @returns An array of platform information, sorted by display name.
 */
export async function loadPlatforms(skillDir: string): Promise<PlatformInfo[]> {
  const platformsDir = path.join(skillDir, 'platforms');
  const entries = await fs.readdir(platformsDir, { withFileTypes: true });

  // Filter to valid platform directories
  const platformDirs = entries.filter((e) => e.isDirectory() && !e.name.startsWith('_'));

  // Load all manifests in parallel
  const loadResults = await Promise.allSettled(
    platformDirs.map(async (e) => {
      const manifestPath = path.join(platformsDir, e.name, 'manifest.json');
      if (!(await pathExists(manifestPath))) return null;

      const manifestRaw = await fs.readFile(manifestPath, 'utf8');
      const parsed: unknown = JSON.parse(manifestRaw);

      // Validate with Zod schema
      const result = safeParsePlatformManifest(parsed);
      if (!result.success) {
        console.warn(`Warning: Invalid platform manifest at ${manifestPath}: ${result.error.message}`);
        // Fall back to partial extraction for backwards compatibility
        const partial = parsed as Record<string, unknown>;
        return {
          platformId: typeof partial.platformId === 'string' ? partial.platformId : e.name,
          displayName: typeof partial.displayName === 'string' ? partial.displayName : e.name,
          adapterVersion: typeof partial.adapterVersion === 'string' ? partial.adapterVersion : null,
        };
      }

      return {
        platformId: result.data.platformId,
        displayName: result.data.displayName,
        adapterVersion: result.data.adapterVersion ?? null,
      };
    })
  );

  // Collect successful results
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
 * @returns The directory path of the current module.
 */
export function resolveThisDir(): string {
  return path.dirname(fileURLToPath(import.meta.url));
}

/**
 * Resolves the path to the APS skill payload directory.
 * Checks packaged payload first, then falls back to dev checkout location.
 * @returns The path to the skill payload directory.
 * @throws If the payload directory cannot be found.
 */
export async function resolvePayloadSkillDir(): Promise<string> {
  // Priority:
  // 1) packaged payload/...
  // 2) repo dev checkout: ../../skill/...
  const thisDir = resolveThisDir();
  const packaged = path.resolve(thisDir, '..', 'payload', SKILL_ID);
  if (await isDirectory(packaged)) return packaged;
  const dev = path.resolve(thisDir, '..', '..', '..', 'skill', SKILL_ID);
  if (await isDirectory(dev)) return dev;
  throw new Error('APS payload not found (payload directory missing).');
}

/**
 * Ensures a directory exists, creating it recursively if needed.
 * @param p - The directory path to create.
 */
export async function ensureDir(p: string): Promise<void> {
  await fs.mkdir(p, { recursive: true });
}

/**
 * Removes a directory recursively.
 * @param p - The directory path to remove.
 */
export async function removeDir(p: string): Promise<void> {
  await fs.rm(p, { recursive: true, force: true });
}

/**
 * Copies a directory recursively.
 * @param src - The source directory path.
 * @param dst - The destination directory path.
 */
export async function copyDir(src: string, dst: string): Promise<void> {
  // Node 18+ supports fs.cp
  await fs.cp(src, dst, {
    recursive: true,
    force: true,
  });
}

/**
 * Recursively lists all files in a directory.
 * @param rootDir - The root directory to traverse.
 * @returns An array of absolute file paths.
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
  /** If true, overwrite existing files. */
  force?: boolean;
  /** Filter function to include/exclude files by relative path. */
  filter?: (relPath: string) => boolean;
}

/**
 * Copies template files from a source directory to a destination root.
 * @param srcDir - The source template directory.
 * @param dstRoot - The destination root directory.
 * @param opts - Copy options.
 * @returns An array of relative paths that were copied.
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
    const relPath = path.relative(srcDir, srcFile);
    if (!filter(relPath)) continue;

    const dstFile = path.join(dstRoot, relPath);
    const dstExists = await pathExists(dstFile);
    if (dstExists && !force) continue;

    await ensureDir(path.dirname(dstFile));
    await fs.copyFile(srcFile, dstFile);
    copied.push(relPath);
  }

  return copied;
}
