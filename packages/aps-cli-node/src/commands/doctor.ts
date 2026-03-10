import path from 'node:path';

import { defaultPersonalSkillPath, defaultProjectSkillPath, expandHome, pathExists, pickWorkspaceRoot } from '../core.js';
import { detectAdapters, loadPlatformsWithMarkersDetailed, sortPlatformsForUi } from '../detection/adapters.js';

export interface DoctorCliOptions {
  root?: string;
  json: boolean;
  validateMcp?: boolean;
}

type McpPathScope = 'workspace' | 'user' | 'absolute';
type McpPathStatus = 'present' | 'missing' | 'skipped';

interface McpPathCheck {
  platform_id: string;
  path: string;
  resolved_path: string | null;
  scope: McpPathScope;
  exists: boolean | null;
  status: McpPathStatus;
  reason?: string;
}

interface McpValidationResult {
  enabled: true;
  checks: McpPathCheck[];
}

function normalizeDeclaredPath(p: string): string {
  return p.startsWith(`.${path.sep}`) ? p.slice(2) : p.startsWith('./') ? p.slice(2) : p;
}

function scopeForDeclaredPath(p: string): McpPathScope {
  if (p === '~' || p.startsWith('~/') || p.startsWith('~\\')) return 'user';
  if (path.isAbsolute(p)) return 'absolute';
  return 'workspace';
}

async function buildMcpValidation(
  root: string | null,
  platforms: readonly { platformId: string; mcpConfigPaths: string[] }[]
): Promise<McpValidationResult> {
  const checks: McpPathCheck[] = [];

  for (const platform of platforms) {
    for (const declared of Array.from(new Set(platform.mcpConfigPaths))) {
      const normalized = normalizeDeclaredPath(declared);
      const scope = scopeForDeclaredPath(normalized);

      if (scope === 'workspace' && !root) {
        checks.push({
          platform_id: platform.platformId,
          path: declared,
          resolved_path: null,
          scope,
          exists: null,
          status: 'skipped',
          reason: 'workspace root not detected',
        });
        continue;
      }

      const resolvedPath =
        scope === 'workspace'
          ? path.join(root ?? '.', normalized)
          : scope === 'user'
            ? expandHome(normalized)
            : normalized;

      const exists = await pathExists(resolvedPath);
      checks.push({
        platform_id: platform.platformId,
        path: declared,
        resolved_path: resolvedPath,
        scope,
        exists,
        status: exists ? 'present' : 'missing',
      });
    }
  }

  return { enabled: true, checks };
}

export async function runDoctor(options: DoctorCliOptions): Promise<void> {
  const root = await pickWorkspaceRoot(options.root);

  const { platforms, issues } = await loadPlatformsWithMarkersDetailed();

  const sortedPlatforms = sortPlatformsForUi(platforms);
  const detectedAdapters = root ? await detectAdapters(root, sortedPlatforms) : null;
  const mcpValidation = options.validateMcp ? await buildMcpValidation(root, sortedPlatforms) : null;

  const rows: Array<[string, string, boolean]> = [];

  if (root) {
    const repoSkill = defaultProjectSkillPath(root, { claude: false });
    const repoSkillClaude = defaultProjectSkillPath(root, { claude: true });
    rows.push(['repo', repoSkill, await pathExists(path.join(repoSkill, 'SKILL.md'))]);
    rows.push([
      'repo (claude)',
      repoSkillClaude,
      await pathExists(path.join(repoSkillClaude, 'SKILL.md')),
    ]);
  }

  const personalSkill = defaultPersonalSkillPath({ claude: false });
  const personalSkillClaude = defaultPersonalSkillPath({ claude: true });
  rows.push(['personal', personalSkill, await pathExists(path.join(personalSkill, 'SKILL.md'))]);
  rows.push([
    'personal (claude)',
    personalSkillClaude,
    await pathExists(path.join(personalSkillClaude, 'SKILL.md')),
  ]);

  const result = {
    workspace_root: root,
    detected_adapters: detectedAdapters,
    platform_load_issues: issues,
    installations: rows.map(([scope, p, ok]) => ({ scope, path: p, installed: ok })),
    mcp_validation: mcpValidation,
  };

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log('APS Doctor');
  console.log('----------');

  if (issues.length) {
    console.warn('Platform load warnings:');
    for (const issue of issues) {
      console.warn(`- platforms/${issue.dirName}: ${issue.message}`);
    }
    console.warn('');
  }

  console.log(`Workspace root: ${root ?? '(not detected)'}`);
  if (detectedAdapters) {
    const detected = Object.values(detectedAdapters).filter((d) => d.detected);
    console.log(
      `Detected adapters: ${detected.length ? detected.map((d) => d.platformId).join(', ') : '(none)'}`
    );
  }

  if (mcpValidation) {
    console.log('');
    console.log('MCP config paths:');
    if (mcpValidation.checks.length === 0) {
      console.log('- (none declared)');
    } else {
      for (const check of mcpValidation.checks) {
        const mark = check.status === 'present' ? '✓' : check.status === 'missing' ? '✗' : '•';
        const resolved = check.resolved_path ?? check.path;
        const detail = check.reason ? ` (${check.reason})` : '';
        console.log(`- ${check.platform_id} [${check.scope}]: ${resolved} ${mark}${detail}`);
      }
    }
  }

  console.log('');
  console.log('Installed skills:');
  for (const [scope, p, ok] of rows) {
    console.log(`- ${scope}: ${p} ${ok ? '✓' : '✗'}`);
  }
}