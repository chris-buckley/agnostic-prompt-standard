import path from 'node:path';

import { isDirectory, pathExists } from '../core.js';

export type KnownAdapterId = 'vscode-copilot' | 'claude-code' | 'crush' | 'opencode';

export interface AdapterDetection {
  platformId: KnownAdapterId;
  detected: boolean;
  /** Human-readable reasons (e.g. '.github/copilot-instructions.md'). */
  reasons: readonly string[];
}

interface Marker {
  kind: 'file' | 'dir';
  /** Display label for UI. */
  label: string;
  /** Path relative to workspace root. */
  relPath: string;
}

const MARKERS: Readonly<Record<KnownAdapterId, readonly Marker[]>> = {
  'vscode-copilot': [
    { kind: 'file', label: '.github/copilot-instructions.md', relPath: '.github/copilot-instructions.md' },
    { kind: 'dir', label: '.github/agents/', relPath: '.github/agents' },
    { kind: 'dir', label: '.github/prompts/', relPath: '.github/prompts' },
    { kind: 'dir', label: '.github/instructions/', relPath: '.github/instructions' },
    { kind: 'dir', label: '.github/skills/', relPath: '.github/skills' },
  ],
  'claude-code': [
    { kind: 'dir', label: '.claude/', relPath: '.claude' },
    { kind: 'file', label: 'CLAUDE.md', relPath: 'CLAUDE.md' },
    { kind: 'file', label: 'CLAUDE.local.md', relPath: 'CLAUDE.local.md' },
    { kind: 'file', label: '.mcp.json', relPath: '.mcp.json' },
    { kind: 'file', label: '.claude/settings.json', relPath: '.claude/settings.json' },
    { kind: 'dir', label: '.claude/agents/', relPath: '.claude/agents' },
    { kind: 'dir', label: '.claude/rules/', relPath: '.claude/rules' },
  ],
  crush: [
    { kind: 'file', label: '.crush.json', relPath: '.crush.json' },
    { kind: 'file', label: 'crush.json', relPath: 'crush.json' },
    { kind: 'file', label: '.crushignore', relPath: '.crushignore' },
    { kind: 'dir', label: '.crush/', relPath: '.crush' },
  ],
  opencode: [
    { kind: 'file', label: '.opencode.json', relPath: '.opencode.json' },
    { kind: 'dir', label: '.opencode/', relPath: '.opencode' },
  ],
} as const;

export const DEFAULT_ADAPTER_ORDER: readonly KnownAdapterId[] = [
  'vscode-copilot',
  'claude-code',
  'crush',
  'opencode',
] as const;

async function markerExists(workspaceRoot: string, marker: Marker): Promise<boolean> {
  const full = path.join(workspaceRoot, marker.relPath);
  if (marker.kind === 'dir') return isDirectory(full);
  return pathExists(full);
}

export async function detectAdapters(workspaceRoot: string): Promise<Record<KnownAdapterId, AdapterDetection>> {
  const out = {} as Record<KnownAdapterId, AdapterDetection>;

  for (const id of DEFAULT_ADAPTER_ORDER) {
    const markers = MARKERS[id];
    const reasons: string[] = [];

    for (const m of markers) {
      // eslint-disable-next-line no-await-in-loop
      if (await markerExists(workspaceRoot, m)) {
        reasons.push(m.label);
      }
    }

    out[id] = {
      platformId: id,
      detected: reasons.length > 0,
      reasons,
    };
  }

  return out;
}

export function formatDetectionLabel(d: AdapterDetection): string {
  if (!d.detected) return '';
  return ' (detected)';
}
