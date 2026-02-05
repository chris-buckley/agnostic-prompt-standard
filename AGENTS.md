<instructions>
You MUST dispatch 3-4 explore agents before making changes to understand codebase patterns.
You MUST verify assumptions about how things work before modifying code.
You MUST check package.json and package-lock.json for installed dependencies before adding new ones.
You MUST find and reuse existing utilities, types, and helpers.
You MUST NOT implement features until explicitly required (KISS/YAGNI).
You SHOULD prefer strategic extensibility (interfaces/plugin points) over speculative features.
You MUST NOT optimize code before measuring real performance bottlenecks.
You MUST leave the codebase cleaner than you found it (Boy Scout Rule).
You MUST optimize code for readability; write for humans, not machines.
You MUST separate concerns so distinct sections address distinct functionalities.
You MUST prefer composition over inheritance; assemble behavior from smaller components.
You MUST follow the Law of Demeter; objects should only talk to immediate collaborators.
You MUST ensure each module has only one reason to change (Single Responsibility).
You MUST design modules open for extension but closed for modification (Open-Closed).
You MUST prefer small, specific interfaces over monolithic ones (Interface Segregation).
You MUST depend on abstractions (interfaces), not concrete implementations (Dependency Inversion).
You SHOULD push state to the edges (databases, caches) by default.
You MUST prefer explicit, self-documenting code over clever tricks or magic.
You MUST use meaningful names that reveal intent for variables, functions, and classes.
You MUST write comments explaining why decisions were made, not restating what code does.
You SHOULD prefer immutable data structures; avoid changing state after creation.
You MUST validate inputs and assert invariants immediately (fail fast).
You SHOULD prefer returning errors explicitly rather than throwing exceptions where feasible.
Functions SHOULD either change state (Command) or return values (Query), rarely both (CQS).
You MUST check standard library and installed dependencies before creating new abstractions.
You MUST apply defense in depth with multiple layered security controls.
You MUST apply least privilege, sanitize all inputs/outputs, and use type-safe wrappers for secrets.
You SHOULD treat structured logging, metrics, and traces as first-class concerns where applicable.
You MUST design operations to handle retries safely without side effects (idempotency).
You MUST group imports: (1) standard library, (2) third-party packages, (3) local modules.
You MUST document all exported functions with JSDoc (TypeScript) or docstrings (Python).
</instructions>

<constants>
SKILL_PATH: "skill/agnostic-prompt-standard"
NODE_CLI_PATH: "packages/aps-cli-node/"
PYTHON_CLI_PATH: "packages/aps-cli-py/src/aps_cli/"
NODE_PAYLOAD_PATH: "packages/aps-cli-node/payload/"
PYTHON_PAYLOAD_PATH: "packages/aps-cli-py/src/aps_cli/payload/"
MIN_EXPLORE_AGENTS: 3

QUICKSTART: TEXT<<
Install the APS skill into your repo:

```bash
npx @agnostic-prompt/aps init
# or
pipx run agnostic-prompt-aps init
```

For Claude Code platform (installs to `.claude/skills/`), use the `--platform` flag:

```bash
npx @agnostic-prompt/aps init --platform claude-code
```

The `init` command supports interactive platform selection and can copy platform templates (agent files) into your workspace.
>>

ABOUT: TEXT<<
This repository contains the Agnostic Prompt Standard (APS), a framework for describing systems.
The primary use case is agentic AI prompts, but APS is designed as a general system description standard.
This enables AI systems to understand and reason about other systems—including themselves.
The result is modular, generalizable AI systems that remain useful as capabilities advance.
APS is designed for both humans and agents to read, write, and reason about systems.
The standard is intentionally model-agnostic. While no single prompt format works perfectly for every model, APS focuses on patterns that generalize as AI capabilities converge.
The standard lives here: `./skill/agnostic-prompt-standard`.
It is packaged as a "skill" an emerging format for AI-consumable specifications.
>>

SKILL_STRUCTURE_INTRO: TEXT<<
APS separates concerns into:
(1) the core specification (`references/`),
(2) reusable templates and examples (`assets/`), and
(3) platform-specific adapters (`platforms/`).
The core abstraction is a structured prompt envelope with seven ordered sections, from static instructions through executable processes to dynamic input.
>>

