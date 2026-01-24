import test from 'node:test';
import assert from 'node:assert/strict';

// ─────────────────────────────────────────────────────────────────────────────
// CLI entry point tests
// ─────────────────────────────────────────────────────────────────────────────

test('main function is exported', async () => {
  const { main } = await import('../dist/cli.js');
  assert.equal(typeof main, 'function');
});

test('CLI module exports main as async function', async () => {
  const cliModule = await import('../dist/cli.js');
  assert.ok('main' in cliModule);
  assert.equal(typeof cliModule.main, 'function');
});
