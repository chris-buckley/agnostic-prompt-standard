# ROADMAP

This document captures high‑leverage, public-facing implementation milestones for the Agnostic Prompt Standard (APS) codebase. The intent is to make APS v1.0 more *executable* (lint/format/compile), *testable* (conformance), and *integrated* (editor tooling), while preserving the model‑agnostic, adapter-driven design.

---

## Goals

- **Executable APS:** Provide a reference parser + linter + formatter that enforces APS v1.0 rules and emits stable `AG-*` diagnostics.
- **Conformance-first:** Make APS evolvable via a canonical conformance suite (golden prompts + expected diagnostics).
- **Typed tool usage:** Enable optional type-aware checks for `USE ... where:` and `CAPTURE map:` paths via external tool signatures.
- **Editor-grade ergonomics:** Provide primitives needed for an APS LSP and syntax tooling (Tree‑sitter grammar, diagnostics, navigation).
- **Platform-agnostic:** Keep normative behavior in `skill/agnostic-prompt-standard/references/`; keep platform differences in adapters.

---

## Non-goals

- **No runtime executor mandate:** APS tooling should validate and compile; host runtimes still own tool execution.
- **No host lock-in:** Do not encode host-only behaviors into the normative spec (beyond adapters).

---

## Current baseline

- Normative spec: `skill/agnostic-prompt-standard/references/00-07.md`
- Skill assets/examples: `skill/agnostic-prompt-standard/assets/`
- Platform adapters: `skill/agnostic-prompt-standard/platforms/` (with adapter JSON Schemas under `platforms/_schemas/`)
- CLIs primarily support *installation + status*:
  - Node: `packages/aps-cli-node/`
  - Python: `packages/aps-cli-py/`
- Repo tooling: `tools/sync_payload.py`, `tools/check_versions.py`, `tools/check_skill_links.py`

---

## Roadmap overview (prioritized)

### P0 — Conformance suite (golden tests as the contract)

**Outcome:** APS behavior becomes testable and stable across implementations.

**Deliverables**
- A `conformance/` test corpus:
  - Valid prompts (should pass).
  - Invalid prompts per error code (must fail with exact `AG-*` codes).
- A deterministic expected-output format for diagnostics (JSON).
- A harness to run conformance checks in CI and locally.

**Proposed repo changes**
```text
conformance/
  README.md
  cases/
    valid/
      minimal.prompt.md
      envelope-order.prompt.md
    invalid/
      AG-010-comment-in-process.prompt.md
      AG-011-tab-detected.prompt.md
      AG-039-format-undefined.prompt.md
      ...
  expected/
    AG-010.json
    AG-011.json
    AG-039.json
    ...
tools/
  run_conformance.py
````

**Reasoning**

* This unblocks future work (linter, formatter, LSP) while preventing spec drift.
* Error taxonomy becomes actionable only when it is enforced and regression-tested.

---

### P0 — Machine-readable spec atoms (make the standard lintable by design)

**Outcome:** The spec becomes a single source of truth for implementations without scraping Markdown.

**Deliverables**

* Extract key “spec atoms” into machine-readable files:

  * Ordered section model (envelope ordering, tag rules).
  * Token/keyword catalogs (reserved words, identifier regexes).
  * Error catalog (`AG-*` codes, severity, messages).
  * Grammar artifact (EBNF or a stable equivalent).

**Proposed repo changes**

```text
skill/agnostic-prompt-standard/
  spec/
    aps-v1.0.sections.json
    aps-v1.0.tokens.json
    aps-v1.0.errors.json
    aps-v1.0.grammar.ebnf
tools/
  extract_spec_atoms.py
```

**Reasoning**

* Keeps tooling aligned with the normative spec.
* Reduces “update docs vs update code” mismatches.

---

### P0 — Reference parser + linter + formatter core, then expose via both CLIs

**Outcome:** APS becomes executable via `aps lint`, `aps fmt`, and `aps compile`.

**Deliverables**

* A reference APS core library implementing:

  * Envelope parsing (sections, tag/newline rules).
  * DSL parsing (process bodies) into an AST.
  * Lint rules mapping to `AG-*` / `AG-W*`.
  * Formatter for canonical spacing / normalization where the spec mandates it.
* CLI integration in Node + Python (even if one CLI shells out initially, this should converge over time).

**Proposed repo changes (one recommended layout)**

```text
packages/
  aps-core/
    src/
      parse/
      lint/
      format/
      diagnostics/
    tests/
packages/aps-cli-node/
  src/
    commands/
      lint.js
      fmt.js
      compile.js
packages/aps-cli-py/
  src/aps_cli/
    commands/
      lint.py
      fmt.py
      compile.py
