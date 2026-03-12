import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

import { computeInstallFamilies, findRepoRoot, inferPlatformId, pickWorkspaceRoot, replaceDirWithCopy } from '../dist/core.js';

async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-node-'));
}

test('findRepoRoot walks up to .git', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.git'));
  const nested = path.join(root, 'a', 'b');
  await fs.mkdir(nested, { recursive: true });

  const found = await findRepoRoot(nested);
  assert.equal(found, root);
});

test('findRepoRoot returns null when no .git', async () => {
  const root = await tempDir();
  const nested = path.join(root, 'a');
  await fs.mkdir(nested, { recursive: true });
  const found = await findRepoRoot(nested);
  assert.equal(found, null);
});

test('inferPlatformId detects vscode-copilot via .github/prompts', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github', 'prompts'), { recursive: true });
  const platform = inferPlatformId(root);
  assert.equal(platform, 'vscode-copilot');
});


test('computeInstallFamilies treats generic as install-family neutral', () => {
  assert.deepEqual(computeInstallFamilies(['generic']), {
    includeClaude: false,
    includeNonClaude: true,
  });
});

test('computeInstallFamilies keeps claude-only install when generic is combined with claude-code', () => {
  assert.deepEqual(computeInstallFamilies(['generic', 'claude-code']), {
    includeClaude: true,
    includeNonClaude: false,
  });
});


test('pickWorkspaceRoot falls back to the git repo root', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.git'));
  const nested = path.join(root, 'a', 'b');
  await fs.mkdir(nested, { recursive: true });

  const originalCwd = process.cwd();
  process.chdir(nested);
  try {
    const found = await pickWorkspaceRoot();
    assert.equal(found, root);
  } finally {
    process.chdir(originalCwd);
  }
});

test('replaceDirWithCopy swaps directory contents without leaving stale files', async () => {
  const root = await tempDir();
  const src = path.join(root, 'src');
  const dest = path.join(root, 'dest');

  await fs.mkdir(path.join(src, 'nested'), { recursive: true });
  await fs.writeFile(path.join(src, 'SKILL.md'), 'framework_revision: "1.2.0"\n');
  await fs.writeFile(path.join(src, 'nested', 'new.txt'), 'new\n');

  await fs.mkdir(path.join(dest, 'nested'), { recursive: true });
  await fs.writeFile(path.join(dest, 'old.txt'), 'old\n');
  await fs.writeFile(path.join(dest, 'nested', 'stale.txt'), 'stale\n');

  const result = await replaceDirWithCopy(src, dest);

  assert.equal(result.replacedExisting, true);
  assert.equal(result.leftoverBackupPath, null);
  assert.equal(await fs.readFile(path.join(dest, 'SKILL.md'), 'utf-8'), 'framework_revision: "1.2.0"\n');
  assert.equal(await fs.readFile(path.join(dest, 'nested', 'new.txt'), 'utf-8'), 'new\n');
  await assert.rejects(fs.access(path.join(dest, 'old.txt')));
  await assert.rejects(fs.access(path.join(dest, 'nested', 'stale.txt')));
});
