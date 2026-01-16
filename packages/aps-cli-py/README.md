# APS CLI (Python)

This package provides the `aps` CLI for installing the **Agnostic Prompt Standard (APS)** skill into:

- a repository workspace: `.github/skills/agnostic-prompt-standard/`
- or as a personal skill: `~/.copilot/skills/agnostic-prompt-standard/`

## Install / run

Global install (recommended):

```bash
pipx install agnostic-prompt-aps
aps init
```

One-off run:

```bash
pipx run agnostic-prompt-aps init
```

## Commands

```bash
aps init [--repo|--personal] [--platform <id>] [--templates] [--yes] [--force]
aps doctor [--json]
aps platforms
aps version
```

## Claude platform path

If you need the Claude platform `.claude/skills` location, pass `--claude`:

```bash
aps init --claude
```
