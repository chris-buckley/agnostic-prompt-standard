import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import fs from 'node:fs/promises';

import { getString, parseAdaptorMdString } from '../dist/parsers/adaptor.js';

const REPO_ROOT = path.resolve(process.cwd(), '..', '..');
const PLATFORMS_DIR = path.join(REPO_ROOT, 'skill', 'agnostic-prompt-standard', 'platforms');

async function pathExists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function listPlatformDirs(): Promise<string[]> {
  const entries = await fs.readdir(PLATFORMS_DIR, { withFileTypes: true });
  return entries.filter((e) => e.isDirectory() && !e.name.startsWith('_')).map((e) => e.name);
}

test('each platform adaptor defines required constants', async () => {
  if (!(await pathExists(PLATFORMS_DIR))) return;

  const dirs = await listPlatformDirs();
  for (const dirName of dirs) {
    const adaptorPath = path.join(PLATFORMS_DIR, dirName, 'adaptor.md');
    assert.ok(await pathExists(adaptorPath), `platforms/${dirName} missing adaptor.md`);

    const raw = await fs.readFile(adaptorPath, 'utf8');
    const data = parseAdaptorMdString(raw);

    assert.ok(getString(data.constants, 'PLATFORM_ID', '').trim(), `platforms/${dirName} missing PLATFORM_ID`);
    assert.ok(getString(data.constants, 'DISPLAY_NAME', '').trim(), `platforms/${dirName} missing DISPLAY_NAME`);
    assert.ok(getString(data.constants, 'ADAPTER_VERSION', '').trim(), `platforms/${dirName} missing ADAPTER_VERSION`);
  }
});

test('each platform adaptor uses unique format ids', async () => {
  if (!(await pathExists(PLATFORMS_DIR))) return;

  const dirs = await listPlatformDirs();
  for (const dirName of dirs) {
    const adaptorPath = path.join(PLATFORMS_DIR, dirName, 'adaptor.md');
    const raw = await fs.readFile(adaptorPath, 'utf8');

    const ids = Array.from(raw.matchAll(/<format\b[^>]*\bid="([^"]+)"/g)).map((m) => m[1]);
    assert.equal(ids.length, new Set(ids).size, `platforms/${dirName} has duplicate <format id="…"> values`);
  }
});

test('AGENT_VERSIONING parses as JSON when present', async () => {
  if (!(await pathExists(PLATFORMS_DIR))) return;

  const dirs = await listPlatformDirs();
  for (const dirName of dirs) {
    const adaptorPath = path.join(PLATFORMS_DIR, dirName, 'adaptor.md');
    const raw = await fs.readFile(adaptorPath, 'utf8');
    const data = parseAdaptorMdString(raw);

    const v = data.constants['AGENT_VERSIONING'];
    if (v === undefined) continue;

    assert.ok(typeof v === 'object' && v !== null && !Array.isArray(v), `platforms/${dirName} AGENT_VERSIONING is not an object`);
    const templates = (v as Record<string, unknown>)['templates'];
    assert.ok(Array.isArray(templates), `platforms/${dirName} AGENT_VERSIONING.templates is not an array`);
  }
});