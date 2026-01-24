import { z } from 'zod';

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
      instructions: z.string().optional(),
      agents: z.string().optional(),
      prompts: z.string().optional(),
      skills: z.string().optional(),
    })
    .optional(),
});

export type PlatformManifest = z.infer<typeof PlatformManifestSchema>;

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
