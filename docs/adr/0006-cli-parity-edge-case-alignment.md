# ADR-006: CLI Parity Edge Case Alignment

**Date:** 2026-01-27
**Status:** Accepted
**Deciders:** APS maintainers
**PR/Issue:** N/A

## Context

The Node and Python APS CLIs aim to behave identically, but several edge cases had drifted:

- Python lacked a global `--version` flag and exited with success when invoked without a subcommand, unlike the Node CLI.
- `doctor --json` in Python used Rich JSON rendering, which can include formatting not suitable for piping.
- Platform ordering was deterministic in Node but not in Python `doctor`, and `init` in Node ordered unknown platforms by ID rather than display name.
- Node did not expand `~` in user-supplied roots and formatted paths using `$HOME`, which breaks on some platforms.
- Node copy operations did not preserve timestamps, while Python used `copy2` semantics.
- Python accepted invalid detection marker objects that Node rejected.

This ADR captures the decisions made to close these remaining parity gaps.

## Quick Reference

1. [Root command behavior parity](#1-root-command-behavior-parity) — Python adds a global `--version` flag and returns exit code `2` when no subcommand is provided.
2. [Deterministic platform ordering](#2-deterministic-platform-ordering) — Both CLIs sort platforms using `DEFAULT_ADAPTER_ORDER` then display name.
3. [Strict detection marker validation](#3-strict-detection-marker-validation) — Python validates detection marker objects with the same constraints as Node.
4. [Cross-platform path handling](#4-cross-platform-path-handling) — Node expands `~` and formats home paths safely.
5. [Metadata-preserving copy](#5-metadata-preserving-copy) — Node preserves file timestamps when copying payload and templates.
6. [Node binary alias parity](#6-node-binary-alias-parity) — Node exposes the `agnostic-prompt-aps` executable alias.

## Consequences

### Positive
- `aps --version` works consistently across Node and Python.
- `aps` without arguments behaves consistently (help to stderr, exit code `2`).
- `doctor --json` outputs pipe-friendly JSON with stable ordering.
- Platform selection ordering is consistent across CLIs and commands.
- Adapter detection uses only valid marker definitions.
- Template installation preserves timestamps across CLIs.

### Negative
- Python becomes stricter: invalid marker objects that previously parsed now surface as validation failures (and fall back to partial extraction).
- Preserving timestamps in Node can fail on some filesystems or permission configurations.

### Neutral
- Node template preview and copy output uses forward slashes for relative paths to keep output stable across operating systems.

## Decisions

### 1. Root command behavior parity

**Decision:** Python adds a global `--version` flag and exits with code `2` when invoked without a subcommand.

**Behavior:**
- The Python CLI prints the semantic version string when invoked with `--version` and exits successfully.
- The Python CLI prints the help text to stderr and exits with code `2` when invoked without a subcommand.

**Rationale:** The Node CLI already implements `--version` and a non-zero usage exit code when no subcommand is supplied. Matching this behavior improves scripting consistency and reduces surprises when switching CLIs.

---

### 2. Deterministic platform ordering

**Decision:** Both CLIs sort platforms using `DEFAULT_ADAPTER_ORDER` first, then sort any remaining platforms by `displayName`.

**Behavior:**
- Interactive platform selection in `init` lists platforms in a known-first order, followed by any additional platforms sorted lexicographically by `displayName`.
- `doctor` evaluates and reports platforms in the same stable order.

**Rationale:** Deterministic ordering improves UX and makes CLI output stable for tests and CI. Sorting unknown platforms by display name matches the Python UI behavior and is more user-friendly than sorting by ID.

---

### 3. Strict detection marker validation

**Decision:** Python validates detection marker objects (`detectionMarkers`) with the same constraints as Node.

**Behavior:**
- Marker objects accept only `kind: "file" | "dir"`.
- Invalid marker objects cause manifest validation to fail, and callers use the safe-parse fallback path.

**Rationale:** Allowing invalid marker objects can change detection behavior in subtle ways and diverges from Node. Strict validation keeps manifests well-formed and ensures both CLIs interpret them identically.

---

### 4. Cross-platform path handling

**Decision:** Node expands `~` in user-provided roots and formats home paths without relying on `$HOME`.

**Behavior:**
- The Node CLI expands leading `~`, `~/`, and `~\\` to the user's home directory for `--root` and interactive root prompts.
- Path formatting replaces only the *leading* home directory prefix with `~` and does not corrupt paths when `$HOME` is unset.

**Rationale:** Python already supports home expansion and safe home formatting. Implementing the same behavior in Node prevents incorrect path rendering on Windows and improves parity across platforms.

---

### 5. Metadata-preserving copy

**Decision:** Node preserves file timestamps when copying payload skills and platform templates.

**Behavior:**
- Copy operations in Node use timestamp-preserving semantics so that copied files keep source mtime/atime when possible.

**Rationale:** Python uses `shutil.copy2`/`copytree` defaults that preserve metadata. Matching this behavior reduces noise in diffs and aligns outcomes across CLIs.

---

### 6. Node binary alias parity

**Decision:** The Node package exposes `agnostic-prompt-aps` as an additional executable name.

**Behavior:**
- Installing the Node CLI provides both `aps` and `agnostic-prompt-aps` entry points.

**Rationale:** The Python package already exposes both script names. Adding the alias in Node improves parity and reduces friction for users who standardize on a single command name.
