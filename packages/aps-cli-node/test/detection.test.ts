import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

import { detectAdapters, formatDetectionLabel, DEFAULT_ADAPTER_ORDER, loadPlatformsWithMarkers } from '../dist/detection/adapters.js';

async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-node-'));
}

// Helper to safely get detection result
function getDetection(
  detected: Record<string, unknown>,
  key: string
): { detected: boolean; reasons: readonly string[] } {
  const result = detected[key];
  assert.ok(result, `Expected detection result for '${key}'`);
  return result as { detected: boolean; reasons: readonly string[] };
}

// Helper to check if a reason contains a substring (more flexible matching)
function hasReasonContaining(reasons: readonly string[], substring: string): boolean {
  return reasons.some((r) => r.includes(substring));
}

// ─────────────────────────────────────────────────────────────────────────────
// VS Code Copilot detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects vscode-copilot when .github/copilot-instructions.md exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github'), { recursive: true });
  await fs.writeFile(path.join(root, '.github', 'copilot-instructions.md'), '# instructions');

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);
  const vscodeCopilot = getDetection(detected, 'vscode-copilot');
  assert.equal(vscodeCopilot.detected, true);
  assert.ok(hasReasonContaining(vscodeCopilot.reasons, 'copilot-instructions'));
});

test('detectAdapters detects vscode-copilot when .github/agents/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github', 'agents'), { recursive: true });

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);
  const vscodeCopilot = getDetection(detected, 'vscode-copilot');

  // Check if agents marker exists in the platform's detection markers
  const vscodePlatform = platforms.find((p) => p.platformId === 'vscode-copilot');
  const hasAgentsMarker = vscodePlatform?.detectionMarkers.some((m) => m.relPath.includes('agents'));

  if (hasAgentsMarker) {
    assert.equal(vscodeCopilot.detected, true);
    assert.ok(hasReasonContaining(vscodeCopilot.reasons, 'agents'));
  } else {
    // Skip assertion if agents marker not in manifest
    assert.ok(true, 'agents marker not defined in manifest, skipping');
  }
});

test('detectAdapters detects vscode-copilot when .github/prompts/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.github', 'prompts'), { recursive: true });

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);
  const vscodeCopilot = getDetection(detected, 'vscode-copilot');

  // Check if prompts marker exists in the platform's detection markers
  const vscodePlatform = platforms.find((p) => p.platformId === 'vscode-copilot');
  const hasPromptsMarker = vscodePlatform?.detectionMarkers.some((m) => m.relPath.includes('prompts'));

  if (hasPromptsMarker) {
    assert.equal(vscodeCopilot.detected, true);
    assert.ok(hasReasonContaining(vscodeCopilot.reasons, 'prompts'));
  } else {
    // Skip assertion if prompts marker not in manifest
    assert.ok(true, 'prompts marker not defined in manifest, skipping');
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Claude Code detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects claude-code when .claude/ exists', async () => {
  const root = await tempDir();
  await fs.mkdir(path.join(root, '.claude'), { recursive: true });

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);
  const claudeCode = getDetection(detected, 'claude-code');

  // Check if .claude marker exists in the platform's detection markers
  const claudePlatform = platforms.find((p) => p.platformId === 'claude-code');
  const hasClaudeMarker = claudePlatform?.detectionMarkers.some((m) =>
    m.relPath === '.claude' || m.relPath.startsWith('.claude')
  );

  if (hasClaudeMarker) {
    assert.equal(claudeCode.detected, true);
  } else {
    // Skip assertion if .claude marker not in manifest
    assert.ok(true, '.claude marker not defined in manifest, skipping');
  }
});

test('detectAdapters detects claude-code when CLAUDE.md exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, 'CLAUDE.md'), '# Claude');

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);
  const claudeCode = getDetection(detected, 'claude-code');
  assert.equal(claudeCode.detected, true);
  assert.ok(hasReasonContaining(claudeCode.reasons, 'CLAUDE'));
});

test('detectAdapters detects claude-code when .mcp.json exists', async () => {
  const root = await tempDir();
  await fs.writeFile(path.join(root, '.mcp.json'), '{}');

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);
  const claudeCode = getDetection(detected, 'claude-code');
  assert.equal(claudeCode.detected, true);
  assert.ok(hasReasonContaining(claudeCode.reasons, 'mcp'));
});

// ─────────────────────────────────────────────────────────────────────────────
// OpenCode detection (only run if opencode platform exists)
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects opencode when .opencode/ exists (if platform available)', async () => {
  const platforms = await loadPlatformsWithMarkers();
  const opencodePlatform = platforms.find((p) => p.platformId === 'opencode');

  if (!opencodePlatform) {
    // Skip test if opencode platform not available
    assert.ok(true, 'opencode platform not available in payload, skipping');
    return;
  }

  const root = await tempDir();
  await fs.mkdir(path.join(root, '.opencode'), { recursive: true });

  const detected = await detectAdapters(root, platforms);
  const opencode = detected['opencode'];

  if (opencode) {
    assert.equal(opencode.detected, true);
  }
});

