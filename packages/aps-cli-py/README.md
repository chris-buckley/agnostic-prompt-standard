# APS CLI (Python)

This package provides the `aps` CLI for installing the **Agnostic Prompt Standard (APS)** skill into:

- a repository workspace: `.github/skills/agnostic-prompt-standard/`
- or as a personal skill: `~/.copilot/skills/agnostic-prompt-standard/`

## Install / run

Global install (recommended):

```bash
pipx install agnostic-prompt-aps
aps init
aps update
```

One-off run:

```bash
pipx run agnostic-prompt-aps init
pipx run agnostic-prompt-aps update
```

## Commands

```bash
aps init [--repo|--personal] [--platform <id>] [--yes] [--force] [--dry-run]
aps doctor [--root <path>] [--json]
aps update [--root <path>] [--repo|--personal] [--check] [--dry-run] [--json] [--yes] [--force]
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

## Windows troubleshooting

On Windows, `pipx run agnostic-prompt-aps` may fail with `FileNotFoundError` due to a known pipx bug with `.exe` launcher paths.

**Workarounds:**

1. **Use `pipx install` instead** (recommended):
   ```bash
   pipx install agnostic-prompt-aps
   aps init
   ```

2. **Use Python module syntax**:
   ```bash
   python -m aps_cli init
   ```

3. **Try the full-name entry point**:
   ```bash
   pipx run agnostic-prompt-aps agnostic-prompt-aps init
   ```

4. **Upgrade pipx** to the latest version:
   ```bash
   python -m pip install --upgrade pipx
   ```


## Update behavior

`aps update` checks PyPI for the latest published APS CLI release and compares it with the running CLI version.

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
pipx run --no-cache agnostic-prompt-aps update --yes
```
