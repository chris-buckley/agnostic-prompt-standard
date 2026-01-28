import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

import {
  defaultProjectSkillPath,
  defaultPersonalSkillPath,
  findRepoRoot,
  SKILL_ID,
} from '../../dist/core.js';

async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-init-'));
}

// ─────────────────────────────────────────────────────────────────────────────
// Skill path computation
// ─────────────────────────────────────────────────────────────────────────────

test('defaultProjectSkillPath returns .github/skills path by default', () => {
  const root = '/test/repo';
  const skillPath = defaultProjectSkillPath(root);
  assert.equal(skillPath, path.join(root, '.github', 'skills', SKILL_ID));
});

test('defaultProjectSkillPath returns .claude/skills path when claude=true', () => {
  const root = '/test/repo';
  const skillPath = defaultProjectSkillPath(root, { claude: true });
  assert.equal(skillPath, path.join(root, '.claude', 'skills', SKILL_ID));
});

test('defaultPersonalSkillPath returns .copilot/skills path by default', () => {
  const home = os.homedir();
  const skillPath = defaultPersonalSkillPath();
  assert.equal(skillPath, path.join(home, '.copilot', 'skills', SKILL_ID));
});

test('defaultPersonalSkillPath returns .claude/skills path when claude=true', () => {
  const home = os.homedir();
  const skillPath = defaultPersonalSkillPath({ claude: true });
  assert.equal(skillPath, path.join(home, '.claude', 'skills', SKILL_ID));
});

// ─────────────────────────────────────────────────────────────────────────────
// Workspace root detection
// ─────────────────────────────────────────────────────────────────────────────

test('findRepoRoot returns root when .git exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.git'));
  const nested = path.join(root, 'src', 'lib');
  await fs.mkdir(nested, { recursive: true });

  const found = await findRepoRoot(nested);
  assert.equal(found, root);
});

test('findRepoRoot returns null when no .git directory', async () => {
  const root = await tempDir();
  const nested = path.join(root, 'some', 'nested', 'path');
  await fs.mkdir(nested, { recursive: true });

  const found = await findRepoRoot(nested);
  assert.equal(found, null);
});
