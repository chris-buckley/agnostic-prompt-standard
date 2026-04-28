import path from 'node:path';

import {
  isDirectory,
  pathExists,
  loadPlatformsDetailed,
  resolvePayloadSkillDir,
  type PlatformInfo,
  type PlatformLoadIssue,
} from '../core.js';
import { parseAdaptorMd } from '../parsers/adaptor.js';

/** Known platform adapter identifiers. */
export type KnownAdapterId =
  | 'vscode-copilot'
  | 'copilot-cli'
  | 'claude-code'
  | 'opencode'
  | 'generic';

/**
 * Result of detecting a platform adapter in a workspace.
 */
export interface AdapterDetection {
  platformId: string;
  detected: boolean;
  reasons: readonly string[];
}

/**
 * A marker file or directory used to detect a platform adapter.
 */
export interface Marker {
  kind: 'file' | 'dir';
  label: string;
  relPath: string;
}

/** The default order of platform adapters for detection and display. */
export const DEFAULT_ADAPTER_ORDER: readonly KnownAdapterId[] = [
  'vscode-copilot',
  'copilot-cli',
  'claude-code',
  'opencode',
  'generic',
] as const;

/**
 * Checks if a marker file or directory exists.
 */
async function markerExists(workspaceRoot: string, marker: Marker): Promise<boolean> {
  const full = path.join(workspaceRoot, marker.relPath);
  if (marker.kind === 'dir') return isDirectory(full);
  return pathExists(full);
}

/**
 * Extended platform info including detection markers.
 */
export interface PlatformWithMarkers extends PlatformInfo {
  detectionMarkers: readonly Marker[];
}

/**
 * Convert a detection marker string array from adaptor.md into Marker objects.
 * Each string is treated as a file marker unless it ends with / (dir).
 */
function markersFromStringArray(raw: string[]): Marker[] {
  return raw.map((m) => {
    const isDir = m.endsWith('/');
    const relPath = isDir ? m.slice(0, -1) : m;
    return { kind: isDir ? ('dir' as const) : ('file' as const), label: m, relPath };
  });
}

export interface LoadPlatformsWithMarkersResult {
  platforms: PlatformWithMarkers[];
  issues: readonly PlatformLoadIssue[];
}

/**
 * Loads platforms with their detection markers from adaptor.md files.
 */
export async function loadPlatformsWithMarkersDetailed(
  skillDir?: string
): Promise<LoadPlatformsWithMarkersResult> {
  const dir = skillDir ?? (await resolvePayloadSkillDir());
  const { platforms, issues } = await loadPlatformsDetailed(dir);
  const results: PlatformWithMarkers[] = [];

  for (const platform of platforms) {
    let markers: Marker[] = [];

    try {
      const data = await parseAdaptorMd(platform.adaptorPath);
      const rawMarkers = data.constants['DETECTION_MARKERS'];
      if (Array.isArray(rawMarkers)) {
        markers = markersFromStringArray(rawMarkers.filter((m): m is string => typeof m === 'string'));
      }
    } catch {
      // Ignore marker parse errors.
    }

    results.push({ ...platform, detectionMarkers: markers });
  }

  return { platforms: results, issues };
}

/**
 * Loads platforms with their detection markers from adaptor.md files.
 */
export async function loadPlatformsWithMarkers(skillDir?: string): Promise<PlatformWithMarkers[]> {
  const { platforms } = await loadPlatformsWithMarkersDetailed(skillDir);
  return platforms;
}

/**
 * Detects which platform adapters are present in a workspace.
 */
export async function detectAdapters(
  workspaceRoot: string,
  platforms?: readonly PlatformWithMarkers[]
): Promise<Record<string, AdapterDetection>> {
  const platformList = platforms ?? (await loadPlatformsWithMarkers());
  const out: Record<string, AdapterDetection> = {};

  const detectionResults = await Promise.all(
    platformList.map(async (platform) => {
      const markerResults = await Promise.all(
        platform.detectionMarkers.map(async (m) => ((await markerExists(workspaceRoot, m)) ? m.label : null))
      );
      const reasons = markerResults.filter((r): r is string => r !== null);
      return {
        id: platform.platformId,
        detection: {
          platformId: platform.platformId,
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
 */
export function formatDetectionLabel(d: AdapterDetection): string {
  if (!d.detected) return '';
  return ' (detected)';
}

/**
 * Sorts platforms for UI display: known adapters first in defined order, then others alphabetically.
 */
export function sortPlatformsForUi<T extends { platformId: string; displayName: string }>(
  platforms: readonly T[]
): T[] {
  const knownOrder = new Map<string, number>(DEFAULT_ADAPTER_ORDER.map((id, idx) => [id, idx]));

  const known = platforms.filter((p) => knownOrder.has(p.platformId));
  const remaining = platforms.filter((p) => !knownOrder.has(p.platformId));

  known.sort((a, b) => (knownOrder.get(a.platformId) ?? 0) - (knownOrder.get(b.platformId) ?? 0));
  remaining.sort((a, b) => a.displayName.toLowerCase().localeCompare(b.displayName.toLowerCase()));

  return [...known, ...remaining];
}