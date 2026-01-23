import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { findRepoRoot, inferPlatformId } from '../dist/core.js';
async function tempDir() {
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
//# sourceMappingURL=core.test.js.map