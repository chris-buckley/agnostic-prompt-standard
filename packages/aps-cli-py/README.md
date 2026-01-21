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
