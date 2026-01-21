# 1. Scope of Platform Adapters: No Generic Scaffolding

Date: 2026-01-22

## Status
Accepted

## Context
Early versions of APS platform adapters (specifically `claude-code`) included generic project templates like `CLAUDE.md` and settings files to help users bootstrap projects.

However, APS is a **Standard** and a **Skill**, not a project generator. Including generic templates:
1.  Bloats the payload distributed to user machines.
2.  Creates a maintenance burden to keep templates aligned with upstream platform best practices.
3.  Confuses the boundary between "What is APS?" and "What is the Platform?".

## Decision
We will **remove generic project scaffolding templates** from all platform adapters.

Platform adapters (`skill/agnostic-prompt-standard/platforms/*`) must only contain:
1.  **Manifests:** To map platform concepts (files, tools) to APS concepts.
2.  **Registries:** To define tool availability and naming.
3.  **Frontmatter/Snippets:** To help users configure *APS-specific* files (like Agents or Rules) within that platform.

We will NOT provide generic "Hello World" project files (e.g., `CLAUDE.md`, `.vscode/settings.json`) unless they are strictly required to make the APS Skill executable.

## Consequences
*   **Positive:** Clean separation of concerns. APS focuses on the prompt standard.
*   **Positive:** Reduced maintenance.
*   **Negative:** Users need to consult platform documentation (e.g., Anthropic or VS Code docs) to set up their base project structure before adding APS.