SKILL_TREE: TEXT<<
skill/
  agnostic-prompt-standard/
    assets/
      constants/
        constants-json-block-v1.0.0.example.md    JSON block constant syntax example
        constants-text-block-v1.0.0.example.md    TEXT block constant syntax example
      formats/
        format-code-changes-full-v1.0.0.example.md        Full file code changes template
        format-code-map-v1.0.0.example.md                 Code snippets with source links
        format-docs-index-v1.0.0.example.md               Documentation index format
        format-error-v1.0.0.example.md                    Single-line error output format
        format-hierarchical-outline-v1.0.0.example.md     Multilevel numbered outline template
        format-ideation-list-v1.0.0.example.md            Structured brainstorming ideas format
        format-link-manifest-v1.0.0.example.md            Link manifest format template
        format-markdown-table-v1.0.0.example.md           Process results table format
        format-table-api-coverage-v1.0.0.example.md       API coverage gap analysis table
    platforms/
      claude-code/
        frontmatter/
          agent-frontmatter.md                YAML template for agent files
          rules-frontmatter.md                YAML template for rules files
        templates/
          .claude/
            agents/
              aps-v{VERSION}.md               APS agent protocol template (versioned)
        manifest.json                         Claude Code file discovery rules
        README.md                             Adapter quickstart and usage guide
        tools-registry.json                   Tool names, sets, and mappings
      opencode/
        manifest.json                         OpenCode file discovery rules
        tools-registry.json                   Tool registry stub (placeholder)
      vscode-copilot/
        frontmatter/
          agent-frontmatter.md                YAML template for agent files
          instructions-frontmatter.md         YAML template for instructions files
          prompt-frontmatter.md               YAML template for prompt files
          skill-frontmatter.md                YAML template for skill files
        templates/
          .github/
            agents/
              aps-v{VERSION}.agent.md         APS prompt protocol agent template (versioned)
        manifest.json                         VS Code file discovery rules
        README.md                             Adapter quickstart and usage guide
        tools-registry.json                   Tool names, sets, and mappings
      _schemas/
        platform-manifest.schema.json         JSON Schema for manifest validation
        tools-registry.schema.json            JSON Schema for tools registry
      _template/
        templates/
          .github/
            agents/
              .gitkeep                        Placeholder for agent templates
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
>>

SKILL_FOLDERS_DESC: TEXT<<
The `references/` folder contains the normative APS v1.0 specification documents (00-07) that define the authoritative rules for prompt structure, vocabulary, linting, agentic control, schemas, grammar, logging/privacy, and error taxonomy.
The `assets/` folder contains reusable templates and example components organized into `constants/` and `formats/` subfolders that can be used when building APS-compliant prompts.
The `scripts/` folder is currently empty (reserved placeholder) for future automation scripts related to skill development.
The `platforms/` folder contains non-normative platform adapters that describe platform-specific differences (file discovery, frontmatter, tool availability) without changing the core APS spec. The `claude-code/` adapter (used with `--platform claude-code`) is particularly important for Claude Code CLI users, alongside `opencode/` and `vscode-copilot/` adapters plus templates for creating new adapters.
>>

NODE_CLI_USAGE: TEXT<<
Node CLI (packages/aps-cli-node/):
npx @agnostic-prompt/aps      # Run CLI
npm install                   # Install dependencies
npm test                      # Build and run tests
npm run lint                  # Run linter
npm pack                      # Build package (runs prepack)
Key dependencies: Commander.js (CLI framework), @inquirer/prompts (interactive prompts), Zod (validation schemas)
>>

PYTHON_CLI_USAGE: TEXT<<
Python CLI (packages/aps-cli-py/):
pipx run agnostic-prompt-aps   # Run CLI
pip install -e ".[dev]"        # Install with dev dependencies
pytest -q tests                # Run tests
python -m build                # Build wheel/sdist
Key dependencies: Typer (CLI framework), Rich (terminal formatting), Questionary (interactive prompts), Pydantic (validation schemas)
>>

CLI_COMMANDS_REF: TEXT<<
Both CLIs expose identical commands:

aps init [options]      Install APS skill into a project
aps doctor [options]    Diagnose skill installation and environment
aps platforms           List available platform adapters
aps version             Display CLI version

init command options:
- --platform <id...> — Platform adapter(s) to apply (e.g., `claude-code`, `vscode-copilot`). Use `none` to skip.
- --root <path> — Workspace root path (defaults to git repo root if found)
- --repo / --personal — Install scope: project skill vs user-level skill
- -f, --force — Overwrite existing files
- -y, --yes — Auto-confirm prompts (non-interactive mode)
- --dry-run — Preview actions without writing files

