export {
  PlatformManifestSchema,
  DetectionMarkerSchema,
  type PlatformManifest,
  type DetectionMarker,
  type DetectionMarkerInput,
  parsePlatformManifest,
  safeParsePlatformManifest,
  normalizeDetectionMarker,
} from './platform.js';

export {
  SkillFrontmatterSchema,
  type SkillFrontmatter,
  parseSkillFrontmatter,
  safeParseSkillFrontmatter,
} from './skill.js';