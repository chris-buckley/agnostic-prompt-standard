# Why APS Exists

APS makes more sense when you see it in action, so this starts with small, complete examples. The greeting and the table aren't the point. The point is that the structure and the output rules are explicit, easy to validate, and easy to move between systems.

APS itself is a specification. It defines the contract: section structure, naming rules, format rules, error codes, and logging and privacy requirements. The enforcement part comes from APS-aware engines and linters that compile, validate, and run prompts that claim APS conformance.

## Start with examples

### "Hello world": the smallest useful APS prompt

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

Example output (what downstream automation can rely on):

```format:HELLO_V1
Hello, world!
```

### Before vs. after: a small failure example

Before (no contract, brittle parsing):

```markdown
API Coverage
- GET /users ✅

Looks good overall.
```

After (contract-first, machine-parseable, and it fails fast if the shape changes):

```text
<format id="API_COVERAGE_MIN_V1" name="API Coverage" purpose="Minimal stable table for automation.">
## <TITLE>
| Method | Path | Gap |
| --- | --- | --- |
| <METHOD> | <PATH> | <GAP> |

WHERE:
- <TITLE> is String.
- <METHOD> is one of: GET, POST, PUT, PATCH, DELETE.
- <PATH> is Path; starts with "/".
- <GAP> is one of: OK, MISSING_PATH, MISSING_METHOD.
</format>
```

```format:API_COVERAGE_MIN_V1
## User API Coverage
| Method | Path | Gap |
| --- | --- | --- |
| GET | /users | OK |
```

If the model adds extra prose, changes headers, or drops a required column, an APS-aware validator rejects it with a specific error (for example `AG-036 FormatContractViolation` or `AG-040 FormatFenceError`) instead of letting corrupted data slip through.

### Costs and tradeoffs

APS adds structure up front. You need an APS-aware linter or engine in your workflow to get the guarantees. Some "quick and dirty" prompting patterns become intentionally harder.

But the assumption that structured prompts are automatically longer prompts is wrong. In practice, APS often makes prompts smaller.

Think about what inflates a typical unstructured prompt. You repeat yourself because there's no way to define something once and reference it. You spell out the same output shape in three different places because there's no format contract to point to. You write paragraph after paragraph of prose explaining control flow that a FOREACH loop or a GIVEN/WHEN/THEN block would express in a few lines. You duplicate context across agents because there's no way to derive a value once and pass it downstream.

APS gives you the tools to stop doing all of that. Constants mean you define a value once and reference it everywhere. Format contracts mean you declare an output shape once instead of describing it repeatedly in prose. Processes with loops (FOREACH), conditionals (GIVEN/WHEN/THEN), and subroutine calls (RUN) compress what would otherwise be pages of step-by-step instructions into compact, reusable control flow. The "Agent as Authority" pattern means you derive context once and flow it as data, instead of stuffing the same background into every agent's prompt.

The state-machine structure helps too. Because each section has a clear job, you don't waste tokens on transitional prose explaining what you're about to say or what you just said. Instructions go in instructions. Config goes in constants. Output shape goes in formats. There's no need to narrate the structure when the structure narrates itself.

So yes, APS has a learning curve and requires tooling. But the tradeoff isn't "more structure equals more tokens." It's "more structure equals fewer repeated tokens, less ambiguity, and prompts that are often shorter than the unstructured version they replace."

It pays off when prompts become long-lived assets, feed automation, or need to be portable, auditable, and safe.

## Use cases

### 1) One spec across multiple AI hosts

Your org uses VS Code Copilot for day-to-day development, Claude Code CLI for deep refactors, and OpenCode for batch automation. Each host discovers files differently, uses different tool naming, has different permission UX, and expects different frontmatter fields.

Without APS, you maintain three incompatible instruction stacks and debug "works on my agent" failures. With APS, the core spec stays constant. The `aps init --platform <target>` CLI generates the correct platform-specific artifacts. Migrating between platforms means swapping the adapter, not rewriting the logic.

### 2) Automation-safe AI outputs

