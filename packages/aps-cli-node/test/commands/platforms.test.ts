import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

import { loadPlatforms, isDirectory } from '../../dist/core.js';

async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-platforms-'));
}

// ─────────────────────────────────────────────────────────────────────────────
// loadPlatforms
// ─────────────────────────────────────────────────────────────────────────────

test('loadPlatforms returns empty array when platforms dir is empty', async () => {
  const root = await tempDir();
  const skillDir = path.join(root, 'skill');
  await fs.mkdir(path.join(skillDir, 'platforms'), { recursive: true });

  const platforms = await loadPlatforms(skillDir);
  assert.deepEqual(platforms, []);
});

test('loadPlatforms skips directories starting with underscore', async () => {
  const root = await tempDir();
  const skillDir = path.join(root, 'skill');
  const platformsDir = path.join(skillDir, 'platforms');
  await fs.mkdir(platformsDir, { recursive: true });

  // Create a _template directory that should be skipped
  const templateDir = path.join(platformsDir, '_template');
  await fs.mkdir(templateDir);
  await fs.writeFile(
    path.join(templateDir, 'manifest.json'),
    JSON.stringify({ platformId: '_template', displayName: 'Template' })
  );

  const platforms = await loadPlatforms(skillDir);
  assert.deepEqual(platforms, []);
});

test('loadPlatforms loads valid platform manifests', async () => {
  const root = await tempDir();
  const skillDir = path.join(root, 'skill');
  const platformsDir = path.join(skillDir, 'platforms');

  // Create a valid platform
  const testPlatformDir = path.join(platformsDir, 'test-platform');
  await fs.mkdir(testPlatformDir, { recursive: true });
  await fs.writeFile(
    path.join(testPlatformDir, 'manifest.json'),
    JSON.stringify({
      platformId: 'test-platform',
      displayName: 'Test Platform',
      adapterVersion: '1.0.0',
    })
  );

  const platforms = await loadPlatforms(skillDir);
  assert.equal(platforms.length, 1);
  assert.equal(platforms[0]?.platformId, 'test-platform');
  assert.equal(platforms[0]?.displayName, 'Test Platform');
  assert.equal(platforms[0]?.adapterVersion, '1.0.0');
});

test('loadPlatforms skips directories without manifest.json', async () => {
  const root = await tempDir();
  const skillDir = path.join(root, 'skill');
  const platformsDir = path.join(skillDir, 'platforms');

  // Create a directory without manifest
  const noManifestDir = path.join(platformsDir, 'no-manifest');
  await fs.mkdir(noManifestDir, { recursive: true });

  const platforms = await loadPlatforms(skillDir);
  assert.deepEqual(platforms, []);
});

// ─────────────────────────────────────────────────────────────────────────────
// isDirectory utility
// ─────────────────────────────────────────────────────────────────────────────

test('isDirectory returns true for directories', async () => {
  const root = await tempDir();
  const dirPath = path.join(root, 'subdir');
  await fs.mkdir(dirPath);

  const isDir = await isDirectory(dirPath);
  assert.equal(isDir, true);
});

test('isDirectory returns false for files', async () => {
  const root = await tempDir();
  const filePath = path.join(root, 'file.txt');
  await fs.writeFile(filePath, 'content');

  const isDir = await isDirectory(filePath);
  assert.equal(isDir, false);
});

test('isDirectory returns false for non-existent paths', async () => {
  const root = await tempDir();
  const noPath = path.join(root, 'nonexistent');

  const isDir = await isDirectory(noPath);
  assert.equal(isDir, false);
});
