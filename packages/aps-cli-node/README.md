# APS CLI (Node)

This package provides the `aps` CLI for installing the **Agnostic Prompt Standard (APS)** skill into:

- a repository workspace: `.github/skills/agnostic-prompt-standard/`
- or as a personal skill: `~/.copilot/skills/agnostic-prompt-standard/`

## Install / run

One-off (no global install):

```bash
npx @agnostic-prompt/aps init
```

Global install:

```bash
npm install -g @agnostic-prompt/aps
aps init
```

## Commands

```bash
aps init [--repo|--personal] [--platform <id>] [--yes] [--force]
aps doctor [--json]
aps platforms
aps version
```

## Platform-specific paths

Use `--platform <id>` to specify a platform adapter:

```bash
# VS Code / Copilot (default paths: .github/skills, ~/.copilot/skills)
aps init --platform vscode-copilot

# Claude Code (paths: .claude/skills, ~/.claude/skills)
aps init --platform claude-code
```