You have an agent generating API coverage reports in a CI pipeline. Every few weeks, a model update slightly changes the Markdown formatting, breaking the regex parser that extracts the coverage score. Models add extra prose, reorder columns, rename headers, or drop required fields.

With APS format contracts, output must match a declared shape and must be one fenced `format:<ID>` block. The CI step rejects non-conforming output with a specific error code instead of silently producing bad data.

### 3) Prompts as reviewable engineering artifacts

Typical prompts mix policy, steps, hidden assumptions, tool usage, and output formatting in a single blob. Reviewing them is guesswork. Small changes have unpredictable effects.

APS forces separation: instructions are one directive per line, constants are typed and read-only, formats are declared contracts, processes are formal control logic. Changes become reviewable like code. New engineers see labeled sections and documented contracts instead of tribal knowledge.

### 4) Reproduce behavior under model drift

Models change behavior over time. Even if you pin a model version, tool results or environment changes shift behavior. If your prompt is unstructured prose, reproducibility collapses.

APS pushes toward deterministic execution: explicit process steps, explicit tool calls with typed parameters, explicit CAPTURE points, explicit RETURN values, deterministic concurrency via PAR/JOIN. "Why did it do that?" becomes answerable. You can version workflows like programs and diff behavior across model versions.

### 5) Privacy as a contract

Agents log too much, copy secrets into outputs, or echo PII. Teams add "don't leak secrets" as prose, but enforcement is inconsistent and unverifiable.

APS makes privacy enforceable: engines must redact secrets and PII as `[REDACTED]`, SNAP supports explicit redaction lists, logging has structured capture points. Privacy policy becomes a real contract, audit trails become safer, and specs become reusable across sensitive environments.

### 6) Prompt CI

Prompts break silently. Malformed tags, comments where forbidden, tabs, invalid identifiers, placeholder mismatches, missing WHERE definitions, wrong tool signatures. Without tooling, you discover failures at runtime, often in production.

APS has normative lint rules, a formal EBNF grammar for compile-time checking, and a formal error taxonomy with named codes. You can lint specs in CI like you lint code and enforce organization-wide policies with the same tooling you use for everything else.

### 7) Standardize orchestration across teams

Every team invents its own way to plan, execute, record results, handle errors, and decide when to stop. Outputs vary wildly. Workflows are undocumented.

APS provides shared primitives: GIVEN/WHEN/THEN for conditions, RUN/USE/CAPTURE/SET/RETURN for execution, TRY/RECOVER for errors, PAR/JOIN for concurrency, and error codes as a shared failure language. Teams can share specs and understand them immediately. Handoffs between agents become predictable. "How we do AI work" becomes teachable rather than tribal.

### 8) Scale autonomy safely

As models become more capable, they also become more dangerous: chaining tool calls, modifying repositories, exfiltrating data via web tools, doing too much without asking. "Do your best" doesn't scale.

APS makes tool usage explicit and auditable. Platform adapters encode tool risk classifications and side effects. Workflows can enforce read-only phases vs. write phases. TRY/RECOVER constrains error behavior. The safety policy defines harm thresholds and decision logic. You can scale autonomy incrementally and audit what tools were intended to be used at each step.

## Concrete examples

### Example 1: a format contract in CI

A docs indexer agent produces a documentation map. The format contract:

```
<formats>
<format id="DOCS_INDEX_V1" name="Documentation Index"
        purpose="Token-efficient hierarchical documentation map.">
# <PROJECT_TITLE> Documentation Map

> Last updated: <TIMESTAMP>

## <GROUP_NAME>

### [<PAGE_TITLE>](<PAGE_URL>)
* <HEADING_TEXT>
  * <SUBHEADING_TEXT>

WHERE:
- <PROJECT_TITLE> is String; name of the project.
- <TIMESTAMP> is ISO8601; when the index was generated.
- <GROUP_NAME> is String; documentation section name.
- <PAGE_TITLE> is String; title of the documentation page.
- <PAGE_URL> is URI; link to the documentation page.
- <HEADING_TEXT> is String; H2/H3 heading text.
- <SUBHEADING_TEXT> is String; nested heading under parent.
</format>
</formats>
```

