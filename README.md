# Agnostic Prompt Standard (APS)

A framework for describing systems in a way that both humans and AI agents can read, write, and reason about.

## What is APS?

APS is a general system description standard. The primary use case is agentic AI prompts, but the framework extends to any system that benefits from structured, machine-readable documentation.

**Core ideas:**
- AI systems can understand and reason about other systems—including themselves
- Modular, generalizable prompts that remain useful as capabilities advance
- Model-agnostic patterns that generalize across different AI implementations

The standard lives in [`./skill/agnostic-prompt-standard`](./skill/agnostic-prompt-standard) and is packaged as a "skill"—an emerging format for AI-consumable specifications.

## Quickstart

Install the APS skill into your repo:

```bash
npx @agnostic-prompt/aps init
# or
pipx run agnostic-prompt-aps init
```

For Claude Code platform path (`.claude/skills`):

```bash
npx @agnostic-prompt/aps init --platform claude-code
```

## Skill Structure

APS separates concerns into three layers:

| Layer | Path | Purpose |
|-------|------|---------|
| **Specification** | `references/` | Normative rules (structure, vocabulary, grammar, etc.) |
| **Assets** | `assets/` | Reusable templates and example components |
| **Platforms** | `platforms/` | Adapters for specific tools (VS Code, Claude, etc.) |

The core abstraction is a structured prompt envelope with seven ordered sections, from static instructions through executable processes to dynamic input.

<details>
<summary>Full directory tree</summary>

```
skill/agnostic-prompt-standard/
├── assets/
│   ├── constants/          # Constant syntax examples (JSON, TEXT blocks)
│   └── formats/            # Output format templates (tables, outlines, etc.)
├── platforms/
│   ├── vscode-copilot/     # VS Code / Copilot adapter
│   ├── claude-code/        # Claude Code adapter
│   ├── _schemas/           # JSON Schemas for validation
│   └── _template/          # Starter template for new adapters
├── references/
│   ├── 00-structure.md     # Prompt sections and envelope rules
│   ├── 01-vocabulary.md    # Normative language and authoring rules
│   ├── 02-linting-and-formatting.md
│   ├── 03-agentic-control.md
│   ├── 04-schemas-and-types.md
│   ├── 05-grammar.md       # EBNF grammar for DSL
│   ├── 06-logging-and-privacy.md
│   └── 07-error-taxonomy.md
└── SKILL.md                # Skill entrypoint and metadata
```

</details>

---

## CLI Tools

APS ships with CLI tools for both Node.js and Python.

| Package | Registry |
|---------|----------|
| `@agnostic-prompt/aps` | [npm](https://www.npmjs.com/package/@agnostic-prompt/aps) |
| `agnostic-prompt-aps` | [PyPI](https://pypi.org/project/agnostic-prompt-aps/) |

### Node

```bash
npx @agnostic-prompt/aps init        # Install skill
npx @agnostic-prompt/aps doctor      # Check installation
npx @agnostic-prompt/aps platforms   # List available adapters
```

### Python

```bash
pipx run agnostic-prompt-aps init
pipx run agnostic-prompt-aps doctor
```

> **Windows:** If `pipx run` fails with `FileNotFoundError`, use `pipx install agnostic-prompt-aps` or `python -m aps_cli` instead. See [`packages/aps-cli-py/README.md`](packages/aps-cli-py/README.md) for details.

---

## Development

### Build Tools

```bash
python tools/sync_payload.py       # Sync skill to CLI payloads
python tools/check_versions.py     # Verify version consistency
python tools/check_skill_links.py  # Check skill link integrity
python tools/bump_version.py X.Y.Z # Update version across all files
```

### Testing

```bash
# Node CLI
node --test packages/aps-cli-node/test/*.test.js

# Python CLI
cd packages/aps-cli-py && pytest -q tests
```

### Architecture

Both CLIs bundle the skill as a "payload" for distribution:
- **Node:** `packages/aps-cli-node/payload/`
- **Python:** `packages/aps-cli-py/src/aps_cli/payload/`

The `sync_payload.py` script copies from `skill/` to these locations before building.

### Version Management

The canonical version is `framework_revision` in `SKILL.md`. All of these must match:
- `skill/agnostic-prompt-standard/SKILL.md`
- `packages/aps-cli-node/package.json`
- `packages/aps-cli-py/pyproject.toml`
- `packages/aps-cli-py/src/aps_cli/__init__.py`

### Installation Paths

| Scope | Default Path | Claude Path |
|-------|--------------|-------------|
| Project | `.github/skills/agnostic-prompt-standard/` | `.claude/skills/agnostic-prompt-standard/` |
| Personal | `~/.copilot/skills/agnostic-prompt-standard/` | `~/.claude/skills/agnostic-prompt-standard/` |

### Key Files

**CLI behavior:**
- Node: `packages/aps-cli-node/src/core.js`, `src/cli.js`
- Python: `packages/aps-cli-py/src/aps_cli/core.py`, `cli.py`

**Specification:**
- `skill/agnostic-prompt-standard/references/*.md`
- `skill/agnostic-prompt-standard/SKILL.md`
