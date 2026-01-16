import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const pkgRoot = path.resolve(here, '..');
const repoRoot = path.resolve(pkgRoot, '..', '..');

const src = path.join(repoRoot, 'skill', 'agnostic-prompt-standard');
const dst = path.join(pkgRoot, 'payload', 'agnostic-prompt-standard');

async function main() {
  // Clean target
  await fs.rm(dst, { recursive: true, force: true });
  await fs.mkdir(path.dirname(dst), { recursive: true });
  await fs.cp(src, dst, { recursive: true });
  console.log(`Synced APS skill payload -> ${dst}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
