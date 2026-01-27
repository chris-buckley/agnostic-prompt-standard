# ADR-003: CLI Parity and Multi-Platform Selection

**Date:** 2025-01-27
**Status:** Accepted
**Deciders:** @chris-buckley
**PR/Issue:** #13

## Context

The Node and Python CLIs for the Agnostic Prompt Standard (APS) had diverged in functionality. Users expected identical behavior regardless of which CLI they used. Additionally, users requested the ability to select multiple platform adapters in a single `init` command rather than running the command multiple times. This ADR documents all decisions made to achieve feature parity and implement multi-platform selection.

## Quick Reference

1. [Multiple Platform Selection](#1-multiple-platform-selection) — Both CLIs accept multiple platforms via the `--platform` option.
2. [Doctor Command Root Option](#2-doctor-command-root-option) — Both CLIs support `--root <path>` on the `doctor` command.
3. [Platform Detection from Manifests](#3-platform-detection-from-manifests) — Detection markers are read from manifest files, not hardcoded.
4. [Doctor JSON Output Structure](#4-doctor-json-output-structure) — Both CLIs produce identical JSON structure for `doctor --json`.
5. [Multi-Destination Skill Installation](#5-multi-destination-skill-installation) — Skills are installed to multiple destinations when mixed platforms are selected.
6. [Platform Ordering in UI](#6-platform-ordering-in-ui) — Platforms display in a fixed order with known platforms first.
7. [OpenCode Platform Status](#7-opencode-platform-status) — OpenCode is an active platform; Crush is out of scope.
8. [Schema Validation Libraries](#8-schema-validation-libraries) — Python uses Pydantic v2; Node uses Zod.
9. [Detection Marker Format](#9-detection-marker-format) — Markers support both string and object formats.
10. [File Conventions Schema](#10-file-conventions-schema) — `fileConventions` fields are arrays, not strings.
11. [Test Flexibility for Platform Availability](#11-test-flexibility-for-platform-availability) — Tests handle missing platforms gracefully.
12. [Pydantic Configuration Style](#12-pydantic-configuration-style) — Use `ConfigDict` instead of class-based `Config`.
13. [Validation Failure Handling](#13-validation-failure-handling) — Validation failures log warnings and attempt partial extraction.
14. [Marker Normalization Function](#14-marker-normalization-function) — Both CLIs implement `normalizeDetectionMarker()` for format conversion.

## Consequences

### Positive
- Users can select multiple platforms in a single command, reducing workflow friction
- Both CLIs behave identically, eliminating confusion when switching between them
- New platforms can be added via manifests without CLI code changes
- JSON output enables CI/CD integration and tooling development
- Schema validation catches malformed manifests early with clear error messages

### Negative
- Reading markers from manifests adds I/O overhead on each CLI invocation
- Supporting two marker formats increases code complexity
- Partial extraction on validation failure may mask manifest authoring errors

### Neutral
- Test suite now has conditional assertions based on platform availability
- CLI payload size unchanged (manifests already existed)
- Users with existing single-platform workflows see no behavior change

## Decisions

### 1. Multiple Platform Selection

**Decision:** Both CLIs accept multiple platforms via the `--platform` option.

**Behavior:** The Node and Python CLIs accept multiple platforms via the `--platform` option. Python uses `list[str]` type, Node uses variadic arguments. Users can specify platforms as comma-separated values (e.g., `--platform vscode-copilot,claude-code`) or multiple flags (e.g., `--platform vscode-copilot --platform claude-code`). The value `"none"` skips platform selection entirely and installs only the skill without templates.

**Rationale:** Multi-select reduces friction for users working across multiple AI coding assistants. The comma-separated and multi-flag approaches match conventions in other CLI tools (e.g., `npm`, `docker`). Node's variadic argument pattern was chosen as the reference implementation because it's more explicit than Python's previous single-value approach.

---

### 2. Doctor Command Root Option

**Decision:** Both CLIs support `--root <path>` on the `doctor` command.

**Behavior:** Both CLIs support a `--root <path>` option on the `doctor` command to specify the workspace root path. If not provided, the CLIs auto-detect the git repository root by walking up the directory tree looking for `.git/`.

**Rationale:** The Node CLI already had this option; Python was missing it. Users running doctor from subdirectories or CI environments need to specify the workspace root explicitly. Auto-detection provides a sensible default for interactive use.

---

### 3. Platform Detection from Manifests

**Decision:** Detection markers are read from manifest files, not hardcoded.

**Behavior:** Both CLIs read `detectionMarkers` from platform `manifest.json` files located at `platforms/{platform-id}/manifest.json`. Detection markers are not hardcoded in CLI source code. When a user runs `init` interactively, the CLI checks each marker against the workspace and pre-selects platforms with matching markers.

**Rationale:** Two approaches were considered:
1. **Hardcoded markers in CLI** - Faster, but requires CLI releases to add new platforms
2. **Markers in manifest files** - Slower initial load, but allows adding platforms without CLI changes

The manifest approach was chosen for maintainability. Platform authors can define their own detection markers without modifying CLI code. This aligns with the "skill as data" philosophy of APS.

---

### 4. Doctor JSON Output Structure

**Decision:** Both CLIs produce identical JSON structure for `doctor --json`.

**Behavior:** The `doctor --json` command outputs a JSON object containing:
- `workspace_root`: string or null
- `detected_adapters`: object mapping platform IDs to `{platformId, detected, reasons}` objects
- `installations`: array of objects with `scope`, `path`, and `installed` fields

Example:
```json
{
  "workspace_root": "/path/to/repo",
  "detected_adapters": {
    "vscode-copilot": {"platformId": "vscode-copilot", "detected": true, "reasons": [".github/copilot-instructions.md"]}
  },
  "installations": [
    {"scope": "repo", "path": "/path/to/repo/.github/skills/agnostic-prompt-standard", "installed": true}
  ]
}
```

**Rationale:** Node's structure was chosen as the reference because it separates concerns (detection vs. installation status) and uses an array for installations which scales better than named keys. Identical structure enables tooling (CI scripts, IDE extensions) to work with either CLI.

---

### 5. Multi-Destination Skill Installation

**Decision:** Skills are installed to multiple destinations when mixed platforms are selected.

**Behavior:** When multiple platforms are selected, the CLIs install skills to all applicable destinations. Specifically:
- If any non-Claude platform is selected → install to `.github/skills/` (repo) or `~/.copilot/skills/` (personal)
- If `claude-code` is selected → install to `.claude/skills/` (repo) or `~/.claude/skills/` (personal)
- If no platforms are selected → default to non-Claude location only

The skill payload is identical in all locations; only the path differs.

**Rationale:** Claude Code and VS Code Copilot look for skills in different directories. Installing to both ensures the skill works regardless of which tool the user runs. Defaulting to non-Claude when no selection is made preserves backwards compatibility with existing workflows.

---

### 6. Platform Ordering in UI

**Decision:** Platforms display in a fixed order with known platforms first.

**Behavior:** Both CLIs display platforms in interactive selection using this order:
1. `vscode-copilot`
2. `claude-code`
3. `opencode`
4. Any additional platforms, sorted alphabetically by display name

This order is defined in `DEFAULT_ADAPTER_ORDER` constant in both CLIs.

**Rationale:** Consistent ordering improves muscle memory for users switching between Node and Python CLIs. The specific order reflects current platform popularity and stability. New platforms appear at the end to avoid surprising existing users.

---

### 7. OpenCode Platform Status

**Decision:** OpenCode is an active platform; Crush is out of scope.

**Behavior:** OpenCode (opencode.ai / `anomalyco/opencode`) is treated as an active, supported platform in the UI and detection logic. The CLIs do not label OpenCode as "legacy" or "archived". Crush (`charmbracelet/crush`) is not included in detection or platform support.

**Rationale:** Initial implementation confused three similarly-named projects:
- **OpenCode** (`anomalyco/opencode`) - Active, this is what we support
- **Crush** (`charmbracelet/crush`) - Separate project, out of scope
- **opencode-ai/opencode** - Archived, transitioned to Crush

The "(legacy)" label was incorrectly applied based on this confusion. Removing it accurately reflects OpenCode's active status.

---

### 8. Schema Validation Libraries

**Decision:** Python uses Pydantic v2; Node uses Zod.

**Behavior:** The Python CLI uses Pydantic v2 for manifest and frontmatter validation. The Node CLI uses Zod for equivalent validation. Both validate:
- `platformId`: required, non-empty string
- `displayName`: required, non-empty string
- `adapterVersion`: optional string
- `detectionMarkers`: optional array of strings or marker objects
- `fileConventions`: optional object with array fields

**Rationale:** These are the idiomatic validation libraries for each ecosystem. Both provide TypeScript/type hint integration, good error messages, and schema composition. Pydantic v2 was specified (not v1) to use `ConfigDict` and avoid deprecation warnings.

---

### 9. Detection Marker Format

**Decision:** Markers support both string and object formats.

**Behavior:** Platform manifests can specify `detectionMarkers` in two formats:

**String format:**
```json
"detectionMarkers": [".github/agents/", "CLAUDE.md"]
```
A trailing `/` indicates a directory; no trailing slash indicates a file.

**Object format:**
```json
"detectionMarkers": [
  {"kind": "dir", "label": ".github/agents/", "relPath": ".github/agents"},
  {"kind": "file", "label": "CLAUDE.md", "relPath": "CLAUDE.md"}
]
```

Both CLIs normalize string markers to object format internally via `normalizeDetectionMarker()`. The normalized `relPath` never includes a trailing slash.

**Rationale:** String format is concise for simple cases (most markers). Object format allows custom labels and explicit kind specification for edge cases. Supporting both provides flexibility without breaking existing manifests.

---

### 10. File Conventions Schema

**Decision:** `fileConventions` fields are arrays, not strings.

**Behavior:** The `fileConventions` field in platform manifests uses arrays for all sub-fields:
```json
"fileConventions": {
  "instructions": [".github/copilot-instructions.md", ".github/instructions/*.md"],
  "agents": [".github/agents/"],
  "prompts": [".github/prompts/"],
  "skills": [".github/skills/"]
}
```

**Rationale:** The actual manifest files already used arrays. The schemas were incorrectly expecting strings. Arrays allow platforms to specify multiple valid paths for each convention (e.g., instructions in multiple locations).

---

### 11. Test Flexibility for Platform Availability

**Decision:** Tests handle missing platforms gracefully.

**Behavior:** Detection tests:
- Check if a platform exists in the payload before asserting detection behavior
- Skip assertions (pass with message) for unavailable platforms rather than failing
- Use substring matching for detection labels to accommodate varying formats

Example: OpenCode tests check `if (!opencodePlatform) { skip }` before asserting.

**Rationale:** The payload directory may not contain all platforms (e.g., during development or in minimal distributions). Hard failures for missing platforms would break CI unnecessarily. Substring matching accommodates label variations like `.github/agents/` vs `.github/agents` without brittle exact matching.

---

### 12. Pydantic Configuration Style

**Decision:** Use `ConfigDict` instead of class-based `Config`.

**Behavior:** Python models use `model_config = ConfigDict(...)` for configuration:
```python
class PlatformManifest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
```

The deprecated class-based `Config` pattern is not used.

**Rationale:** Pydantic v2 deprecated class-based `Config` with warnings indicating removal in v3. Using `ConfigDict` future-proofs the code and eliminates console warnings during test runs.

---

### 13. Validation Failure Handling

**Decision:** Validation failures log warnings and attempt partial extraction.

**Behavior:** When manifest validation fails:
1. A warning is logged to stderr with the file path and validation errors
2. The CLI attempts to extract `platformId`, `displayName`, and `adapterVersion` directly from the raw JSON
3. Detection markers are extracted if present, even if other fields failed validation
4. The platform is still included in the available platforms list

**Rationale:** Strict validation that rejects entire manifests would break users who have slightly malformed manifests. Partial extraction preserves functionality while the warning alerts users to fix their manifests. This follows the robustness principle: "Be conservative in what you send, be liberal in what you accept."

---

### 14. Marker Normalization Function

**Decision:** Both CLIs implement `normalizeDetectionMarker()` for format conversion.

**Behavior:** The `normalizeDetectionMarker()` function:
- Accepts string, dict/object, or typed marker object
- Returns normalized marker with `kind`, `label`, and `relPath` fields
- For strings: determines `kind` from trailing `/`, sets `label` to original string, strips trailing `/` for `relPath`
- For objects: extracts fields directly, supporting both `relPath` and `rel_path` key names

**Rationale:** Centralizing normalization ensures consistent behavior regardless of input format. Supporting both `relPath` (camelCase) and `rel_path` (snake_case) accommodates both JSON conventions and Python idioms.