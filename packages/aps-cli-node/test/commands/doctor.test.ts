import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

import {
  defaultProjectSkillPath,
  defaultPersonalSkillPath,
  pathExists,
  SKILL_ID,
} from '../../dist/core.js';

async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-doctor-'));
}

// ─────────────────────────────────────────────────────────────────────────────
// Skill detection paths
// ─────────────────────────────────────────────────────────────────────────────

test('doctor checks repo skill path correctly', () => {
  const root = '/test/repo';
  const skillPath = defaultProjectSkillPath(root);
  const expectedPath = path.join(root, '.github', 'skills', SKILL_ID);
  assert.equal(skillPath, expectedPath);
});

test('doctor checks personal skill path correctly', () => {
  const home = os.homedir();
  const skillPath = defaultPersonalSkillPath();
  const expectedPath = path.join(home, '.copilot', 'skills', SKILL_ID);
  assert.equal(skillPath, expectedPath);
});

// ─────────────────────────────────────────────────────────────────────────────
// pathExists utility
// ─────────────────────────────────────────────────────────────────────────────

test('pathExists returns true for existing file', async () => {
  const root = await tempDir();
  const filePath = path.join(root, 'test.txt');
  await fs.writeFile(filePath, 'content');

  const exists = await pathExists(filePath);
  assert.equal(exists, true);
});

test('pathExists returns false for non-existing file', async () => {
  const root = await tempDir();
  const filePath = path.join(root, 'nonexistent.txt');

  const exists = await pathExists(filePath);
  assert.equal(exists, false);
});

test('pathExists returns true for existing directory', async () => {
  const root = await tempDir();
  const dirPath = path.join(root, 'subdir');
  await fs.mkdir(dirPath);

  const exists = await pathExists(dirPath);
  assert.equal(exists, true);
});
