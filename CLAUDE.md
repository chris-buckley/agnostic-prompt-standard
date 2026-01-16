# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agnostic Prompt Standard (APS) is a reference framework for generating, compiling, and linting prompts. The repository contains three main components:

- `skill/agnostic-prompt-standard/` — The APS skill (prompt protocol spec)
- `packages/aps-cli-node/` — Node.js CLI (`npx @agnostic-prompt/aps`)
- `packages/aps-cli-py/` — Python CLI (`pipx run agnostic-prompt-aps`)

## Commands

### Node CLI (packages/aps-cli-node/)
```bash
npm install          # Install dependencies
npm test             # Run tests (node --test)
npm run lint         # Run linter
npm pack             # Build package (runs prepack)
```

### Python CLI (packages/aps-cli-py/)
```bash
pip install -e ".[dev]"    # Install with dev dependencies
pytest -q tests            # Run tests
python -m build            # Build wheel/sdist
```

### Build Tools (from repo root)
```bash
python tools/sync_payload.py           # Sync skill to both CLI payloads
python tools/sync_payload.py --node    # Sync to Node payload only
python tools/sync_payload.py --python  # Sync to Python payload only
python tools/check_versions.py         # Verify version consistency
python tools/check_skill_links.py      # Check skill link integrity
```

## Architecture

### Skill Structure
The normative APS v1.0 spec lives in `skill/agnostic-prompt-standard/references/`:
- `00-structure.md` through `07-error-taxonomy.md` define the standard

Platform adapters in `skill/.../platforms/` provide non-normative file conventions, frontmatter templates, and tool registries. Currently only `vscode-copilot/` adapter exists.

### CLI Payload Model
Both CLIs bundle the skill directory as a "payload" for distribution:
- Node: `packages/aps-cli-node/payload/`
- Python: `packages/aps-cli-py/src/aps_cli/payload/`

The `tools/sync_payload.py` script copies `skill/agnostic-prompt-standard/` to these locations before building. In development, the CLIs fall back to reading directly from `skill/` if no payload exists.

### Version Management
The canonical version is `framework_revision` in `skill/agnostic-prompt-standard/SKILL.md`. These must all match:
- `SKILL.md` framework_revision
- `packages/aps-cli-node/package.json` version
- `packages/aps-cli-py/pyproject.toml` [project].version
- `packages/aps-cli-py/src/aps_cli/__init__.py` __version__

CI runs `check_versions.py` to enforce this.

### Skill Installation Paths
Default paths for installed skills:
- Project: `.github/skills/agnostic-prompt-standard/`
- Personal: `~/.copilot/skills/agnostic-prompt-standard/`
- Claude (with `--claude`): `.claude/skills/` instead