doctor command options:
- --root <path> — Workspace root path (defaults to git repo root if found)
- --json — Output in JSON format (useful for CI)
>>

BUILD_TOOLS: TEXT<<
python tools/sync_payload.py           # Sync skill to both CLI payloads
python tools/sync_payload.py --node    # Sync to Node payload only
python tools/sync_payload.py --python  # Sync to Python payload only
python tools/check_versions.py         # Verify version consistency
python tools/check_skill_links.py      # Check skill link integrity
python tools/bump_version.py           # Bump version across all sources
python tools/test_bump_version.py      # Run bump_version unit tests
python tools/generate-decision-index.py  # Generate ADR decision index
>>

NODE_BUILD_PROCESS: TEXT<<
The Node CLI is written in TypeScript and requires compilation:
npm run build           # Compile src/*.ts → dist/
npm run build:test      # Compile test/*.ts → dist-test/
npm run typecheck       # Type-check without emitting
npm run lint            # Run ESLint on src/ and test/
npm run format          # Format with Prettier
Tests run against compiled output: node --test ./dist-test/*.test.js ./dist-test/commands/*.test.js
>>

ARCHITECTURE_PAYLOAD: TEXT<<
CLI Payload Model:
Both CLIs bundle the skill directory as a "payload" for distribution:
- Node: packages/aps-cli-node/payload/
- Python: packages/aps-cli-py/src/aps_cli/payload/
The tools/sync_payload.py script copies skill/agnostic-prompt-standard/ to these locations before building.
In development, the CLIs fall back to reading directly from skill/ if no payload exists.
>>

VERSION_MANAGEMENT: TEXT<<
The canonical version is `framework_revision` in `skill/agnostic-prompt-standard/SKILL.md`.
These must all match:
- SKILL.md framework_revision
- packages/aps-cli-node/package.json version
- packages/aps-cli-py/pyproject.toml [project].version
- packages/aps-cli-py/src/aps_cli/__init__.py __version__
CI runs check_versions.py to enforce this.
>>

SKILL_INSTALL_PATHS: TEXT<<
Skill Installation Paths:
Default paths for installed skills:
- Project: .github/skills/agnostic-prompt-standard/
- Personal: ~/.copilot/skills/agnostic-prompt-standard/
- Claude Code (with --platform claude-code): .claude/skills/ instead
>>

TESTING_COMMANDS: TEXT<<
Run all tests:
# Node CLI (uses native node:test runner, requires build first)
npm test --prefix packages/aps-cli-node

# Python CLI (uses pytest)
cd packages/aps-cli-py && pytest -q tests

Manual CLI verification:
# Node CLI
node packages/aps-cli-node/bin/aps.js doctor
node packages/aps-cli-node/bin/aps.js init --platform claude-code --dry-run --yes

# Python CLI
python -m aps_cli doctor
python -m aps_cli init --platform claude-code --dry-run --yes
>>

KEY_FILES_NODE: JSON<<
{
  "cli_entry": "src/cli.ts",
  "core_logic": "src/core.ts",
  "commands": "src/commands/*.ts",
  "adapters": "src/detection/adapters.ts",
  "schemas": "src/schemas/*.ts",
  "result_type": "src/types/result.ts",
  "tests": "test/**/*.test.ts"
}
>>

KEY_FILES_PYTHON: JSON<<
{
  "cli_entry": "cli.py",
  "core_logic": "core.py",
  "schemas": "schemas.py",
  "version": "__init__.py",
  "module_entry": "__main__.py"
}
>>

KEY_FILES_SKILL: JSON<<
{
  "references": "skill/agnostic-prompt-standard/references/*.md",
  "skill_metadata": "skill/agnostic-prompt-standard/SKILL.md"
}
>>

DEPS_NODE: JSON<<
{
  "cli_framework": "Commander.js",
  "prompts": "@inquirer/prompts",
  "validation": "Zod"
}
>>

DEPS_PYTHON: JSON<<
{
  "cli_framework": "Typer",
  "terminal": "Rich",
  "prompts": "Questionary",
  "validation": "Pydantic"
}
>>

