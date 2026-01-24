import path from 'node:path';

import { isDirectory, pathExists } from '../core.js';

/** Known platform adapter identifiers. */
export type KnownAdapterId = 'vscode-copilot' | 'claude-code' | 'crush' | 'opencode';

/**
 * Result of detecting a platform adapter in a workspace.
 */
export interface AdapterDetection {
  /** The platform adapter identifier. */
  platformId: KnownAdapterId;
  /** Whether the adapter was detected. */
  detected: boolean;
  /** Human-readable reasons (e.g. '.github/copilot-instructions.md'). */
  reasons: readonly string[];
}

/**
 * A marker file or directory used to detect a platform adapter.
 */
interface Marker {
  /** The type of marker (file or directory). */
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

/** The default order of platform adapters for detection and display. */
export const DEFAULT_ADAPTER_ORDER: readonly KnownAdapterId[] = [
  'vscode-copilot',
  'claude-code',
  'crush',
  'opencode',
] as const;

/**
 * Checks if a marker file or directory exists.
 * @param workspaceRoot - The workspace root directory.
 * @param marker - The marker to check.
 * @returns True if the marker exists.
 */
async function markerExists(workspaceRoot: string, marker: Marker): Promise<boolean> {
  const full = path.join(workspaceRoot, marker.relPath);
  if (marker.kind === 'dir') return isDirectory(full);
  return pathExists(full);
}

/**
 * Detects which platform adapters are present in a workspace.
 * @param workspaceRoot - The workspace root directory.
 * @returns A record mapping adapter IDs to their detection results.
 */
export async function detectAdapters(workspaceRoot: string): Promise<Record<KnownAdapterId, AdapterDetection>> {
  const out = {} as Record<KnownAdapterId, AdapterDetection>;

  // Check all adapters in parallel
  const detectionResults = await Promise.all(
    DEFAULT_ADAPTER_ORDER.map(async (id) => {
      const markers = MARKERS[id];
      const markerResults = await Promise.all(
        markers.map(async (m) => (await markerExists(workspaceRoot, m)) ? m.label : null)
      );
      const reasons = markerResults.filter((r): r is string => r !== null);
      return {
        id,
        detection: {
          platformId: id,
          detected: reasons.length > 0,
          reasons,
        },
      };
    })
  );

  for (const { id, detection } of detectionResults) {
    out[id] = detection;
  }

  return out;
}

/**
 * Formats a detection result as a label suffix.
 * @param d - The adapter detection result.
 * @returns A label suffix like ' (detected)' or empty string.
 */
export function formatDetectionLabel(d: AdapterDetection): string {
  if (!d.detected) return '';
  return ' (detected)';
}