A CI step validates: does the agent's output parse as a single `format:DOCS_INDEX_V1` fenced block? Are all required placeholders resolved? Are timestamps ISO 8601? If not, the build fails with a specific AG-0xx error code. No regex hacking. No "it looks about right."

### Example 2: deterministic parallel research

An agent needs to fetch documentation from three sources simultaneously. In unstructured prompts, the model calls tools in whatever order it prefers, and results bind nondeterministically.

With APS:

```
PAR:
  USE `fetch_api_docs` where: source="openapi"
  USE `fetch_api_docs` where: source="graphql"
  USE `fetch_api_docs` where: source="grpc"
JOIN:
  CAPTURE OPENAPI_DOCS from `fetch_api_docs`
  CAPTURE GRAPHQL_DOCS from `fetch_api_docs`
  CAPTURE GRPC_DOCS from `fetch_api_docs`
```

Results bind in lexical order regardless of completion time. If any call fails, JOIN raises a composite error with the first hard error and aggregates others as suppressed. Deterministic, auditable, reproducible.

### Example 3: cross-platform agent generation

Your core spec defines a code reviewer agent. From this single source, APS adapters generate:

For VS Code Copilot (`.github/agents/code-reviewer.agent.md`): YAML frontmatter with `tools: [search/codebase, search/changes, read/readFile, read/problems]`, `user-invokable: true`, `disable-model-invocation: false`.

For Claude Code (`.claude/agents/code-reviewer.md`): YAML frontmatter with `tools: Read, Grep, Glob, Bash`, `disallowedTools: Write, Edit`, `permissionMode: default`.

The agent's behavior spec (what it reviews, how it reports findings, what format the output takes) is identical. Only the platform mapping changes.

## What APS actually is

APS is a system description standard. It's a way to describe systems so both humans and agents can read, write, and reason about the same artifact.

The most common adoption path is agent prompts: structured instructions that govern autonomous behavior across platforms. But it fits anywhere you'd benefit from a structured, machine-readable specification. API contracts, runbooks, compliance policies, deployment pipelines, organizational processes, architecture docs.

The core abstraction is a structured envelope with seven ordered sections:

1. Instructions: directives that govern behavior (one per line, imperative, lintable).
2. Constants: read-only values resolved before execution (inline, JSON blocks, TEXT blocks, YAML blocks, CSV blocks).
3. Formats: output contracts with placeholders, types, and WHERE clauses.
4. Runtime: environment-specific bindings (dev, staging, prod).
5. Triggers: event-to-process mappings.
6. Processes: executable control logic using a formal DSL.
7. Input: dynamic data consumed by the system.

The separation is intentional. Instructions don't drift into process logic. Constants don't hide in prose. Output shapes are declared, not implied. Environment bindings don't leak into core logic. Each section has its own lint rules, validation requirements, and authoring constraints.

APS is to system descriptions what TypeScript is to JavaScript: optional rigor that pays off at scale. APS defines the contract (the structural rules, error codes, and behavioral requirements). Enforcement comes from engines and linters that implement it, just as TypeScript's type system is defined by the spec but enforced by `tsc`. When this document says "engines MUST," it means the spec places a normative obligation on implementations. APS itself doesn't ship an executor.

## What APS enables

### Contract-first outputs

APS format contracts define exactly what a system's output looks like: columns, headers, placeholders, and types. The WHERE clause validates every placeholder. Rendered output must be a single fenced `format:<ID>` block with no surrounding prose. If the output doesn't match the contract, it triggers `AG-036 FormatContractViolation`, a lint-time failure, not a runtime mystery.

This works like type checking. A WHERE definition like `<OPERATION> is one of: GET, POST, PUT, PATCH, DELETE` is an enum constraint. `<TIMESTAMP> is ISO8601` is a type constraint. `<URI> is Path; MUST NOT start with "/"` is a validation rule. These constraints make outputs machine-consumable without fragile parsing.

A concrete illustration:

