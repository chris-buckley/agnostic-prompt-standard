import { z } from 'zod';

/**
 * Schema for detection marker objects in platform manifests.
 * Supports both object format and simple string format.
 */
export const DetectionMarkerSchema = z.union([
  z.object({
    kind: z.enum(['file', 'dir']),
    label: z.string(),
    relPath: z.string(),
  }),
  z.string(),
]);

export type DetectionMarkerInput = z.infer<typeof DetectionMarkerSchema>;

/**
 * Normalized detection marker with all fields.
 */
export interface DetectionMarker {
  kind: 'file' | 'dir';
  label: string;
  relPath: string;
}

/**
 * Schema for platform manifest.json files.
 * Validates the structure of platform adapter manifests.
 */
export const PlatformManifestSchema = z.object({
  platformId: z.string().min(1, 'platformId is required'),
  displayName: z.string().min(1, 'displayName is required'),
  adapterVersion: z.string().nullable().optional(),
  description: z.string().optional(),
  skillRoot: z.string().optional(),
  fileConventions: z
    .object({
      instructions: z.array(z.string()).optional(),
      agents: z.array(z.string()).optional(),
      prompts: z.array(z.string()).optional(),
      skills: z.array(z.string()).optional(),
    })
    .optional(),
  detectionMarkers: z.array(DetectionMarkerSchema).optional(),
});

export type PlatformManifest = z.infer<typeof PlatformManifestSchema>;

/**
 * Converts a detection marker input (string or object) to normalized Marker format.
 * @param input - String path or marker object
 * @returns Normalized DetectionMarker
 */
export function normalizeDetectionMarker(input: DetectionMarkerInput): DetectionMarker {
  if (typeof input === 'string') {
    // String format: ".github/agents/" -> dir, ".github/copilot-instructions.md" -> file
    const isDir = input.endsWith('/');
    const relPath = isDir ? input.slice(0, -1) : input;
    return {
      kind: isDir ? 'dir' : 'file',
      label: input,
      relPath,
    };
  }
  return input;
}

/**
 * Parses and validates a platform manifest object.
 * @param data - The raw data to validate.
 * @returns The validated PlatformManifest or throws a ZodError.
 */
export function parsePlatformManifest(data: unknown): PlatformManifest {
  return PlatformManifestSchema.parse(data);
}

/**
 * Safely parses a platform manifest without throwing.
 * @param data - The raw data to validate.
 * @returns A Zod SafeParseReturnType with the result.
 */
export function safeParsePlatformManifest(data: unknown): z.SafeParseReturnType<unknown, PlatformManifest> {
  return PlatformManifestSchema.safeParse(data);
}