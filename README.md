# Agnostic Prompt Standard (APS) v1.0

APS is a reference framework for generating, compiling, and linting prompts.

This repository contains:

- `skill/agnostic-prompt-standard/` — the APS skill (drop-in for Agent Skills)
- `packages/aps-cli-node/` — Node CLI (`npx @agnostic-prompt/aps ...`)
- `packages/aps-cli-py/` — Python CLI (`pipx install agnostic-prompt-aps`)

## Quickstart (VS Code + GitHub Copilot)

### 1) Install the APS skill into your repo

One-off (no global install):

```bash
npx @agnostic-prompt/aps init
```

Or, with pipx:

```bash
pipx run agnostic-prompt-aps init
```

If you need the **Claude platform** path (`.claude/skills`), add `--claude`.

### 2) (Optional) Install the VS Code platform templates

The `init` command can also copy the VS Code templates (agents / AGENTS.md) into your workspace.

## Development

- Sync payloads before building (used by CI):

```bash
python tools/sync_payload.py
```

- Version consistency:

```bash
python tools/check_versions.py
```
