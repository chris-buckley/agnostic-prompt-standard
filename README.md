# Agnostic Prompt Standard (APS)

APS is a system description standard. It gives you explicit structure, output contracts, and validation rules for the instructions that govern AI agents, and it works across platforms.

APS makes more sense when you see it, so here's the smallest useful prompt:

```text
<instructions>
You MUST output exactly one fenced block whose info string is `format:HELLO_V1`.
You MUST NOT output any text outside that fenced block.
</instructions>
<constants>
NAME: "world"
</constants>
<formats>
<format id="HELLO_V1" name="Hello" purpose="Minimal greeting output.">
Hello, <NAME>!

WHERE:
- <NAME> is String.
</format>
</formats>
<runtime>
</runtime>
<triggers>
<trigger event="manual" target="hello" />
</triggers>
<processes>
<process id="hello">
TELL "Render the HELLO_V1 greeting."
RETURN: name=NAME
</process>
</processes>
<input>
</input>
```

Output (what downstream automation can rely on):

```format:HELLO_V1
Hello, world!
```

Seven ordered sections. Typed output contracts. Lintable structure. If the model drifts from the declared format, a validator catches it with a specific error code instead of letting bad data through.

For the full motivation, use cases, concrete examples, and design rationale, read [Why APS Exists](docs/why-aps-exists.md).

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

Validate your installation:

```bash
npx @agnostic-prompt/aps doctor
```

Update an existing APS installation:

```bash
npx @agnostic-prompt/aps update
# or
pipx run agnostic-prompt-aps update
```

Check only, without writing:

```bash
aps update --check
```

To force the newest published CLI before the refresh, run the latest package explicitly:

```bash
npx @agnostic-prompt/aps@latest update --yes
pipx run --no-cache agnostic-prompt-aps update --yes
```

## Skill Structure

APS separates concerns into three layers:

| Layer | Path | Purpose |
|-------|------|---------|
| Specification | `references/` | Normative rules (structure, vocabulary, grammar, error taxonomy) |
| Assets | `assets/` | Reusable templates and example components |
| Platforms | `platforms/` | Adapters for specific hosts (VS Code Copilot, Claude Code, OpenCode) |

The core abstraction is a structured envelope with seven ordered sections, from static instructions through executable processes to dynamic input.

<details>
<summary>Full directory tree</summary>

```
skill/agnostic-prompt-standard/
├── assets/
│   ├── constants/          # Constant syntax examples (JSON, TEXT, CSV blocks)
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

## CLI Tools

Available on both npm and PyPI.

| Package | Registry |
|---------|----------|
| `@agnostic-prompt/aps` | [npm](https://www.npmjs.com/package/@agnostic-prompt/aps) |
| `agnostic-prompt-aps` | [PyPI](https://pypi.org/project/agnostic-prompt-aps/) |

### Node

```bash
npx @agnostic-prompt/aps init        # Install skill
npx @agnostic-prompt/aps doctor      # Check installation
npx @agnostic-prompt/aps update      # Refresh installed APS skills
npx @agnostic-prompt/aps platforms   # List available adapters
```

### Python

```bash
pipx run agnostic-prompt-aps init
pipx run agnostic-prompt-aps doctor
pipx run agnostic-prompt-aps update
```

> **Windows:** If `pipx run` fails with `FileNotFoundError`, use `pipx install agnostic-prompt-aps` or `python -m aps_cli` instead. See [`packages/aps-cli-py/README.md`](packages/aps-cli-py/README.md) for details.

## Development

### Build Tools

```bash
python tools/sync_payload.py             # Sync skill to CLI payloads
python tools/check_versions.py           # Verify version consistency
python tools/check_skill_links.py        # Check skill link integrity
python tools/bump_version.py X.Y.Z       # Update version across all files
python tools/auto_bump_version.py        # Auto-bump when releasable changes exist
python tools/test_bump_version.py        # Run bump_version unit tests
python tools/test_auto_bump_version.py   # Run auto_bump_version unit tests
python tools/generate-decision-index.py  # Generate ADR decision index
```

### Testing

```bash
# Node CLI
npm test --prefix packages/aps-cli-node

# Python CLI
cd packages/aps-cli-py && pytest -q tests
```

### Architecture

Both CLIs bundle the skill as a payload for distribution:

- Node: `packages/aps-cli-node/payload/`
- Python: `packages/aps-cli-py/src/aps_cli/payload/`

The `sync_payload.py` script copies from `skill/` to these locations before building.

### Version Management

The canonical version is `framework_revision` in `SKILL.md`. All of these must match:

- `skill/agnostic-prompt-standard/SKILL.md`
- `packages/aps-cli-node/package.json`
- `packages/aps-cli-node/package-lock.json`
- `packages/aps-cli-py/pyproject.toml`
- `packages/aps-cli-py/src/aps_cli/__init__.py`

Release automation now has three layers:

- `.github/workflows/ci.yml` validates versions and runs Node + Python tests
- `.github/workflows/auto-bump-version.yml` creates a follow-up version bump commit on `main` when releasable files changed but the version did not
- `.github/workflows/publish-packages.yml` publishes npm and PyPI packages from `vX.Y.Z` tags after re-validating the tagged version

The publish workflow is designed for trusted publishing / OIDC on npm and PyPI. Configure those repository-side credentials before you use the workflow.

### Installation Paths

| Scope | Default Path | Claude Path |
|-------|--------------|-------------|
| Project | `.github/skills/agnostic-prompt-standard/` | `.claude/skills/agnostic-prompt-standard/` |
| Personal | `~/.copilot/skills/agnostic-prompt-standard/` | `~/.claude/skills/agnostic-prompt-standard/` |

### Key Files

CLI behavior:

- Node: `packages/aps-cli-node/src/core.js`, `src/cli.js`
- Python: `packages/aps-cli-py/src/aps_cli/core.py`, `cli.py`

Specification:

- `skill/agnostic-prompt-standard/references/*.md`
- `skill/agnostic-prompt-standard/SKILL.md`

## License

MIT
