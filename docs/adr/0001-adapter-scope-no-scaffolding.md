# ADR-001: Scope of Platform Adapters: No Generic Scaffolding

**Date:** 2026-01-22
**Status:** Accepted
**Deciders:** APS maintainers
**PR/Issue:** N/A

## Context

Early versions of APS platform adapters (specifically `claude-code`) included generic project templates like `CLAUDE.md` and settings files to help users bootstrap projects. However, APS is a Standard and a Skill, not a project generator. Including generic templates bloats the payload, creates maintenance burden, and confuses the boundary between "What is APS?" and "What is the Platform?".

## Quick Reference

1. [Remove Generic Scaffolding](#1-remove-generic-scaffolding) — Platform adapters contain only manifests, registries, and APS-specific snippets.

## Consequences

### Positive
- Clean separation of concerns; APS focuses on the prompt standard
- Reduced maintenance burden for keeping templates aligned with upstream platforms

### Negative
- Users need to consult platform documentation (e.g., Anthropic or VS Code docs) to set up their base project structure before adding APS

### Neutral
- Existing users with generic templates may need to manually remove them

## Decisions

### 1. Remove Generic Scaffolding

**Decision:** Platform adapters do not include generic project scaffolding templates.

**Behavior:** Platform adapters (`skill/agnostic-prompt-standard/platforms/*`) contain only:
1. **Manifests:** To map platform concepts (files, tools) to APS concepts
2. **Registries:** To define tool availability and naming
3. **Frontmatter/Snippets:** To help users configure APS-specific files (like Agents or Rules) within that platform

Generic "Hello World" project files (e.g., `CLAUDE.md`, `.vscode/settings.json`) are not provided unless strictly required to make the APS Skill executable.

**Rationale:** Including generic templates bloats the distributed payload, creates ongoing maintenance to track upstream platform changes, and blurs the line between what APS provides versus what the platform provides. Users benefit from a focused skill that does one thing well.
