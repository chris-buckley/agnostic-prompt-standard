import { z } from 'zod';

/**
 * Schema for SKILL.md frontmatter.
 * Validates the YAML frontmatter structure in skill files.
 */
export const SkillFrontmatterSchema = z
  .object({
    name: z.string().optional(),
    version: z.string().optional(),
    description: z.string().optional(),
    author: z.string().optional(),
    license: z.string().optional(),
  })
  .passthrough();

export type SkillFrontmatter = z.infer<typeof SkillFrontmatterSchema>;

/**
 * Parses and validates skill frontmatter.
 * @param data - The raw frontmatter data to validate.
 * @returns The validated SkillFrontmatter or throws a ZodError.
 */
export function parseSkillFrontmatter(data: unknown): SkillFrontmatter {
  return SkillFrontmatterSchema.parse(data);
}

/**
 * Safely parses skill frontmatter without throwing.
 * @param data - The raw frontmatter data to validate.
 * @returns A Zod SafeParseReturnType with the result.
 */
export function safeParseSkillFrontmatter(data: unknown): z.SafeParseReturnType<unknown, SkillFrontmatter> {
  return SkillFrontmatterSchema.safeParse(data);
}