```
<formats>
<format id="TABLE_API_COVERAGE_V1" name="API Coverage Table"
        purpose="Report API operation coverage against a specification.">
## <TABLE_NAME>
| Operation | URI | SpecRef | Gap |
| --- | --- | --- | --- |
| <OPERATION> | <URI> | <SPEC_REF> | <GAP> |

WHERE:
- <TABLE_NAME> is String; title for the API coverage table.
- <OPERATION> is one of: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS.
- <URI> is Path; starts with "/".
- <SPEC_REF> is String; reference to the relevant API specification.
- <GAP> is one of: OK, MISSING_PATH, MISSING_METHOD, REQ_SCHEMA_MISMATCH.
</format>
</formats>
```

A CI pipeline consuming this output knows the exact structure and allowed values. When a model update tweaks Markdown formatting, the contract catches it. When an engineer adds an endpoint, the coverage table reflects it in a parseable row. That's the shift: "AI wrote a report" becomes "AI produced a validated artifact."

### Deterministic agent control

When an AI executes shell commands or edits code, "do your best" isn't a safety policy. APS uses a formal DSL within `<processes>` to define execution boundaries.

The DSL includes BDD-style control flow (GIVEN/WHEN/THEN), explicit tool invocation (USE with typed parameters), structured variable binding (SET/CAPTURE/RETURN), error handling (TRY/RECOVER), iteration (FOREACH), and deterministic concurrency (PAR/JOIN).

PAR/JOIN is worth looking at closely. When an agent needs to call three tools in parallel, APS requires lexical ordering of the PAR block, makes JOIN the first legal CAPTURE point, and mandates that CAPTURE order follows the lexical order of USE statements regardless of completion time. This wipes out an entire class of nondeterminism bugs that show up when agents coordinate multiple tool calls.

TRY/RECOVER blocks give agents defined fallback behavior. Without them, an agent hitting an error either halts unexpectedly or improvises. Improvised error handling from a language model is unpredictable. With APS, recovery paths are specified, tested, and auditable.

### Cross-platform portability

APS separates the normative specification (the `references/` directory) from non-normative platform mappings (the `platforms/` directory). The spec stays stable. Adapters handle translation.

Each adapter documents file locations, frontmatter templates, tool naming and risk classification, hooks, import syntax, and permissions. Today APS ships adapters for VS Code Copilot, Claude Code, and OpenCode. Adding a new platform means copying the `_template/` skeleton and filling in `manifest.json` and `tools-registry.json`. You don't change the spec.

The tool naming abstraction is a good illustration. Claude Code calls its shell tool `Bash`. VS Code Copilot calls it `execute/runInTerminal`, and the runtime function name is `run_in_terminal`. APS tool registries map these names so prompt logic references a canonical identifier. When VS Code renamed `problems` to `read/problems`, the adapter absorbed the change. Prompts didn't move.

### Fail-fast validation

The error taxonomy defines hard errors and warnings, each with a code, name, and description (see `references/07-error-taxonomy.md`). Malformed tags (AG-009), tab characters (AG-011), unresolved placeholders (AG-006), mismatched process arguments (AG-044), missing WHERE sections (AG-041): all caught at lint time, not runtime.

This makes "prompt CI" possible. Lint specs in your pipeline like you lint code. Run `aps doctor` to validate an installation. Enforce organization-wide policies. Catch prompt bugs before they reach a model.

### Privacy and redaction as requirements

APS treats logging and privacy as normative, not advisory. Engines must redact secrets and PII as `[REDACTED]` (AG-032). SNAP statements support explicit redaction lists. When you snapshot state for debugging, listed symbols are zeroed in prior state, new state, and artifacts. TELL statements that reference redacted symbols emit only the symbol name, never the content.

For teams under GDPR, HIPAA, or SOC2, this is the difference between "we told the model not to leak secrets" and "we can prove the tooling enforces redaction."

### Derive once, flow downstream

APS follows the "Agent as Authority" principle. Within a single workflow, consult an authority once at the natural derivation point, then flow the result as data to all consumers. Don't duplicate context across dozens of agents. Don't create "service agents" that exist only to answer "what is X?" and get called over and over.

One derivation. Many consumers. No repeated queries. This saves tokens, reduces hallucination drift, and makes runs more deterministic and traceable.