NAMING_CONVENTIONS: JSON<<
{
  "typescript": {
    "functions": "camelCase",
    "variables": "camelCase",
    "types": "PascalCase",
    "interfaces": "PascalCase",
    "constants": "SCREAMING_SNAKE_CASE"
  },
  "python": {
    "functions": "snake_case",
    "variables": "snake_case",
    "classes": "PascalCase",
    "constants": "SCREAMING_SNAKE_CASE"
  },
  "files": "kebab-case"
}
>>
</constants>

<formats>
<format id="EXPLORE_REPORT_V1" name="Exploration Report" purpose="Summarize findings from pre-change codebase exploration">
## Exploration Report
Agents Dispatched: <AGENT_COUNT>

### Patterns Found
<PATTERNS_LIST>

### Relevant Files
<FILES_LIST>

### Reusable Components
<COMPONENTS_LIST>

### Assumptions Verified
<ASSUMPTIONS_LIST>

WHERE:
- <AGENT_COUNT> is Integer; minimum value is 3.
- <PATTERNS_LIST> is Markdown bullet list of architectural patterns discovered.
- <FILES_LIST> is Markdown bullet list of file paths.
- <COMPONENTS_LIST> is Markdown bullet list of reusable utilities, types, or helpers.
- <ASSUMPTIONS_LIST> is Markdown bullet list of verified assumptions.
</format>

<format id="REUSE_CHECK_V1" name="Reuse Check Result" purpose="Document the reuse-before-create analysis">
## Reuse Check: <FUNCTIONALITY>
Status: <STATUS>

### Standard Library
<STDLIB_RESULT>

### Installed Dependencies
<DEPS_RESULT>

### Codebase Utilities
<CODEBASE_RESULT>

### Recommendation
<RECOMMENDATION>

WHERE:
- <FUNCTIONALITY> is String describing the needed functionality.
- <STATUS> is one of: FOUND_STDLIB, FOUND_DEPENDENCY, FOUND_CODEBASE, CREATE_NEW.
- <STDLIB_RESULT> is String describing stdlib search result.
- <DEPS_RESULT> is String describing dependency search result.
- <CODEBASE_RESULT> is String describing codebase search result.
- <RECOMMENDATION> is String with actionable recommendation.
</format>
</formats>

<runtime>
SESSION_INIT: false
EXPLORATION_COMPLETE: false
CURRENT_TASK: ""
</runtime>

<triggers>
<trigger event="code_change_request" target="pre_change_exploration" />
<trigger event="new_functionality_request" target="reuse_before_create" />
</triggers>

<processes>
<process id="pre_change_exploration" name="Pre-Change Exploration">
TELL "Dispatching exploration agents to understand codebase" level=brief
PAR:
  USE `Grep` where: path=".", pattern="class|function|interface"
  USE `Glob` where: pattern="**/*.ts,**/*.py"
  USE `Read` where: filePath="package.json"
  USE `Read` where: filePath="pyproject.toml"
JOIN:
  CAPTURE PATTERNS from `Grep`
  CAPTURE SOURCE_FILES from `Glob`
  CAPTURE NODE_DEPS from `Read`
  CAPTURE PYTHON_DEPS from `Read`
SET EXPLORATION_COMPLETE := true (from "Agent Inference")
RETURN: format="EXPLORE_REPORT_V1", patterns=PATTERNS, files=SOURCE_FILES
</process>

<process id="reuse_before_create" name="Reuse Before Create" args="functionality: String">
TELL "Checking for existing solutions before creating new" level=brief
SET STDLIB_CHECK := <STDLIB_RESULT> (from "Agent Inference")
IF STDLIB_CHECK contains solution:
  RETURN: format="REUSE_CHECK_V1", status="FOUND_STDLIB", recommendation=STDLIB_CHECK
USE `Grep` where: path="package.json", pattern=functionality
CAPTURE DEPS_CHECK from `Grep`
IF DEPS_CHECK contains solution:
  RETURN: format="REUSE_CHECK_V1", status="FOUND_DEPENDENCY", recommendation=DEPS_CHECK
USE `Grep` where: path="src/", pattern=functionality
CAPTURE CODEBASE_CHECK from `Grep`
IF CODEBASE_CHECK contains solution:
  RETURN: format="REUSE_CHECK_V1", status="FOUND_CODEBASE", recommendation=CODEBASE_CHECK
RETURN: format="REUSE_CHECK_V1", status="CREATE_NEW", recommendation="No existing solution found; create new abstraction"
</process>
</processes>

<input>
USER_INPUT is the user's latest message containing task description or code change request.
CURRENT_TASK is extracted from USER_INPUT representing the specific work item.
</input>
