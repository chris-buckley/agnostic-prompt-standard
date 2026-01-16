import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

export const SKILL_ID = 'agnostic-prompt-standard';

export function homeDir() {
  return os.homedir();
}

export async function pathExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

export async function isDirectory(p) {
  try {
    const st = await fs.stat(p);
    return st.isDirectory();
  } catch {
    return false;
  }
}

export async function findRepoRoot(startDir) {
  let cur = path.resolve(startDir);
  while (true) {
    const gitDir = path.join(cur, '.git');
    if (existsSync(gitDir)) return cur;
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

export function defaultProjectSkillPath(repoRoot, opts = {}) {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(repoRoot, '.claude', 'skills', SKILL_ID)
    : path.join(repoRoot, '.github', 'skills', SKILL_ID);
}

export function defaultPersonalSkillPath(opts = {}) {
  const claude = Boolean(opts.claude);
  return claude
    ? path.join(homeDir(), '.claude', 'skills', SKILL_ID)
    : path.join(homeDir(), '.copilot', 'skills', SKILL_ID);
}

export function inferPlatformId(workspaceRoot) {
  // Heuristic: VS Code + Copilot convention folders/files.
  // If more platforms are added, extend this with adapter-specific heuristics.
  const gh = path.join(workspaceRoot, '.github');
  const hasAgents = existsSync(path.join(gh, 'agents'));
  const hasPrompts = existsSync(path.join(gh, 'prompts'));
  const hasInstructions = existsSync(path.join(gh, 'copilot-instructions.md')) || existsSync(path.join(gh, 'instructions'));
  if (hasAgents || hasPrompts || hasInstructions) return 'vscode-copilot';
  return null;
}

export async function readSkillFrontmatter(skillDir) {
  const skillPath = path.join(skillDir, 'SKILL.md');
  const raw = await fs.readFile(skillPath, 'utf8');
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const yaml = match[1];
  const out = {};
  // Extremely small YAML subset parser: key: "value" / key: value
  for (const line of yaml.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf(':');
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let val = trimmed.slice(idx + 1).trim();
    // strip quotes
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

export async function loadPlatforms(skillDir) {
  const platformsDir = path.join(skillDir, 'platforms');
  const entries = await fs.readdir(platformsDir, { withFileTypes: true });
  const platforms = [];
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (e.name.startsWith('_')) continue;
    const manifestPath = path.join(platformsDir, e.name, 'manifest.json');
    if (!(await pathExists(manifestPath))) continue;
    try {
      const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
      platforms.push({
        platformId: manifest.platformId ?? e.name,
        displayName: manifest.displayName ?? e.name,
        adapterVersion: manifest.adapterVersion ?? null,
        hasTemplates: await isDirectory(path.join(platformsDir, e.name, 'templates')),
      });
    } catch {
      // ignore malformed platform manifests
    }
  }
  platforms.sort((a, b) => a.displayName.localeCompare(b.displayName));
  return platforms;
}

export function resolveThisDir() {
  return path.dirname(fileURLToPath(import.meta.url));
}

export async function resolvePayloadSkillDir() {
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

export async function ensureDir(p) {
  await fs.mkdir(p, { recursive: true });
}

export async function removeDir(p) {
  await fs.rm(p, { recursive: true, force: true });
}

export async function copyDir(src, dst) {
  // Node 18+ supports fs.cp
  await fs.cp(src, dst, {
    recursive: true,
    force: true,
  });
}

export async function copyTemplates(templatesDir, workspaceRoot, { force }) {
  // Merge-copy everything from templatesDir into workspaceRoot.
  // If force=false, we will not overwrite existing files.
  // We implement this with a manual tree walk to make overwrite policy explicit.
  async function walk(rel) {
    const abs = path.join(templatesDir, rel);
    const st = await fs.stat(abs);
    if (st.isDirectory()) {
      const entries = await fs.readdir(abs);
      for (const ent of entries) await walk(path.join(rel, ent));
      return;
    }
    // file
    const dest = path.join(workspaceRoot, rel);
    await ensureDir(path.dirname(dest));
    if (!force && (await pathExists(dest))) {
      return { skipped: [rel], copied: [] };
    }
    await fs.copyFile(abs, dest);
    return { skipped: [], copied: [rel] };
  }

  const summary = { copied: [], skipped: [] };
  const entries = await fs.readdir(templatesDir);
  for (const ent of entries) {
    const res = await walk(ent);
    if (!res) continue;
    summary.copied.push(...res.copied);
    summary.skipped.push(...res.skipped);
  }
  return summary;
}
