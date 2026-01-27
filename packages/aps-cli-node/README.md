# APS CLI (Node)

Installs the Agnostic Prompt Standard skill into a repository or into your personal skill directory, and can apply platform adapter templates.

## Install

```bash
npm install -g @agnostic-prompt/aps-cli
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

Install APS skill + templates.

* Project skill:

  * Copilot: `<repo>/.github/skills/agnostic-prompt-standard`
  * Claude: `<repo>/.claude/skills/agnostic-prompt-standard`
* Personal skill:

  * Copilot: `~/.copilot/skills/agnostic-prompt-standard`
  * Claude: `~/.claude/skills/agnostic-prompt-standard`

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

aps init --yes --platform none
aps init --yes --platform claude-code --personal
```

### doctor

Show installation status and detection results.

```bash
aps doctor
aps doctor --json
aps doctor --root /path/to/workspace
```

### platforms

List available platform adapters.

```bash
aps platforms
```

### version

Print CLI version.

```bash
aps version
aps --version
```