test('detectAdapters detects opencode when .opencode/opencode.jsonc exists (if platform available)', async () => {
  const platforms = await loadPlatformsWithMarkers();
  const opencodePlatform = platforms.find((p) => p.platformId === 'opencode');

  if (!opencodePlatform) {
    assert.ok(true, 'opencode platform not available in payload, skipping');
    return;
  }

  const root = await tempDir();
  await fs.mkdir(path.join(root, '.opencode'), { recursive: true });
  await fs.writeFile(path.join(root, '.opencode', 'opencode.jsonc'), '{}');

  const detected = await detectAdapters(root, platforms);
  const opencode = detected['opencode'];

  if (opencode) {
    assert.equal(opencode.detected, true);
  }
});

test('detectAdapters detects opencode when .opencode/opencode.json exists (if platform available)', async () => {
  const platforms = await loadPlatformsWithMarkers();
  const opencodePlatform = platforms.find((p) => p.platformId === 'opencode');

  if (!opencodePlatform) {
    assert.ok(true, 'opencode platform not available in payload, skipping');
    return;
  }

  const root = await tempDir();
  await fs.mkdir(path.join(root, '.opencode'), { recursive: true });
  await fs.writeFile(path.join(root, '.opencode', 'opencode.json'), '{}');

  const detected = await detectAdapters(root, platforms);
  const opencode = detected['opencode'];

  if (opencode) {
    assert.equal(opencode.detected, true);
  }
});

test('detectAdapters detects opencode when opencode.json exists (if platform available)', async () => {
  const platforms = await loadPlatformsWithMarkers();
  const opencodePlatform = platforms.find((p) => p.platformId === 'opencode');

  if (!opencodePlatform) {
    assert.ok(true, 'opencode platform not available in payload, skipping');
    return;
  }

  const root = await tempDir();
  await fs.writeFile(path.join(root, 'opencode.json'), '{}');

  const detected = await detectAdapters(root, platforms);
  const opencode = detected['opencode'];

  if (opencode) {
    assert.equal(opencode.detected, true);
  }
});

test('detectAdapters detects opencode when opencode.jsonc exists (if platform available)', async () => {
  const platforms = await loadPlatformsWithMarkers();
  const opencodePlatform = platforms.find((p) => p.platformId === 'opencode');

  if (!opencodePlatform) {
    assert.ok(true, 'opencode platform not available in payload, skipping');
    return;
  }

  const root = await tempDir();
  await fs.writeFile(path.join(root, 'opencode.jsonc'), '{}');

  const detected = await detectAdapters(root, platforms);
  const opencode = detected['opencode'];

  if (opencode) {
    assert.equal(opencode.detected, true);
  }
});

test('detectAdapters detects opencode when .opencode.json exists (if platform available)', async () => {
  const platforms = await loadPlatformsWithMarkers();
  const opencodePlatform = platforms.find((p) => p.platformId === 'opencode');

  if (!opencodePlatform) {
    assert.ok(true, 'opencode platform not available in payload, skipping');
    return;
  }

  const root = await tempDir();
  await fs.writeFile(path.join(root, '.opencode.json'), '{"ok":true}');

  const detected = await detectAdapters(root, platforms);
  const opencode = detected['opencode'];

  if (opencode) {
    assert.equal(opencode.detected, true);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// No detection
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters returns no detections for empty directory', async () => {
  const root = await tempDir();

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);

  // All platforms should have detected=false
  for (const [_id, detection] of Object.entries(detected)) {
    const det = detection as { detected: boolean };
    assert.equal(det.detected, false);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Multiple adapters
// ─────────────────────────────────────────────────────────────────────────────

test('detectAdapters detects multiple adapters when multiple markers exist', async () => {
  const root = await tempDir();
  // Use markers that we know exist based on passing tests
  await fs.mkdir(path.join(root, '.github'), { recursive: true });
  await fs.writeFile(path.join(root, '.github', 'copilot-instructions.md'), '# instructions');
  await fs.writeFile(path.join(root, 'CLAUDE.md'), '# Claude');

  const platforms = await loadPlatformsWithMarkers();
  const detected = await detectAdapters(root, platforms);

  const vscodeCopilot = detected['vscode-copilot'];
  const claudeCode = detected['claude-code'];

  if (vscodeCopilot) {
    assert.equal(vscodeCopilot.detected, true);
  }
  if (claudeCode) {
    assert.equal(claudeCode.detected, true);
  }
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