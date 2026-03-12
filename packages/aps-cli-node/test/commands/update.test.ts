import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import {
  collectSkillTargets,
  compareSemver,
  detectNodeRuntimeMode,
  fetchLatestCliVersion,
  inferInstalledSkillVersion,
} from '../../dist/commands/update.js';

test('compareSemver orders semver versions correctly', () => {
  assert.equal(compareSemver('1.2.0', '1.1.9'), 1);
  assert.equal(compareSemver('1.1.9', '1.2.0'), -1);
  assert.equal(compareSemver('1.2.0', '1.2.0'), 0);
});

test('detectNodeRuntimeMode classifies dev-local paths', () => {
  const mode = detectNodeRuntimeMode('/repo/agnostic-prompt-standard/packages/aps-cli-node/bin/aps.js');
  assert.equal(mode, 'dev-local');
});

test('detectNodeRuntimeMode classifies npx cache paths', () => {
  const mode = detectNodeRuntimeMode('/home/user/.npm/_npx/123/node_modules/@agnostic-prompt/aps/bin/aps.js');
  assert.equal(mode, 'ephemeral');
});

test('detectNodeRuntimeMode classifies local project installs', () => {
  const mode = detectNodeRuntimeMode('/repo/project/node_modules/@agnostic-prompt/aps/bin/aps.js');
  assert.equal(mode, 'local-project');
});

test('detectNodeRuntimeMode defaults to installed', () => {
  const mode = detectNodeRuntimeMode('/usr/local/lib/node_modules/@agnostic-prompt/aps/bin/aps.js');
  assert.equal(mode, 'installed');
});

test('fetchLatestCliVersion reads npm dist-tags latest', async () => {
  const latest = await fetchLatestCliVersion(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ 'dist-tags': { latest: '1.2.3' } }),
  }) as Response);

  assert.equal(latest, '1.2.3');
});

test('fetchLatestCliVersion rejects invalid dist-tag responses', async () => {
  await assert.rejects(
    fetchLatestCliVersion(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ 'dist-tags': { latest: 'latest' } }),
    }) as Response),
    /valid latest dist-tag/
  );
});


async function tempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), 'aps-cli-node-update-'));
}

test('inferInstalledSkillVersion uses versioned adapter artifacts when SKILL.md is missing', async () => {
  const skillDir = await tempDir();
  const adaptorDir = path.join(skillDir, 'platforms', 'claude-code');
  const templateDir = path.join(skillDir, 'platforms', 'vscode-copilot', 'templates', '.github', 'agents');

  await fs.mkdir(adaptorDir, { recursive: true });
  await fs.mkdir(templateDir, { recursive: true });
  await fs.writeFile(
    path.join(adaptorDir, 'adaptor.md'),
    'current_path: "templates/.claude/agents/aps-v1.1.16.md"\n',
  );
  await fs.writeFile(path.join(templateDir, 'aps-v1.1.16.agent.md'), '# agent\n');

  const version = await inferInstalledSkillVersion(skillDir);
  assert.equal(version, '1.1.16');
});

test('collectSkillTargets includes orphaned installs when the directory exists without SKILL.md', async () => {
  const workspaceRoot = await tempDir();
  const skillDir = path.join(workspaceRoot, '.github', 'skills', 'agnostic-prompt-standard');
  const templateDir = path.join(skillDir, 'platforms', 'vscode-copilot', 'templates', '.github', 'agents');

  await fs.mkdir(templateDir, { recursive: true });
  await fs.writeFile(path.join(templateDir, 'aps-v1.1.16.agent.md'), '# agent\n');

  const targets = await collectSkillTargets({
    root: workspaceRoot,
    repo: true,
    personal: false,
    desiredVersion: '1.2.0',
  });

  const orphaned = targets.filter(t => t.status === 'orphaned');
  assert.equal(orphaned.length, 1);
  assert.equal(orphaned[0]?.scope, 'repo');
  assert.equal(orphaned[0]?.installedVersion, '1.1.16');
});
