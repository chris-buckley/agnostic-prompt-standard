// Core platform/tool detection and loading logic for APS CLI

import { randomUUID } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { existsSync, type Dirent } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { parseAdaptorMd, parseAdaptorMdString, getString, getStringArray } from './parsers/adaptor.js';

export const APS\_PAYLOAD\_SKILL\_DIR = 'skill/agnostic-prompt-standard';
export const SKILL\_ID = 'agnostic-prompt-standard' as const;

export const LEGACY\_AGENT\_NAMES = [
'aps-prompt-protocol.agent.md',
'aps-agent-protocol.md'
];

/\*\*

  * Determine if a path exists.
    \*/
    export async function pathExists(p: string): Promise&lt;boolean&gt; {
    try {
    await fs.access(p);
    return true;
    } catch {
    return false;
    }
    }

/\*\*

  * Determine if a path is a directory.
    \*/
    export async function isDirectory(p: string): Promise&lt;boolean&gt; {
    try {
    const stat = await fs.stat(p);
    return stat.isDirectory();
    } catch {
    return false;
    }
    }

/\*\*

  * Resolve the APS skill directory.
  * 
  * Resolution order:
  * 1)  Bundled package payload (works for `npx @agnostic-prompt/aps ...`)
  * 2)  Monorepo dev layout relative to cwd
        \*/
        export async function resolvePayloadSkillDir(): Promise&lt;string&gt; {
        // Packaged payload (dist/.. -\> payload/&lt;skill&gt;)
        const here = path.dirname(fileURLToPath(import.meta.url));
        const packaged = path.resolve(here, '..', 'payload', SKILL\_ID);
        if (await isDirectory(packaged)) return packaged;

// Monorepo/dev fallback: look relative to where the user invoked the CLI.
const cwd = process.cwd();
const candidate = path.join(cwd, APS\_PAYLOAD\_SKILL\_DIR);
if (await isDirectory(candidate)) return candidate;

const up = path.resolve(cwd, '..', '..', APS\_PAYLOAD\_SKILL\_DIR);
if (await isDirectory(up)) return up;

throw new Error(`Cannot locate payload skill directory. Tried: ${packaged}, ${candidate}, ${up}`);
}

/\*\*

  * Get default personal skill path for a given platform.
    \*/
    export function defaultPersonalSkillPath(opts: { claude?: boolean } = {}): string {
    if (opts.claude) return path.join(os.homedir(), '.claude', 'skills', 'agnostic-prompt-standard');
    return path.join(os.homedir(), '.copilot', 'skills', 'agnostic-prompt-standard');
    }

/\*\*

  * Get default project skill path for a given workspace root.
    \*/
    export function defaultProjectSkillPath(workspaceRoot: string, opts: { claude?: boolean } = {}): string {
    if (opts.claude) return path.join(workspaceRoot, '.claude', 'skills', 'agnostic-prompt-standard');
    return path.join(workspaceRoot, '.github', 'skills', 'agnostic-prompt-standard');
    }

/\*\*

  * Check if a platform uses Claude-specific install paths.
    \*/
    export function isClaudePlatform(platformId: string): boolean {
    return platformId === 'claude-code';
    }

/\*\*

  * Check if a platform is install-family neutral.
    \*/
    export function isGenericPlatform(platformId: string): boolean {
    return platformId === 'generic';
    }

/\*\*

  * Compute which install families are required for a selection of platform adapters.
  * Neutral adapters such as `generic` do not force a concrete install family.
    \*/
    export function computeInstallFamilies(
    selectedPlatforms: readonly string[]
    ): { includeClaude: boolean; includeNonClaude: boolean } {
    const concretePlatforms = selectedPlatforms.filter((p) =\> \!isGenericPlatform(p));
    const wantsClaude = concretePlatforms.some((p) =\> isClaudePlatform(p));
    const wantsNonClaude = concretePlatforms.some((p) =\> \!isClaudePlatform(p));

return {
includeClaude: wantsClaude,
includeNonClaude: wantsNonClaude || concretePlatforms.length === 0,
};
}

/\*\*

  * Infer a platform adapter from workspace markers.
    \*/
    export function inferPlatformId(workspaceRoot: string): 'vscode-copilot' | null {
    const prompts = path.join(workspaceRoot, '.github', 'prompts');
    if (existsSync(prompts)) return 'vscode-copilot';
    return null;
    }

/\*\*

  * Pick the workspace root. Uses a provided path or attempts to infer from cwd.
    \*/
    export async function pickWorkspaceRoot(root?: string): Promise\<string | null\> {
    if (root) return path.resolve(expandHome(root));
    return findRepoRoot(process.cwd());
    }

/\*\*

  * Information about a platform adapter.
    \*/
    export interface PlatformInfo {
    platformId: string;
    dirName: string;
    adaptorPath: string;
    displayName: string;
    adapterVersion: string | null;
    mcpConfigPaths: string[];
    }

export type PlatformLoadIssueKind =
| 'missing\_adaptor'
| 'parse\_error'
| 'missing\_required\_constant'
| 'id\_mismatch';

export interface PlatformLoadIssue {
dirName: string;
kind: PlatformLoadIssueKind;
message: string;
}

export interface LoadPlatformsResult {
platforms: PlatformInfo[];
issues: PlatformLoadIssue[];
}

/\*\*

  * Loads all platform adapters from the skill's platforms directory.
    \*/
    export async function loadPlatformsDetailed(skillDir: string): Promise&lt;LoadPlatformsResult&gt; {
    const platformsDir = path.join(skillDir, 'platforms');
    let entries: Dirent[];

try {
entries = await fs.readdir(platformsDir, { withFileTypes: true });
} catch {
return { platforms: [], issues: [] };
}

const platforms: PlatformInfo[] = [];
const issues: PlatformLoadIssue[] = [];

const platformDirs = entries.filter((e) =\> e.isDirectory() && \!e.name.startsWith('\_'));

for (const entry of platformDirs) {
const dirName = entry.name;
const platformDir = path.join(platformsDir, dirName);
const adaptorPath = path.join(platformDir, 'adaptor.md');