## The cost of no standard

### The inconsistency tax

Picture a team of 12 engineers building AI-assisted features. Each writes prompts differently: different structures, different conventions, different assumptions about what the model knows. Reviewing a teammate's prompt means spending more time understanding the format than evaluating the logic. When a prompt breaks in production, there's no standard way to trace what went wrong. The team moves slowly because every prompt is a snowflake.

This applies beyond prompts too. When each team describes their service's behavior in its own format (one uses Notion docs, another uses ADRs, a third uses inline comments), cross-team understanding collapses. APS provides a shared structure that makes any system description reviewable like code.

### The platform trap

A company builds 30 agent configurations on Claude Code. Six months later, leadership standardizes on VS Code Copilot for half the team. Every agent file, every instruction set, every tool reference needs manual translation. File paths change. Frontmatter syntax changes. Tool names change (`Bash` becomes `execute/runInTerminal`, `Read` becomes `read/readFile`). The migration takes weeks and introduces regressions that take months to find.

APS separates normative logic from platform conventions. Platform adapters handle file discovery, frontmatter dialects, and tool naming. Your core system description stays constant. Switching platforms means swapping the adapter, not rewriting the specification.

### The audit gap

A financial services firm uses AI agents to assist with compliance reviews. A regulator asks: "What instructions governed this agent's behavior on March 15th? What changed between March and April? How do you validate that the agent's outputs conform to your specifications?"

The team has a folder of markdown files, some versioned, some not. Nobody can answer with confidence.

APS prompts are plain text files in version control. Every change is a commit with an author, timestamp, and message. The structured logging spec defines capture points at every RUN, USE, CAPTURE, SET, and RETURN. The error taxonomy provides named failure codes for every structural violation. The privacy spec requires redaction of secrets and PII. You can reconstruct exactly what instructions an agent operated under and what it did.

### Specification rot

Most specifications (prompts or otherwise) are "successful once" and then degrade. The original author leaves. Model behavior shifts. Tool availability changes. Output shapes evolve. Safety constraints get added ad hoc. People copy-paste snippets until nothing is consistent.