```

**Implementation notes**

* **Diagnostics contract:** adopt a stable JSON diagnostic model (code, severity, message, file, range). This will later feed the LSP.
* **Compile vs lint:** “compile” should produce a canonicalized prompt output (where the spec defines normalization); “lint” should validate without rewriting unless explicitly requested.

**Reasoning**

* CLI commands make APS usable in real projects and pipelines.
* A shared core prevents duplicate logic and divergent behaviors.

---

### P0 — Resolve spec-level inconsistencies that block strict parsing

**Outcome:** The normative spec and grammar can be implemented without ad-hoc exceptions.

**Known mismatches to address**

* Keyword set mismatch: `05-grammar.md` includes constructs (e.g., `FOREACH`, `TRY`, `RECOVER`) that are not listed in the keyword/reserved catalogs in `03-agentic-control.md`.
* Statement terminators mismatch: `03-agentic-control.md` examples show trailing `.` on statements, while the grammar does not define `.` as a terminator (and the linting rules emphasize newline termination).
* `<expr>` and `<path>` are intentionally unspecified in v1.0; this prevents strong validation for `ASSERT` and `CAPTURE map:` paths.

**Deliverables**

* Align `03-agentic-control.md` keyword/reserved lists with `05-grammar.md` (or explicitly mark the extra constructs as extensions).
* Remove or formalize statement terminators so that examples match the grammar.
* Make an explicit decision for v1.0 tooling:

  * Either treat `<expr>` and `<path>` as engine-defined (and only do shallow validation), **or**
  * Standardize a baseline subset for portable linting.

**Proposed repo changes**

```text
skill/agnostic-prompt-standard/references/
  03-agentic-control.md    # align keywords/reserved + examples
  05-grammar.md            # clarify extension points and/or baseline constraints
  07-error-taxonomy.md     # add any new codes if needed for clarified behavior
```

**Reasoning**

* A reference implementation should not need “special casing” to reconcile the spec.

---

### P1 — Standardize `CAPTURE map:` paths using an existing standard (portable capture semantics)

**Outcome:** `CAPTURE map:` becomes deterministic and interoperable across engines.

**Deliverables**

* Define `<path>` as one of:

  * JSON Pointer, or
  * JSONPath,
  * (or support both with explicit tagging rules).
* Add lint rules for invalid paths and missing/optional paths (align with `AG-028`).

**Proposed repo changes**

```text
skill/agnostic-prompt-standard/references/
  05-grammar.md            # define <path> syntax choice(s)
  04-schemas-and-types.md  # document and exemplify CAPTURE mapping rules
packages/aps-core/src/
  capture_path/
    json_pointer.*
    jsonpath.*             # optional if supporting JSONPath
