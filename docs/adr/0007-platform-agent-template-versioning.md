# ADR-007: Platform Agent Template Versioning

**Date:** 2026-02-04
**Status:** Accepted
**Deciders:** @chris-buckley
**PR/Issue:** #22

## Context

The APS skill includes platform-specific agent templates (e.g., `aps-prompt-protocol.agent.md` for VS Code, `aps-agent-protocol.md` for Claude Code) that help users generate APS-compliant prompts. These templates had no version identifier, making it impossible for users to know which APS version an installed agent targets. When users updated the APS skill, they had no way to verify their agent was current or identify version mismatches between the skill and agent templates.

Additionally, different platforms have different conventions for agent frontmatter:
- VS Code Copilot uses human-readable names: `name: "APS v1.0 Agent"`
- Claude Code uses slug-style identifiers: `name: aps-agent-protocol`

A versioning solution needed to handle these platform-specific differences while maintaining a single source of truth for the version number.

## Quick Reference

1. [Three-Number Semver in Agent Names](#1-three-number-semver-in-agent-names) — Agent versions use full semver (v1.1.7 not v1.1).
2. [Agent Version Parity with CLI](#2-agent-version-parity-with-cli) — Agent version must exactly match CLI version.
3. [Simplified Agent Filename](#3-simplified-agent-filename) — Agent files use `aps-v{version}` naming pattern.
4. [Platform-Specific Versioning Config](#4-platform-specific-versioning-config) — Each platform's manifest.json defines its own versioning patterns.
5. [Automatic Version Bump](#5-automatic-version-bump) — bump_version.py updates agent templates alongside core files.

## Consequences

### Positive
- Users can immediately identify which APS version an agent targets from the filename and frontmatter
- Version mismatches between CLI and agent templates are impossible when using bump_version.py
- Adding new platforms requires only manifest configuration, no script changes
- Simplified `aps-v{version}` naming is easy to recognize and sort

### Negative
- Previous agent files become orphaned after version bumps (old files must be manually deleted or gitignored)
- Users who manually edited agent templates will need to re-apply customizations after updates
- File renames on each version bump create larger git diffs

### Neutral
- The bump_version.py script gains additional responsibilities
- Platform manifests grow slightly larger with versioning configuration
- Test coverage for versioning adds maintenance overhead

## Decisions

### 1. Three-Number Semver in Agent Names

**Decision:** Agent versions use full semver format (v1.1.7 not v1.1).

**Behavior:** All version references in agent filenames and frontmatter use the complete `{major}.{minor}.{patch}` format. For example: `aps-v1.1.7.agent.md`, not `aps-v1.1.agent.md`.

**Rationale:** Two formats were considered:
1. **Two-number (major.minor)** — Shorter, assumes patches don't affect agent behavior
2. **Three-number (major.minor.patch)** — Explicit, matches CLI versioning exactly

The three-number format was chosen to maintain exact parity with the CLI version. This eliminates any ambiguity about which specific release an agent corresponds to. If a patch release includes bug fixes to agent templates (e.g., fixing a typo in instructions), users should be able to identify whether they have that fix. The slight increase in filename length is an acceptable tradeoff for clarity.

---

### 2. Agent Version Parity with CLI

**Decision:** Agent version must exactly match CLI version.

**Behavior:** When `bump_version.py` updates the version, it updates all four core files (SKILL.md, package.json, pyproject.toml, __init__.py) AND all platform agent templates simultaneously. The agent version is derived from the same version string, ensuring they cannot diverge.

**Rationale:** Independent versioning was rejected because:
- It would require tracking multiple version numbers
- Users would need to understand the relationship between CLI and agent versions
- Mismatched versions could cause subtle compatibility issues

By enforcing parity, users can trust that `aps-v1.1.7.agent.md` works with CLI version 1.1.7. The bump_version.py script is the single mechanism for version updates, preventing accidental divergence.

---

### 3. Simplified Agent Filename

**Decision:** Agent files use `aps-v{version}` naming pattern.

**Behavior:** Agent templates are named `aps-v{major}.{minor}.{patch}.agent.md` (VS Code) or `aps-v{major}.{minor}.{patch}.md` (Claude Code). The previous descriptive suffixes (`-prompt-protocol`, `-agent-protocol`) are dropped.

**Rationale:** Three naming approaches were considered:
1. **Keep descriptive names:** `aps-prompt-protocol-v1.1.7.agent.md` — Long, redundant since it's in an `agents/` folder
2. **Platform-prefixed:** `vscode-aps-v1.1.7.agent.md` — Redundant since it's in a platform-specific folder
3. **Simple version only:** `aps-v1.1.7.agent.md` — Short, clear, consistent across platforms

The simplified naming was chosen for brevity and clarity. The `aps-` prefix identifies it as an APS agent, and the version is immediately visible. Platform context comes from the directory structure (`templates/.github/agents/` vs `templates/.claude/agents/`).

---

### 4. Platform-Specific Versioning Config

**Decision:** Each platform's manifest.json defines its own versioning patterns.

**Behavior:** The `agentVersioning` section in each platform's manifest.json specifies:
- `path`: The versioned filename pattern with `{major}`, `{minor}`, `{patch}` placeholders
- `currentPath`: The original unversioned filename (for migration)
- `frontmatter`: Patterns for updating YAML frontmatter fields (`name`, `description`)

Example for VS Code:
```json
"agentVersioning": {
  "templates": [{
    "path": "templates/.github/agents/aps-v{major}.{minor}.{patch}.agent.md",
    "currentPath": "templates/.github/agents/aps-prompt-protocol.agent.md",
    "frontmatter": {
      "name": { "pattern": "APS v{major}.{minor}.{patch} Agent" },
      "description": { "pattern": "Generate APS v{major}.{minor}.{patch} .prompt.md files..." }
    }
  }]
}
```

**Rationale:** Platforms have different frontmatter conventions:
- VS Code uses human-readable names with spaces: `"APS v1.1.7 Agent"`
- Claude Code uses slug identifiers with hyphens: `aps-v1-1-7`

Hardcoding these patterns in bump_version.py would require script changes for each new platform. By moving configuration to manifests, platform maintainers can define their own conventions. This follows the same "data over code" principle used for detection markers (ADR-003).

---

### 5. Automatic Version Bump

**Decision:** bump_version.py updates agent templates alongside core files.

**Behavior:** Running `python tools/bump_version.py 1.1.7` performs these operations atomically:
1. Updates SKILL.md `framework_revision`
2. Updates package.json `version`
3. Updates pyproject.toml `version`
4. Updates __init__.py `__version__`
5. For each platform with `agentVersioning` config:
   - Updates frontmatter fields using regex substitution
   - Renames the agent file to include the version

The script finds existing agent files by checking both the `currentPath` (unversioned) and glob-matching the `path` pattern (previously versioned).

**Rationale:** Manual agent updates were rejected because:
- Humans forget steps, leading to version drift
- Multiple files across multiple platforms increase error probability
- CI/CD pipelines need deterministic, scriptable version bumps

Integrating agent updates into the existing bump_version.py maintains the "single command to bump everything" workflow that was already established for core version files.

---
