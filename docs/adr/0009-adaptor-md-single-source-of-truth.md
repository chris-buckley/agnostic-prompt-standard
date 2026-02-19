# ADR-009: adaptor.md as Single Source of Truth for Platform Adapters

**Date:** 2026-02-19
**Status:** Accepted
**Deciders:** @chris-buckley
**PR/Issue:** #43

## Context

Platform adapters previously scattered configuration across multiple files per platform:
- `manifest.json` — platform metadata, file conventions, detection markers, agent versioning config
- `tools-registry.json` — tool names, sets, and mappings
- `frontmatter/*.md` — separate files for each frontmatter template (agent, rules, instructions, etc.)
- `README.md` — per-platform quickstart and usage guide
- `_schemas/*.json` — JSON Schema files for validating manifests and tool registries

This multi-file approach created several problems:
1. **Information duplication** — the same data existed in both JSON config and markdown docs
2. **Sync drift** — changes to one file required updating others, leading to inconsistencies
3. **Parser complexity** — both CLIs needed JSON manifest parsers, Zod/Pydantic schemas, and normalisation logic alongside the new adaptor.md parser
4. **Onboarding friction** — contributors had to understand multiple file formats and their relationships

APS already defines a structured envelope format (`<instructions>`, `<constants>`, `<formats>`) with block constant types (TEXT, JSON, CSV). A single `adaptor.md` file using this format can express everything the scattered files contained, and the envelope format is self-documenting.

## Quick Reference

1. [Single adaptor.md per Platform](#1-single-adaptormd-per-platform) — Each platform has exactly one configuration file.
2. [Remove Manifest Fallback](#2-remove-manifest-fallback) — CLIs read only from adaptor.md, no JSON fallback.
3. [Delete Legacy Files](#3-delete-legacy-files) — Remove manifest.json, tools-registry.json, frontmatter/, _schemas/.
4. [Block Constants for Structured Data](#4-block-constants-for-structured-data) — Use CSV and JSON block types for tools and versioning config.

## Consequences

### Positive
- Single file to read, edit, and maintain per platform
- Platform adapters are themselves valid APS documents, demonstrating the standard
- Format contracts in `<formats>` replace separate frontmatter template files
- CSV block constants provide a compact, readable tool registry
- Reduced code complexity: manifest Zod/Pydantic schemas, normalisation functions, and fallback logic are removed
- New platforms only need to create one `adaptor.md` file

### Negative
- Breaking change for any external tooling that consumed `manifest.json` or `tools-registry.json` directly
- ADR-002 (fileConventions required in manifest) and ADR-007 decision 4 (versioning config in manifest.json) are superseded

### Neutral
- `bump_version.py` continues to manage agent template versioning, now reading/writing AGENT_VERSIONING JSON blocks in adaptor.md instead of manifest.json
- The `_template/` directory provides a starter `adaptor.md` for new platform adapters

---

## Decisions

### 1. Single adaptor.md per Platform

Each platform directory contains exactly one `adaptor.md` file structured as an APS envelope:

```
<instructions>
Platform-specific generation instructions.
</instructions>

<constants>
PLATFORM_ID: "platform-id"
DISPLAY_NAME: "Platform Name"
TOOLS: CSV<<
name,risk,description
...
>>
AGENT_VERSIONING: JSON<<
{ "templates": [...] }
>>
</constants>

<formats>
<format id="..." name="..." purpose="...">
...
</format>
</formats>
```

**Decision:** Each platform has exactly one `adaptor.md` file using the APS envelope format (`<instructions>`, `<constants>`, `<formats>`) as its single source of truth for all configuration, tools, and format contracts.

**Rationale:** APS's own envelope format is expressive enough to hold all platform configuration. Using it for adapters means the adapters are self-documenting APS examples, and a single parser handles everything.

### 2. Remove Manifest Fallback

Both CLIs (Node and Python) load platforms exclusively from `adaptor.md`. The previous two-stage loading pattern (prefer adaptor.md, fall back to manifest.json) is removed.

**Decision:** CLIs load platform configuration only from `adaptor.md`, with no fallback to `manifest.json`. If `adaptor.md` is missing or unparseable, the platform is skipped.

**Rationale:** Maintaining dual parsing paths added complexity and made it unclear which file was authoritative. With all platforms migrated to adaptor.md, the fallback is unnecessary.

### 3. Delete Legacy Files

The following file types are removed from all platform directories:
- `manifest.json` — replaced by `<constants>` in adaptor.md
- `tools-registry.json` — replaced by `TOOLS: CSV<<` block constant
- `frontmatter/*.md` — replaced by `<formats>` section format contracts
- `_schemas/` — JSON Schema validation replaced by adaptor.md parser
- Per-platform `README.md` — instructions moved to `<instructions>` section

**Decision:** Remove `manifest.json`, `tools-registry.json`, `frontmatter/` directories, `_schemas/` directory, and per-platform `README.md` files from all platform directories.

**Rationale:** These files are fully superseded. Keeping them would invite sync drift and confusion about which source is authoritative.

### 4. Block Constants for Structured Data

Tool registries use `CSV<<` block constants for compact, readable representation. Agent versioning config uses `JSON<<` block constants for structured nested data. Both use the APS v1.0 block constant syntax with `<<` opener and `>>` closer.

**Decision:** Use `CSV<<` block constants for tool registries and `JSON<<` block constants for agent versioning configuration within `adaptor.md`.

**Rationale:** CSV is ideal for tabular tool data (many rows, fixed columns). JSON is ideal for the nested versioning config structure. Both are first-class APS constant types that parsers already handle.
