import { spawnSync } from 'node:child_process';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    if (entry === 'payload') continue; // generated
    const p = join(dir, entry);
    const st = statSync(p);
    if (st.isDirectory()) out.push(...walk(p));
    else if (st.isFile() && p.endsWith('.js')) out.push(p);
  }
  return out;
}

const rootPath = fileURLToPath(new URL('..', import.meta.url));

const files = walk(rootPath);
let failed = false;
for (const file of files) {
  const r = spawnSync(process.execPath, ['--check', file], { stdio: 'inherit' });
  if (r.status !== 0) failed = true;
}

process.exit(failed ? 1 : 0);
