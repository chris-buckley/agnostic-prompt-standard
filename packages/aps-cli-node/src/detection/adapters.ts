import path from 'node:path';
import fs from 'node:fs/promises';

import { isDirectory, pathExists, loadPlatforms, resolvePayloadSkillDir, type PlatformInfo } from '../core.js';
import { safeParsePlatformManifest, normalizeDetectionMarker, type DetectionMarker } from '../schemas/index.js';

/** Known platform adapter identifiers. */
export type KnownAdapterId = 'vscode-copilot' | 'claude-code' | 'opencode';

/**
 * Result of detecting a platform adapter in a workspace.
 */
export interface AdapterDetection {
  /** The platform adapter identifier. */
  platformId: string;
  /** Whether the adapter was detected. */
  detected: boolean;
  /** Human-readable reasons (e.g. '.github/copilot-instructions.md'). */
  reasons: readonly string[];
}

/**
 * A marker file or directory used to detect a platform adapter.
 */
export interface Marker {
  /** The type of marker (file or directory). */
  kind: 'file' | 'dir';
  /** Display label for UI. */
  label: string;
  /** Path relative to workspace root. */
  relPath: string;
}

/** The default order of platform adapters for detection and display. */
export const DEFAULT_ADAPTER_ORDER: readonly KnownAdapterId[] = [
  'vscode-copilot',
  'claude-code',
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
 * Extended platform info including detection markers.
 */
export interface PlatformWithMarkers extends PlatformInfo {
  detectionMarkers: readonly Marker[];
}

/**
 * Loads platforms with their detection markers from manifest files.
 * @param skillDir - The skill directory containing platforms.
 * @returns Array of platforms with detection markers.
 */
export async function loadPlatformsWithMarkers(skillDir?: string): Promise<PlatformWithMarkers[]> {
  const dir = skillDir ?? await resolvePayloadSkillDir();
  const platforms = await loadPlatforms(dir);
  const results: PlatformWithMarkers[] = [];

  for (const platform of platforms) {
    const manifestPath = path.join(dir, 'platforms', platform.platformId, 'manifest.json');
    let markers: Marker[] = [];

    try {
      const raw = await fs.readFile(manifestPath, 'utf8');
      const parsed: unknown = JSON.parse(raw);

      // Validate with Zod schema
      const result = safeParsePlatformManifest(parsed);
      if (result.success && result.data.detectionMarkers) {
        // Normalize markers (handle both string and object formats)
        markers = result.data.detectionMarkers.map((m) => {
          const normalized: DetectionMarker = normalizeDetectionMarker(m);
          return {
            kind: normalized.kind,
            label: normalized.label,
            relPath: normalized.relPath,
          };
        });
      } else if (!result.success) {
        console.warn(`Warning: Invalid platform manifest at ${manifestPath}: ${JSON.stringify(result.error.errors, null, 2)}`);
      }
    } catch {
      // No manifest or invalid JSON - continue with empty markers
    }

    results.push({
      ...platform,
      detectionMarkers: markers,
    });
  }

  return results;
}

/**
 * Detects which platform adapters are present in a workspace.
 * Reads detection markers from platform manifests.
 * @param workspaceRoot - The workspace root directory.
 * @param platforms - Optional pre-loaded platforms with markers.
 * @returns A record mapping adapter IDs to their detection results.
 */
export async function detectAdapters(
  workspaceRoot: string,
  platforms?: readonly PlatformWithMarkers[]
): Promise<Record<string, AdapterDetection>> {
  const platformList = platforms ?? await loadPlatformsWithMarkers();
  const out: Record<string, AdapterDetection> = {};

  // Check all adapters in parallel
  const detectionResults = await Promise.all(
    platformList.map(async (platform) => {
      const markerResults = await Promise.all(
        platform.detectionMarkers.map(async (m) =>
          (await markerExists(workspaceRoot, m)) ? m.label : null
        )
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
 * @param d - The adapter detection result.
 * @returns A label suffix like ' (detected)' or empty string.
 */
export function formatDetectionLabel(d: AdapterDetection): string {
  if (!d.detected) return '';
  return ' (detected)';
}