```

**Reasoning**

* Captures are the binding point for turning tool outputs into symbols; standardizing paths increases portability and debuggability.

---

### P1 — Platform adapter validation as a first-class command

**Outcome:** Platform adapters cannot silently drift from their schemas.

**Deliverables**

* A validator that loads every `platforms/*/manifest.json` and `tools-registry.json` and checks them against the adapter JSON Schemas already present in the repo.
* CLI entrypoints to run the validation.

**Proposed repo changes**

```text
tools/
  validate_adapters.py
packages/aps-cli-node/src/commands/
  validate-adapters.js
packages/aps-cli-py/src/aps_cli/commands/
  validate_adapters.py
```

**Reasoning**

* Adapters are the bridge between APS and host environments; schema validation prevents brittle breakage.

---

### P1 — Tool signatures layer (`predefinedTools.json`) + schema + generator

**Outcome:** `USE ... where:` becomes type-checkable; IDEs can show better completions and errors.

**Deliverables**

* A JSON Schema for `predefinedTools.json`.
* Optional generator tooling (deriving a baseline from known platform adapters / registries).
* Linter/compile hooks:

  * validate `where:` keys + value shapes when signatures exist,
  * detect signature collisions (`AG-034`),
  * optionally enforce “only declared tools are used” in strict mode.

**Proposed repo changes**

```text
skill/agnostic-prompt-standard/
  schemas/
    predefined-tools.schema.json
tools/
  gen_predefined_tools.py
packages/aps-core/src/
  tools/
    signatures.*
    where_validation.*
```

**Reasoning**

* This is the fastest path toward “type safety” without embedding tool configs inside prompts (which APS forbids).

---

### P2 — Tree-sitter grammar (incremental parsing foundation)

**Outcome:** APS can get editor-grade parsing with robust error recovery and incremental updates.

**Deliverables**

* Tree-sitter grammar for at least the APS DSL blocks (process bodies).
* Optional: grammar support for the broader envelope sections for navigation/highlighting.

**Proposed repo changes**

```text
packages/
  tree-sitter-aps/
    grammar.js
    src/
    bindings/
    README.md
```

**Reasoning**

* Establishes a reusable parsing primitive for syntax highlighting, structural navigation, and future LSP features.

---

### P2 — APS Language Server Protocol (LSP) skeleton

**Outcome:** Editors can surface APS diagnostics and navigation affordances.

**Deliverables**

* A minimal LSP server that provides:

  * Diagnostics via `aps-core` lint results.
  * Formatting via `aps-core` formatter.
  * “Go to definition” for:

    * `RUN \`process_id``→`<process id="...">`
    * format references → `<format id="...">`
* Optional: code actions for common fixes (e.g., sort `where:` keys, remove tabs, normalize spacing).

**Proposed repo changes**

```text
packages/
  aps-lsp/
    src/
      server.*
      diagnostics.*
      workspace.*
    README.md
```

**Reasoning**

* Makes APS practical to author and maintain at scale (especially when the framework targets LSP lintability).

---

### P2 — VS Code extension (editor integration)

**Outcome:** APS authors get syntax highlighting, diagnostics, and navigation directly in VS Code.

**Deliverables**

* A VS Code extension that:

  * Registers the Tree-sitter grammar for syntax highlighting.
  * Launches the APS LSP server for diagnostics, formatting, and go-to-definition.
  * Provides file associations for `.prompt.md`, `.agent.md`, and related APS file types.
* Optional: snippet support for common APS constructs (process blocks, USE statements, CAPTURE patterns).

**Proposed repo changes**

```text
packages/
  vscode-aps/
    src/
      extension.ts
    syntaxes/
    language-configuration.json
    package.json
    README.md
```

**Reasoning**

* VS Code is the primary target editor for GitHub Copilot and Agent Skills workflows; native extension support lowers friction for APS adoption.
* The extension is a thin integration layer—heavy lifting is done by Tree-sitter and LSP.

---

### P2 — Agent Skills ecosystem guardrails (portability tests + path invariants)

**Outcome:** APS remains compatible with the emerging Agent Skills directory conventions across hosts.

**Deliverables**

* Tests that assert install path logic and discovery invariants:

  * project skill paths,
  * personal skill paths,
  * optional `.claude/` behavior.
* Documentation-level checks ensuring templates and manifests remain valid.

**Proposed repo changes**

```text
packages/aps-cli-node/test/
  paths.test.js
packages/aps-cli-py/tests/
  test_paths.py
```

**Reasoning**

* APS is distributed as a Skill; portability assumptions should be tested, not implicit.

---

### P3 — CI enforcement (spec ↔ tooling consistency)

**Outcome:** Every merge preserves spec correctness and tooling reliability.

**Deliverables**

* CI workflow that runs:

  * existing checks (`check_versions.py`, `check_skill_links.py`),
  * adapter validation,
  * conformance suite,
  * unit tests for CLIs and core library.

**Proposed repo changes**

```text
.github/workflows/
  ci.yml
```

**Reasoning**

* Prevents regressions as APS grows and multiple toolchains are added.

---

## Proposed “end-state” repo additions (summary)

```text
conformance/
tools/
  run_conformance.py
  extract_spec_atoms.py
  validate_adapters.py
  gen_predefined_tools.py          # optional
skill/agnostic-prompt-standard/
  spec/
  schemas/
packages/
  aps-core/
  tree-sitter-aps/
  aps-lsp/
  vscode-aps/
packages/aps-cli-node/
  src/commands/
packages/aps-cli-py/
  src/aps_cli/commands/
.github/workflows/
  ci.yml
```

---

## Success criteria (definition of done)

* `aps lint` emits stable `AG-*` / `AG-W*` codes and locations for the conformance corpus.
* `aps fmt` produces a canonical form consistent with APS formatting rules (with idempotent output).
* `aps compile` produces a deterministic normalized prompt representation suitable for host consumption.
* Adapter validation fails fast on schema violations and is enforced in CI.
* Tree-sitter grammar and LSP can report syntax + lint diagnostics in-editor.
* VS Code extension provides syntax highlighting, diagnostics, and navigation for APS files out of the box.
* Conformance suite and CI prevent spec/tool divergence over time.

---

## Open decisions to make explicit (tracked as issues)

* **Core implementation language strategy:** single reference core vs parallel TS/Python implementations.
* **`<path>` standard choice:** JSON Pointer vs JSONPath vs dual support (and the exact mapping rules).
* **`<expr>` baseline:** keep engine-defined vs standardize a minimal portable expression subset for linting.
* **Strictness modes:** define “strict conformance” vs “host-extensions enabled” behavior in tooling output.

---

## External standards referenced (for implementers)

(Links shown as literal URLs for copy/paste stability.)

* JSON Schema (draft 2020-12): `https://json-schema.org/specification`
* JSON Pointer (RFC 6901): `https://www.rfc-editor.org/rfc/rfc6901`
* JSONPath (RFC 9535): `https://www.rfc-editor.org/rfc/rfc9535.html`
* Language Server Protocol (LSP): `https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/`
* JSON-RPC 2.0: `https://www.jsonrpc.org/specification`
* Tree-sitter: `https://github.com/tree-sitter/tree-sitter`
* GitHub Agent Skills docs (paths + conventions): `https://docs.github.com/en/copilot/concepts/agents/about-agent-skills`
