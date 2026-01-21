# VS Code + GitHub Copilot adapter

This adapter documents **how APS fits into VS Code Copilot's file conventions**.

## What this adapter provides

- `manifest.json` — where VS Code discovers skills, agents, prompts, and instructions
- `tools-registry.json` — a curated registry of tools/tool-sets and their **canonical frontmatter names**
- `frontmatter/` — copy/paste YAML frontmatter templates for VS Code files

## Quickstart

Install this APS skill into your repo at:
- `.github/skills/agnostic-prompt-standard/`

## VS Code file locations (summary)

VS Code Copilot discovers these files:

- **Agent Skills**: `.github/skills/<skill-id>/SKILL.md`
- **Custom agents**: `.github/agents/*.agent.md`
- **Prompt files**: `.github/prompts/*.prompt.md`
- **Custom instructions**:
  - `.github/copilot-instructions.md`
  - `.github/instructions/*.instructions.md`

See `manifest.json` for the full matrix (including personal and Claude locations).

## Frontmatter nuances (important)

VS Code uses **YAML frontmatter** in several file types.

### `*.agent.md` (custom agents)

Supported frontmatter keys include:

- `name`
- `description`
- `argument-hint`
- `tools`
- `model`
- `infer`
- `target`
- `handoffs`
- `mcp-servers`

**Lint note:** if you see diagnostics like "Unexpected indentation" on `description: >` blocks, keep `description` as a **single-line string** (quoted is safest).

### `*.prompt.md` (prompt files)

Common keys:

- `name`
- `description`
- `argument-hint`
- `agent` (ask|edit|agent|<custom-agent-id>)
- `tools`
- `model`

See `frontmatter/` for templates.

## Tools: names, tool-sets, and renames

### Tool mentions vs `tools:`

- In chat, tools appear as `#` mentions (ex: `#codebase`, `#problems`).
- In frontmatter `tools: [...]`, list tool names **without** `#`.
- Depending on VS Code version, some names are **qualified** (ex: `search/codebase`, `read/problems`, `web/fetch`).

**Rule:** always prefer the exact tool name shown by VS Code's tools picker.

### Common rename fixes (VS Code diagnostics)

If you get diagnostics like "Tool or toolset X has been renamed", update frontmatter.
Common mappings:

- `problems` → `read/problems`
- `changes` → `search/changes`
- `usages` → `search/usages`
- `fetch` → `web/fetch`
- `todos` → `todo`

This repository encodes the canonical names in `tools-registry.json`.

### APS tool bundles

For APS, we recommend starting with:

- **Planner** (read-only-ish): `recommended.aps.planner`
- **Implementer**: `recommended.aps.implementer`

Both are defined in `tools-registry.json` so you can keep frontmatter small and consistent.
