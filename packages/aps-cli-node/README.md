# APS CLI (Node)

This package provides the `aps` CLI for installing the **Agnostic Prompt Standard (APS)** skill into:

- a repository workspace: `.github/skills/agnostic-prompt-standard/` (and/or `.claude/skills/agnostic-prompt-standard/`)
- or as a personal skill: `~/.copilot/skills/agnostic-prompt-standard/` (and/or `~/.claude/skills/agnostic-prompt-standard/`)

## Install / run

One-off (no global install):

```bash
npx @agnostic-prompt/aps init
npx @agnostic-prompt/aps update
```

Global install:

```bash
npm install -g @agnostic-prompt/aps
aps init
aps update
```

## Commands

```bash
aps init [--repo|--personal] [--platform <id...>] [--yes] [--force] [--dry-run]
aps doctor [--root <path>] [--json]
aps update [--root <path>] [--repo|--personal] [--check] [--dry-run] [--json] [--yes] [--force]
aps platforms
aps version
```

## Platform adapters

In interactive mode, `aps init` will:

- auto-detect existing adapter markers in the repo
- show a checkbox list (multi-select)
- show a confirmation summary before writing

You can also pass adapters explicitly:

```bash
aps init --platform vscode-copilot claude-code
# or
aps init --platform vscode-copilot --platform claude-code
```

## Platform-specific paths

Use `--platform <id>` to specify one or more platform adapters.

```bash
# VS Code / Copilot (default paths: .github/skills, ~/.copilot/skills)
aps init --platform vscode-copilot

# Claude Code (paths: .claude/skills, ~/.claude/skills)
aps init --platform claude-code
```


## Update behavior

`aps update` checks npm for the latest published APS CLI release and compares it with the running CLI version.

- If a newer CLI release exists, the command can refresh the CLI package first and then re-run the update with the newer bundled APS payload.
- Installed APS skill directories are then refreshed from that payload.
- Use `--check` to report only, `--dry-run` to preview file updates, and `--force` to refresh installed skills even when versions already match.

Examples:

```bash
# Refresh installed APS skills
aps update

# Check for updates without writing
aps update --check

# Run from the newest published package immediately
npx @agnostic-prompt/aps@latest update --yes
```
