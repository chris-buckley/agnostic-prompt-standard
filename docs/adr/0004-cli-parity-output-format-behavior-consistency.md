# ADR-004: CLI Parity Alignment: Output Format and Behavior Consistency

**Date:** 2026-01-27
**Status:** Accepted
**Deciders:** @chris-buckley
**PR/Issue:** CLI Parity Review

## Context

Following the initial CLI parity work documented in ADR-0003, a subsequent review identified additional behavioral and output differences between the Node and Python CLI implementations. These differences, while minor, could cause confusion for users switching between implementations or writing tooling that depends on consistent output. This ADR documents the decisions made to resolve these remaining parity issues.

## Quick Reference

1. [Scope Flag Conflict Handling](#1-scope-flag-conflict-handling) — When both `--repo` and `--personal` are passed, `--personal` takes priority silently
2. [Platform Sorting in Platforms Command](#2-platform-sorting-in-platforms-command) — The `platforms` command applies consistent sorting with known adapters first
3. [Platforms Command Table Output](#3-platforms-command-table-output) — Both CLIs display platforms in a formatted table with identical columns
4. [Template Planning Synchronicity](#4-template-planning-synchronicity) — Python's template planning function is synchronous to match actual I/O behavior

## Consequences

### Positive
- Users experience identical behavior regardless of which CLI implementation they use
- Platform listing order is predictable and consistent across commands and sessions
- Table output improves readability over plain text lists
- Python implementation is simpler without unnecessary async machinery

### Negative
- Silent handling of conflicting scope flags may confuse users who expect an error
- Table rendering in Node requires manual box-drawing character handling

### Neutral
- Both implementations now apply `sortPlatformsForUi` in the `platforms` command
- Version display for platforms without `adapterVersion` shows empty string in both CLIs

## Decisions

### 1. Scope Flag Conflict Handling

**Decision:** When both `--repo` and `--personal` flags are passed to `aps init`, the CLI silently prioritizes `--personal` without raising an error.

**Behavior:** The `init` command accepts both `--repo` and `--personal` flags. If both are provided, the install scope resolves to `personal`. The evaluation order is: if `--personal` is true, scope is `personal`; else if `--repo` is true, scope is `repo`; else auto-detect based on git repository presence.

**Rationale:** The Node implementation already exhibited this behavior. Rather than adding validation to Node (a breaking change for scripts that may pass both flags), Python was aligned to match. This follows the principle of least surprise for users with existing workflows. Explicit validation could be added in a future major version if user feedback indicates confusion.

---

### 2. Platform Sorting in Platforms Command

**Decision:** The `platforms` command applies `sortPlatformsForUi` to display platforms in consistent order.

**Behavior:** The `aps platforms` command sorts output with known adapters (`vscode-copilot`, `claude-code`, `opencode`) first in that order, followed by any additional platforms sorted alphabetically by display name. This matches the sorting already applied in the interactive `init` command.

**Rationale:** The Node CLI's `platforms` command was only applying alphabetical sorting by `displayName` via `loadPlatforms`, while `init` used `sortPlatformsForUi`. Python applied consistent sorting in both places. Aligning Node ensures users see the same platform order regardless of which command they run.

---

### 3. Platforms Command Table Output

**Decision:** Both CLIs display the `platforms` command output as a formatted table with columns for `platform_id`, `display_name`, and `adapter_version`.

**Behavior:** The `aps platforms` command outputs a table titled "APS Platform Adapters" with three columns. Python uses Rich's `Table` component with automatic column sizing. Node renders a table using Unicode box-drawing characters (`┌`, `─`, `┬`, `│`, `├`, `┼`, `┤`, `└`, `┴`, `┘`) with manually calculated column widths. When `adapterVersion` is null or undefined, an empty string is displayed.

**Rationale:** The previous Node implementation used plain text with dash prefixes (e.g., `- vscode-copilot: VS Code Copilot (v1.0.0)`), while Python used a Rich table. Table format improves readability when comparing multiple platforms. While Python's Rich library handles table rendering automatically, Node required manual implementation to achieve visual parity. The empty string for missing versions avoids implying uncertainty where there is simply no version specified.

---

### 4. Template Planning Synchronicity

**Decision:** Python's `_plan_platform_templates` function is synchronous.

**Behavior:** The function performs file system checks using Python's synchronous `pathlib` operations (`Path.is_dir()`, `Path.exists()`). It returns a list of `PlannedPlatformTemplates` objects directly without async/await. Callers invoke it as a normal function call, not via `asyncio.get_event_loop().run_until_complete()`.

**Rationale:** The previous implementation was marked `async` but contained no `await` statements, requiring awkward `asyncio.run_until_complete()` calls at the call site. Since Python's standard `pathlib` operations are inherently synchronous, the async wrapper provided no benefit and added complexity. The Node implementation uses async filesystem operations appropriately for its runtime model (Node's `fs/promises`), but this is an implementation detail that doesn't affect the external API contract.