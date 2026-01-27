# APS CLI (Python)

A small CLI to install + manage the Agnostic Prompt Standard (APS) skill.

- Installs APS into:
  - a repository workspace:
    - Copilot: `.github/skills/agnostic-prompt-standard`
    - Claude: `.claude/skills/agnostic-prompt-standard`
  - a personal skill dir:
    - Copilot: `~/.copilot/skills/agnostic-prompt-standard`
    - Claude: `~/.claude/skills/agnostic-prompt-standard`
- Applies platform adapter templates (e.g. Copilot Agents, Claude Code, etc.)

## Install

```bash
pipx install aps-cli
```

## Usage

```bash
aps <command> [options]
```

Commands:

* `init` — install APS skill + optional platform templates
* `doctor` — verify installs and show basic platform detection
* `platforms` — list bundled platform adapters
* `version` — print CLI version

### init

Install APS skill + apply adapter templates.

Examples:

```bash
aps init
aps init --repo
aps init --personal
aps init --platform vscode-copilot

# Multiple adapters: use comma-separated values or repeat the flag (both work cross-CLI)
aps init --platform vscode-copilot,claude-code
# or
aps init --platform vscode-copilot --platform claude-code

aps init --platform none
aps init --platform claude-code --personal
```

### doctor

```bash
aps doctor
aps doctor --json
aps doctor --root /path/to/workspace
```

### platforms

```bash
aps platforms
```

### version

```bash
aps version
aps --version
```