## Quickstart

Install the APS skill into your repo:

```bash
npx @agnostic-prompt/aps init
# or
pipx run agnostic-prompt-aps init
```

For Claude platform path (`.claude/skills`), add `--claude`:

```bash
npx @agnostic-prompt/aps init --claude
```

The `init` command can also copy VS Code templates (agents / AGENTS.md) into your workspace.

## About this codebase

This repository contains the Agnostic Prompt Standard (APS), a framework for describing systems.
The primary use case is agentic AI prompts, but APS is designed as a general system description standard.
This enables AI systems to understand and reason about other systems—including themselves.
The result is modular, generalizable AI systems that remain useful as capabilities advance.
APS is designed for both humans and agents to read, write, and reason about systems.
The standard is intentionally model-agnostic. While no single prompt format works perfectly for every model, APS focuses on patterns that generalize as AI capabilities converge.

The standard lives here: `./skill/agnostic-prompt-standard`.
It is packaged as a "skill" an emerging format for AI-consumable specifications.

## Skill Structure

APS separates concerns into:
(1) the core specification (`references/`),
(2) reusable templates and examples (`assets/`), and
(3) platform-specific adapters (`platforms/`).

The core abstraction is a structured prompt envelope with seven ordered sections, from static instructions through executable processes to dynamic input.

```
skill/
  agnostic-prompt-standard/
    assets/
      agents/
        vscode-agent-v1.0.0.agent.md          APS prompt generator for VS Code
      constants/
        constants-json-block-v1.0.0.example.md    JSON block constant syntax example
        constants-text-block-v1.0.0.example.md    TEXT block constant syntax example
      formats/
        format-code-changes-full-v1.0.0.example.md        Full file code changes template
        format-code-map-v1.0.0.example.md                 Code snippets with source links
        format-error-v1.0.0.example.md                    Single-line error output format
        format-hierarchical-outline-v1.0.0.example.md     Multilevel numbered outline template
        format-ideation-list-v1.0.0.example.md            Structured brainstorming ideas format
        format-markdown-table-v1.0.0.example.md           Process results table format
        format-table-api-coverage-v1.0.0.example.md       API coverage gap analysis table
    platforms/
      vscode-copilot/
        frontmatter/
          agent-frontmatter.md                YAML template for agent files
          instructions-frontmatter.md         YAML template for instructions files
          prompt-frontmatter.md               YAML template for prompt files
          skill-frontmatter.md                YAML template for skill files
        templates/
          .github/
            agents/
          AGENTS.md                           Workspace instructions for AI agents
        manifest.json                         VS Code file discovery rules
        README.md                             Adapter quickstart and usage guide
        tools-registry.json                   Tool names, sets, and mappings
      _schemas/
        platform-manifest.schema.json         JSON Schema for manifest validation
        tools-registry.schema.json            JSON Schema for tools registry
      _template/
        manifest.json                         Starter manifest for new adapters
        README.md                             Instructions to create new adapters
        tools-registry.json                   Empty tools registry template
      README.md                               Platforms overview and adapter contract
    references/
      00-structure.md                         Prompt sections and envelope rules
      01-vocabulary.md                        Normative language and authoring rules
      02-linting-and-formatting.md            Compile-time formatting rules
      03-agentic-control.md                   DSL keywords and control flow
      04-schemas-and-types.md                 Schemas and format contracts
      05-grammar.md                           EBNF grammar for DSL
      06-logging-and-privacy.md               Logging and redaction requirements
      07-error-taxonomy.md                    Error and warning codes
    scripts/
      .gitkeep                                Placeholder for future scripts
    SKILL.md                                  Skill entrypoint and layout overview
```

The `references/` folder contains the normative APS v1.0 specification documents (00-07) that define the authoritative rules for prompt structure, vocabulary, linting, agentic control, schemas, grammar, logging/privacy, and error taxonomy.

The `assets/` folder contains reusable templates and example components organized into `constants/`, `formats/`, and `agents/` subfolders that can be used when building APS-compliant prompts.

The `scripts/` folder is currently empty (reserved placeholder) for future automation scripts related to skill development.

The `platforms/` folder contains non-normative platform adapters that describe platform-specific differences (file discovery, frontmatter, tool availability) without changing the core APS spec, including the `vscode-copilot/` adapter and templates for creating new adapters.

## CLI Tools

To lower the barrier to adoption, APS ships with CLI tools that let agents install the skill directly into any project.

| Package | Registry |
|---------|----------|
| `@agnostic-prompt/aps` | [npm](https://www.npmjs.com/package/@agnostic-prompt/aps) |
| `agnostic-prompt-aps` | [PyPI](https://pypi.org/project/agnostic-prompt-aps/) |

### Node CLI (packages/aps-cli-node/)
```bash
npx @agnostic-prompt/aps      # Run CLI
npm install                   # Install dependencies
npm test                      # Run tests (node --test)
npm run lint                  # Run linter
npm pack                      # Build package (runs prepack)
```

### Python CLI (packages/aps-cli-py/)
```bash
pipx run agnostic-prompt-aps   # Run CLI
pip install -e ".[dev]"        # Install with dev dependencies
pytest -q tests                # Run tests
python -m build                # Build wheel/sdist
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

## Testing

### Run all tests
```bash
# Node CLI
node --test packages/aps-cli-node/test/*.test.js

# Python CLI
cd packages/aps-cli-py && pytest -q tests
```

### Manual CLI verification
```bash
# Node CLI
node packages/aps-cli-node/bin/aps.js doctor
node packages/aps-cli-node/bin/aps.js init --claude --dry-run --yes

# Python CLI (from packages/aps-cli-py/)
python -c "import sys; sys.argv = ['aps', 'doctor']; from aps_cli.cli import app; app()"
```

### Linting
```bash
node packages/aps-cli-node/scripts/lint.js
```

## Key Files

When modifying CLI behavior:
- **Node**: `packages/aps-cli-node/src/core.js` (path logic), `src/cli.js` (commands)
- **Python**: `packages/aps-cli-py/src/aps_cli/core.py` (path logic), `cli.py` (commands)

When modifying the skill/spec:
- `skill/agnostic-prompt-standard/references/*.md` — normative spec documents
- `skill/agnostic-prompt-standard/SKILL.md` — skill metadata and version