APS prevents rot by forcing specs to be lintable, diffable, and contract-bound. Constants are typed. Formats have WHERE clauses. Processes have formal grammar. Identifiers follow naming regexes. Comments are forbidden (they rot; directives don't). The spec either validates or it doesn't. There is no "mostly correct."

## How we built APS: structure plus plain language

We combined the precision of code structure with controlled-language ideas. The foundation was Standard Technical English (ASD-STE100), which uses controlled vocabulary, active voice, short sentences, and one instruction per sentence so procedures don't get fuzzy. More on STE here: https://www.asd-ste100.org/

We also leaned into a practical observation: modern language models tend to follow Python- and JavaScript-shaped structure well because those patterns show up constantly in training data (see "LLMs Love Python 2025": https://arxiv.org/html/2503.L7181vJ). So APS borrows structural habits from those languages and uses them to define seven ordered sections. Then it applies STE-style clarity rules inside those sections.

The result behaves like a state machine. Each section has a job, the prompt moves through sections in a defined order, and you go from static rules to dynamic input without mixing everything into one blob. APS is model-agnostic and modular, so humans and agents can both read and write the same spec. We validated the approach with experiments across multiple model families (including Nvidia, Anthropic, OpenAI, Google, and Microsoft/Phi) and across smaller and larger sizes.

## What programming languages give you, and what APS gives system descriptions

Programming languages aren't successful because they're convenient. They're successful because they give you structural guarantees that unstructured text can't. APS exists to bring those same guarantees to system descriptions: prompts, specs, runbooks, contracts, and any artifact that tells a system how to behave.

Everything below is something you get from a programming language. APS aims to provide an equivalent for the specs that drive agents and describe systems.

Types and contracts. You declare the shape of data. A compiler or runtime checks it before anything runs. Consumers know what to expect without reading the implementation. APS does this with format contracts: WHERE clauses, typed placeholders, and enum constraints. Output shape is declared and validated, not hoped for.

Abstraction and encapsulation. You hide complexity behind interfaces. APS mirrors this with named processes (behavior behind an id), constants (config separated from logic), and a fixed envelope that keeps concerns separated.

Composability. Small pieces combine into larger pieces because they share interfaces. APS uses processes that call other processes via RUN, format contracts that define stable outputs, and skills that package reusable components.

Predictability. Same inputs, same outputs, and an evaluation order you can reason about. APS pushes in that direction with read-only constants, defined placeholder resolution order, deterministic PAR/JOIN capture ordering, and "no randomness without a seed."

Scope and namespacing. Languages keep variables from leaking everywhere. APS does the same: SET variables are local unless RETURNed, WITH defaults shadow outer defaults without leaking, and FOREACH loop variables stay inside the loop.

Structured error handling. Languages force you to face failure. APS uses TRY/RECOVER with named error bindings, a formal taxonomy with named codes for structural violations (see `references/07-error-taxonomy.md`), and ASSERT statements for runtime preconditions. Engines must treat hard errors as fatal.

Iteration primitives. Languages give you safe ways to apply work across collections. APS has FOREACH with deterministic index-order iteration. Empty collections skip the body, and engines expose the current index.

Concurrency primitives. Languages give you async tools with synchronization rules. APS has PAR/JOIN: PAR launches concurrent tool invocations in lexical order, JOIN is the sync point, CAPTURE order is deterministic, and composite errors aggregate failures predictably.

Modularity and packaging. Code becomes libraries. APS treats skills as versioned units with `SKILL.md` entrypoints, semantic versioning, and distribution via npm and PyPI. Platform adapters live separately from the core spec.

Linting and static analysis. Structure makes linting possible. APS includes normative lint rules (comments forbidden, tabs forbidden, one directive per line), a formal EBNF grammar for compile-time checking, and error codes for structural violations.

Testability. Clear inputs and outputs make tests possible. APS has ASSERT statements inside processes, testable format contracts ("does output match the declared shape?"), and typed process signatures that can be validated against callers.

Refactoring safety. In code, renames and type changes surface breakage. In APS, process ids, tool names, symbols, and format ids are formal references. Rename a process id and every RUN targeting it breaks visibly. Rename a format id and every reference to it surfaces. (Examples: AG-004 missing process reference, AG-039 undefined format reference.)

Versioning and diffing. Stable syntax makes diffs meaningful. APS has seven fixed sections in a defined order, with distinct rules per section. Diffs show what changed without archaeology.

Documentation generation. Language structure lets tools extract docs. APS format WHERE clauses are self-documenting contracts, process signatures declare arguments and types, and `SKILL.md` metadata is machine-extractable.

Interoperability and standards. Shared conventions make ecosystems work. APS uses platform adapters to map into host conventions, and tool registries to normalize naming across platforms. One spec can generate correct artifacts for VS Code Copilot, Claude Code, and OpenCode.

Access control and permissions. Languages encode visibility and boundaries. APS pushes permission logic into platform adapters (tool risk classification and side effects) plus a safety policy that defines thresholds and decision rules. Processes can enforce read-only phases versus write phases.

Optimization. Compilers optimize because they understand structure. APS engines can do similar things: deduplicate idempotent USE calls via stable input hashes, resolve constants at compile time, and surface unused symbols as warnings (for example AG-W01).

Reproducibility. Pinned deps and deterministic builds let you recreate artifacts later. APS aims for reproducible runs via immutable constants, defined resolution order, deterministic logging hashes, and version-pinned skills.

Formal verification. Some languages support proofs. APS doesn't pretend to be that, but it does provide hooks: ASSERT/ASSERT ALL for runtime property checks, WHERE clauses for type and range constraints, and a grammar that makes conformance decidable.

Redaction and privacy. Most languages don't treat this as native, but APS does because it has to. Engines must redact secrets and PII as `[REDACTED]`. SNAP supports explicit redaction lists. Logging rules are normative.

That mapping is the core idea: APS provides language-like guarantees at the specification layer, where they were missing.

## The paradox of exponential AI

A common objection: "Models are getting so good that structured prompting standards will stop mattering." The opposite is usually what happens.

The empirical trends are clear and accelerating. Model intelligence is increasing. Context windows are expanding, letting you inject more data per interaction. Supported data types are diversifying toward robotics and multimodal. Latency is decreasing. Steerability is improving. Cost per equivalent capability is falling. Models that need cloud infrastructure today will run on consumer hardware 12 months from now.

Every one of these trends makes structured specifications more valuable. None of them solve the specification problem itself.

Every leap in AI capability expands the surface area of what agents can do. Early models could summarize text. Current models orchestrate multi-step workflows, call tools, modify codebases, manage state, and make decisions with real consequences. Each capability jump creates an order-of-magnitude increase in use cases, and every one of those use cases needs reliable, repeatable, reviewable instructions.

When a model can only answer questions, a sloppy prompt costs you a bad paragraph. When it can execute code, modify files, call APIs, and coordinate with other agents, a sloppy prompt costs you a production incident.

We've seen this pattern before. Compilers got better, but programming languages didn't become unnecessary. Databases got faster, but SQL didn't go away. Browsers got smarter, but HTML standards became more important, not less. HTTP didn't replace English; it created a protocol for machines to communicate reliably. Capability improvements make structure more valuable. They don't replace it.

As models become dramatically more capable, the bottleneck shifts further toward governance, reproducibility, tool safety, integration, portability, auditability, and maintainability. Raw intelligence doesn't remove these needs. It raises the stakes. More capable agents can do more damage, drift further, and get used for higher-stakes automation.

## The interface bottleneck

Two problems persist regardless of how capable models become, even given superintelligence and unlimited compute.

Intent translation. Getting your thoughts and intent across to an AI model is an interface problem, not an intelligence problem. A superintelligent model that misunderstands your intent executes the wrong thing faster and more confidently. No amount of model intelligence compensates for ambiguous instructions. It only makes the consequences worse. As steerability improves, precise specs yield more precise results, and imprecise specs yield more precisely wrong results.

Contextual awareness. Understanding your specific situation (your deployment environment, your compliance requirements, your team's conventions, your risk tolerance) requires explicit specification. Models don't absorb this context by becoming smarter. They absorb it by being told. The precision of that telling determines the precision of the outcome.

This is exactly what produced Standard Technical English (STE) in aerospace. Ambiguous natural language in maintenance documentation caused errors, not because technicians were unintelligent, but because natural language is inherently imprecise for procedural work. STE solved this with constrained vocabulary and grammar rules. APS follows the same logic for the AI age: constrained structure and vocabulary for system descriptions, because ambiguous natural language causes agent errors regardless of how smart the model is.

APS scales with models because it addresses the interface layer, the constant bottleneck, not the intelligence layer. As models get smarter, they follow APS specs more faithfully. As context windows grow, more structured data can be injected via constants and input sections. As cost falls and models reach consumer hardware, more people without engineering backgrounds start writing agent instructions, and the need for structural guardrails grows. The better the model, the higher the return on precise specification.

## Beyond prompts: APS as a system description language

The seven-section envelope describes any system that receives input, follows rules, uses tools, and produces output. That covers most systems. The interface bottleneck (translating human intent and context into machine-executable specification) applies to all of these domains, not just AI prompts.

### API behavior contracts

An API's behavior is a system: it receives requests (input), follows business rules (instructions + processes), calls downstream services (tool invocations), and produces responses (format contracts). APS can describe these contracts in a form that both humans review and AI agents consume, whether for generating client code, validating responses, generating test cases, or documenting behavior.

The format contracts work the same way whether the output is an agent's response or an API's JSON body. The WHERE clause validates identically. The error taxonomy catches the same structural violations.

### Operational runbooks

A runbook is a process triggered by events. APS models this directly: triggers map events (alert fired, threshold exceeded, deployment failed) to processes. Processes use GIVEN/WHEN/THEN to express conditions, TRY/RECOVER for escalation paths, and format contracts for incident reports.

A traditional runbook is prose that nobody follows under pressure. An APS runbook is a validated spec that an agent can execute step-by-step, or that a human can follow with the same structure. The BDD pattern (GIVEN this incident, WHEN this condition holds, THEN take this action) is immediately familiar to anyone who's written a test.

### Compliance and policy

Regulatory requirements are systems. They define constraints (instructions), reference thresholds (constants), require specific report formats (format contracts), and mandate audit trails (logging). APS can encode these requirements in a machine-readable, lintable format.

When an auditor asks "what policy governed this decision?", the answer is a versioned APS file in git, not a paragraph buried in a Confluence page. The safety vocabulary (WARNING, CAUTION, NOTICE) is standardized. The decision logic (PROCEED / PROCEED_WITH_CAUTION / HOLD_FOR_REVIEW) is explicit.

### Data pipelines

A data pipeline receives input, transforms it through stages, and produces output. APS processes model each stage. FOREACH handles batch iteration. PAR/JOIN handles parallel ETL stages with deterministic capture ordering. Constants hold configuration. Runtime holds environment-specific bindings. Format contracts define the shape of intermediate and final outputs.

### Organizational knowledge

When someone asks "how does our deployment process work?", the answer is usually tribal knowledge spread across wiki pages, Slack threads, and one person's memory. An APS specification of the deployment process (triggers, processes, decision points, format contracts for approval gates) is a single, versionable, reviewable artifact that both humans and AI agents can consume.

The two-way readability is the point. Traditional specs (OpenAPI, ADRs, runbooks) are human-first, with machines parsing them as an afterthought. APS was designed from the start to be written and read by both humans and AI agents. The vocabulary constraints, tense rules, and line discipline exist to serve both audiences.

## When to use APS

APS pays off most when any of these are true:

- You maintain more than a handful of prompts or agent configurations.
- You run agents on more than one host (IDE, CLI, CI runner).
- You need outputs to be machine-consumable by downstream systems.
- You need reproducibility and audit trails for compliance or debugging.
- You have privacy or safety constraints that must be enforced, not implied.
- You want to treat specs as real assets with versioning and CI.
- You expect rapid model, tool, or platform evolution.
- You need to describe systems (not just prompts) in a form both humans and AI can consume.

### When APS isn't necessary

APS isn't needed for single-use casual prompts, one-off conversations, or exploratory work where the goal is speed rather than reliability. If you're asking a model a question and reading the answer yourself, natural language is fine. APS is for when the answer feeds another system, when the prompt will be maintained by a team, or when the behavior must be reproducible and auditable.

APS also isn't a replacement for domain expertise. Knowing your domain is still the hard part. APS is the container for encoding that knowledge in a form that AI agents can consume deterministically and that your team can review, version, and maintain.

## Starter portfolio

If you want APS to show value quickly, these are high-leverage early specs:

1. Repo analyst: emits a validated code map and risk summary using format contracts.
2. Implementation planner: emits a SMEAC-style plan contract with phases, success criteria, and rollback.
3. PR reviewer: emits a fixed review checklist format with actionable findings.
4. Docs indexer: emits a docs map contract and link manifest.
5. Release note generator: emits a stable changelog format (not "vibes").
6. Security sweep: emits a structured findings table with severity taxonomy.
7. CI assistant: reads test failures and returns a deterministic remediation plan.

As the portfolio grows, APS makes these composable rather than a pile of bespoke prompts. Shared constants, shared format contracts, and shared vocabulary mean each new spec builds on the work already done.

## Getting started

```bash
npx @agnostic-prompt/aps init                           # Install skill (default path)
npx @agnostic-prompt/aps init --platform claude-code    # Claude Code path
npx @agnostic-prompt/aps doctor                         # Validate installation
npx @agnostic-prompt/aps platforms                      # List available adapters
```

Or with Python:

```bash
pipx run agnostic-prompt-aps init
pipx run agnostic-prompt-aps doctor
```

The spec is MIT licensed. The normative spec lives in `references/`. Platform adapters live in `platforms/`. Reusable assets (format templates, constant examples) live in `assets/`.

Start with one format contract on one agent. You'll feel the difference the first time a model tries to "be helpful" with extra prose and your validator shuts it down.
