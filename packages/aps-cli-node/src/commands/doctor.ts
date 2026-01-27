import path from 'node:path';

import {
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  pathExists,
  pickWorkspaceRoot,
  resolvePayloadSkillDir,
} from '../core.js';
import { detectAdapters, loadPlatformsWithMarkers, sortPlatformsForUi } from '../detection/adapters.js';

export interface DoctorOptions {
  root?: string;
  json?: boolean;
}

interface InstallationRow {
  scope: string;
  path: string;
  installed: boolean;
}

export async function runDoctor(opts: DoctorOptions): Promise<void> {
  const root = await pickWorkspaceRoot(opts.root);

  let detectedAdapters = null;
  if (root) {
    const payloadSkillDir = await resolvePayloadSkillDir();
    const platforms = sortPlatformsForUi(await loadPlatformsWithMarkers(payloadSkillDir));
    detectedAdapters = await detectAdapters(root, platforms);
  }

  const installations: InstallationRow[] = [];

  if (root) {
    const repoSkill = defaultProjectSkillPath(root, { claude: false });
    const repoSkillClaude = defaultProjectSkillPath(root, { claude: true });
    installations.push({
      scope: 'repo',
      path: repoSkill,
      installed: await pathExists(path.join(repoSkill, 'SKILL.md')),
    });
    installations.push({
      scope: 'repo (claude)',
      path: repoSkillClaude,
      installed: await pathExists(path.join(repoSkillClaude, 'SKILL.md')),
    });
  }

  const personalSkill = defaultPersonalSkillPath({ claude: false });
  const personalSkillClaude = defaultPersonalSkillPath({ claude: true });
  installations.push({
    scope: 'personal',
    path: personalSkill,
    installed: await pathExists(path.join(personalSkill, 'SKILL.md')),
  });
  installations.push({
    scope: 'personal (claude)',
    path: personalSkillClaude,
    installed: await pathExists(path.join(personalSkillClaude, 'SKILL.md')),
  });

  const result = {
    workspace_root: root,
    detected_adapters: detectedAdapters,
    installations,
  };

  if (opts.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log('APS Doctor');
  console.log('----------');
  console.log(`Workspace root: ${root ?? '(not detected)'}`);

  if (detectedAdapters) {
    const detected = Object.values(detectedAdapters).filter((d) => d.detected);
    console.log(`Detected adapters: ${detected.length ? detected.map((d) => d.platformId).join(', ') : '(none)'}`);
  }
  console.log('');

  console.log('Installed skills:');
  for (const inst of installations) {
    const status = inst.installed ? '✓' : '✗';
    console.log(`- ${inst.scope}: ${inst.path} ${status}`);
  }
}
