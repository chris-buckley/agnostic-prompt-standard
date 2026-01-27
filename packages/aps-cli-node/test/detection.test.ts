import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

import { detectAdapters, formatDetectionLabel, DEFAULT_ADAPTER_ORDER } from '../dist/detection/adapters.js';

async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-node-'));
}

// ─────────────────────────────────────────────────────────────────────────────
// VS Code Copilot detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects vscode-copilot when .github/copilot-instructions.md exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github'), { recursive: true });
  await fs.writeFile(path.join(root, '.github', 'copilot-instructions.md'), '# instructions');

  const detected = await detectAdapters(root);
  assert.equal(detected['vscode-copilot'].detected, true);
  assert.ok(detected['vscode-copilot'].reasons.includes('.github/copilot-instructions.md'));
});

test('detectAdapters detects vscode-copilot when .github/agents/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github', 'agents'), { recursive: true });

  const detected = await detectAdapters(root);
  assert.equal(detected['vscode-copilot'].detected, true);
  assert.ok(detected['vscode-copilot'].reasons.includes('.github/agents/'));
});

test('detectAdapters detects vscode-copilot when .github/prompts/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github', 'prompts'), { recursive: true });

  const detected = await detectAdapters(root);
  assert.equal(detected['vscode-copilot'].detected, true);
  assert.ok(detected['vscode-copilot'].reasons.includes('.github/prompts/'));
});

// ─────────────────────────────────────────────────────────────────────────────
// Claude Code detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects claude-code when .claude/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.claude'), { recursive: true });

  const detected = await detectAdapters(root);
  assert.equal(detected['claude-code'].detected, true);
  assert.ok(detected['claude-code'].reasons.includes('.claude/'));
});

test('detectAdapters detects claude-code when CLAUDE.md exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, 'CLAUDE.md'), '# Claude');

  const detected = await detectAdapters(root);
  assert.equal(detected['claude-code'].detected, true);
  assert.ok(detected['claude-code'].reasons.includes('CLAUDE.md'));
});

test('detectAdapters detects claude-code when .mcp.json exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, '.mcp.json'), '{}');

  const detected = await detectAdapters(root);
  assert.equal(detected['claude-code'].detected, true);
  assert.ok(detected['claude-code'].reasons.includes('.mcp.json'));
});

// ─────────────────────────────────────────────────────────────────────────────
// OpenCode detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects opencode when .opencode/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.opencode'), { recursive: true });

  const detected = await detectAdapters(root);
  assert.equal(detected.opencode.detected, true);
  assert.ok(detected.opencode.reasons.includes('.opencode/'));
});

test('detectAdapters detects opencode when .opencode/opencode.jsonc exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.opencode'), { recursive: true });
  await fs.writeFile(path.join(root, '.opencode', 'opencode.jsonc'), '{}');

  const detected = await detectAdapters(root);
  assert.equal(detected.opencode.detected, true);
  assert.ok(detected.opencode.reasons.includes('.opencode/opencode.jsonc'));
});

test('detectAdapters detects opencode when .opencode/opencode.json exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.opencode'), { recursive: true });
  await fs.writeFile(path.join(root, '.opencode', 'opencode.json'), '{}');

  const detected = await detectAdapters(root);
  assert.equal(detected.opencode.detected, true);
  assert.ok(detected.opencode.reasons.includes('.opencode/opencode.json'));
});

test('detectAdapters detects opencode when opencode.json exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, 'opencode.json'), '{}');

  const detected = await detectAdapters(root);
  assert.equal(detected.opencode.detected, true);
  assert.ok(detected.opencode.reasons.includes('opencode.json'));
});

test('detectAdapters detects opencode when opencode.jsonc exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, 'opencode.jsonc'), '{}');

  const detected = await detectAdapters(root);
  assert.equal(detected.opencode.detected, true);
  assert.ok(detected.opencode.reasons.includes('opencode.jsonc'));
});

test('detectAdapters detects opencode when .opencode.json exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, '.opencode.json'), '{"ok":true}');

  const detected = await detectAdapters(root);
  assert.equal(detected.opencode.detected, true);
  assert.ok(detected.opencode.reasons.includes('.opencode.json'));
});

// ─────────────────────────────────────────────────────────────────────────────
// No detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters returns no detections for empty directory', async () => {
  const root = await tempDir();

  const detected = await detectAdapters(root);
  assert.equal(detected['vscode-copilot'].detected, false);
  assert.equal(detected['claude-code'].detected, false);
  assert.equal(detected.opencode.detected, false);
});

// ─────────────────────────────────────────────────────────────────────────────
// Multiple adapters
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects multiple adapters when multiple markers exist', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github', 'agents'), { recursive: true });
  await fs.mkdir(path.join(root, '.claude'), { recursive: true });

  const detected = await detectAdapters(root);
  assert.equal(detected['vscode-copilot'].detected, true);
  assert.equal(detected['claude-code'].detected, true);
  assert.equal(detected.opencode.detected, false);
});

// ─────────────────────────────────────────────────────────────────────────────
// formatDetectionLabel
// ─────────────────────────────────────────────────────────────────────────────

test('formatDetectionLabel returns "(detected)" for detected adapters', () => {
  const label = formatDetectionLabel({
    platformId: 'vscode-copilot',
    detected: true,
    reasons: ['.github/copilot-instructions.md'],
  });
  assert.equal(label, ' (detected)');
});

test('formatDetectionLabel returns empty string for non-detected adapters', () => {
  const label = formatDetectionLabel({
    platformId: 'vscode-copilot',
    detected: false,
    reasons: [],
  });
  assert.equal(label, '');
});

// ─────────────────────────────────────────────────────────────────────────────
// DEFAULT_ADAPTER_ORDER
// ─────────────────────────────────────────────────────────────────────────────

test('DEFAULT_ADAPTER_ORDER contains all known adapters in correct order', () => {
  assert.deepEqual(DEFAULT_ADAPTER_ORDER, ['vscode-copilot', 'claude-code', 'opencode']);
});
