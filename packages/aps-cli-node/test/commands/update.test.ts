import test from 'node:test';
import assert from 'node:assert/strict';

import {
  compareSemver,
  detectNodeRuntimeMode,
  fetchLatestCliVersion,
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
