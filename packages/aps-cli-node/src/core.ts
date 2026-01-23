import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

export const SKILL_ID = 'agnostic-prompt-standard' as const;

export interface PlatformInfo {
  platformId: string;
  displayName: string;
  adapterVersion: string | null;
}

export function homeDir(): string {
  return os.homedir();
}

export async function pathExists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

export async function isDirectory(p: string): Promise<boolean> {
  try {
    const st = await fs.stat(p);
    return st.isDirectory();
  } catch {
    return false;
  }
}

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

export function defaultProjectSkillPath(repoRoot: string, opts: { claude?: boolean } = {}): string {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(repoRoot, '.claude', 'skills', SKILL_ID)
    : path.join(repoRoot, '.github', 'skills', SKILL_ID);
}

export function defaultPersonalSkillPath(opts: { claude?: boolean } = {}): string {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(homeDir(), '.claude', 'skills', SKILL_ID)
    : path.join(homeDir(), '.copilot', 'skills', SKILL_ID);
}

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

export type SkillFrontmatter = Record<string, string>;

export async function readSkillFrontmatter(skillDir: string): Promise<SkillFrontmatter | null> {
  const skillPath = path.join(skillDir, 'SKILL.md');
  const raw = await fs.readFile(skillPath, 'utf8');
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const yaml = match[1] ?? '';
  const out: SkillFrontmatter = {};

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
  return out;
}

export async function loadPlatforms(skillDir: string): Promise<PlatformInfo[]> {
  const platformsDir = path.join(skillDir, 'platforms');
  const entries = await fs.readdir(platformsDir, { withFileTypes: true });
  const platforms: PlatformInfo[] = [];

  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (e.name.startsWith('_')) continue;

    const manifestPath = path.join(platformsDir, e.name, 'manifest.json');
    if (!(await pathExists(manifestPath))) continue;

    try {
      const manifestRaw = await fs.readFile(manifestPath, 'utf8');
      const manifest = JSON.parse(manifestRaw) as Partial<PlatformInfo> & {
        platformId?: string;
        displayName?: string;
        adapterVersion?: string | null;
      };

      platforms.push({
        platformId: manifest.platformId ?? e.name,
        displayName: manifest.displayName ?? e.name,
        adapterVersion: manifest.adapterVersion ?? null,
      });
    } catch {
      // ignore malformed platform manifests
    }
  }

  platforms.sort((a, b) => a.displayName.localeCompare(b.displayName));
  return platforms;
}

export function resolveThisDir(): string {
  return path.dirname(fileURLToPath(import.meta.url));
}

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

export async function ensureDir(p: string): Promise<void> {
  await fs.mkdir(p, { recursive: true });
}

export async function removeDir(p: string): Promise<void> {
  await fs.rm(p, { recursive: true, force: true });
}

export async function copyDir(src: string, dst: string): Promise<void> {
  // Node 18+ supports fs.cp
  await fs.cp(src, dst, {
    recursive: true,
    force: true,
  });
}

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

export interface CopyTemplateTreeOptions {
  force?: boolean;
  filter?: (relPath: string) => boolean;
}

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
