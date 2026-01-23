import path from 'node:path';

import {
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  findRepoRoot,
  inferPlatformId,
  pathExists,
} from '../core.js';
import { detectAdapters } from '../detection/adapters.js';

export interface DoctorCliOptions {
  root?: string;
  json: boolean;
}

async function pickWorkspaceRoot(cliRoot: string | undefined): Promise<string | null> {
  if (cliRoot) return path.resolve(cliRoot);
  return findRepoRoot(process.cwd());
}

export async function runDoctor(options: DoctorCliOptions): Promise<void> {
  const root = await pickWorkspaceRoot(options.root);
  const detectedPlatform = root ? inferPlatformId(root) : null;
  const detectedAdapters = root ? await detectAdapters(root) : null;

  const rows: Array<[string, string, boolean]> = [];

  if (root) {
    const repoSkill = defaultProjectSkillPath(root, { claude: false });
    const repoSkillClaude = defaultProjectSkillPath(root, { claude: true });
    rows.push(['repo', repoSkill, await pathExists(path.join(repoSkill, 'SKILL.md'))]);
    rows.push(['repo (claude)', repoSkillClaude, await pathExists(path.join(repoSkillClaude, 'SKILL.md'))]);
  }

  const personalSkill = defaultPersonalSkillPath({ claude: false });
  const personalSkillClaude = defaultPersonalSkillPath({ claude: true });
  rows.push(['personal', personalSkill, await pathExists(path.join(personalSkill, 'SKILL.md'))]);
  rows.push(['personal (claude)', personalSkillClaude, await pathExists(path.join(personalSkillClaude, 'SKILL.md'))]);

  const result = {
    workspace_root: root,
    detected_platform: detectedPlatform,
    detected_adapters: detectedAdapters,
    installations: rows.map(([scope, p, ok]) => ({ scope, path: p, installed: ok })),
  };

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log('APS Doctor');
  console.log('----------');
  console.log(`Workspace root: ${root ?? '(not detected)'}`);
  console.log(`Detected platform (heuristic): ${detectedPlatform ?? '(none)'}`);
  if (detectedAdapters) {
    const detected = Object.values(detectedAdapters).filter((d) => d.detected);
    console.log(`Detected adapters: ${detected.length ? detected.map((d) => d.platformId).join(', ') : '(none)'}`);
  }
  console.log('');
  console.log('Installed skills:');
  for (const [scope, p, ok] of rows) {
    console.log(`- ${scope}: ${p} ${ok ? '✓' : '✗'}`);
  }
}
