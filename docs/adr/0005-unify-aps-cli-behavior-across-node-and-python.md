# ADR-0005: Unify APS CLI Behavior Across Node and Python

**Date:** 2026-01-27  
**Status:** Accepted  
**Deciders:** @chris-buckley
**PR/Issue:** #13

## Context

The APS project ships two CLIs—Node (`@agnostic-prompt/aps`) and Python (`agnostic-prompt-aps`)—intended to be functionally equivalent. Behavioral drift created inconsistencies that impacted automation and user expectations, including non-machine-readable JSON output, differences in global flags, inconsistent path handling (notably `~` expansion), divergent adapter ordering in interactive selection, non-deterministic detection ordering, inconsistent file-copy metadata behavior, and differing strictness in manifest validation.

This work aligns both CLIs so the same commands and flags produce equivalent behavior and predictable outputs across platforms.

## Quick Reference

1. [Emit raw JSON for doctor JSON mode](#1-emit-raw-json-for-doctor-json-mode) — `aps doctor --json` prints plain JSON suitable for piping and parsing.
2. [Expose top-level version flag and consistent no-command exit behavior](#2-expose-top-level-version-flag-and-consistent-no-command-exit-behavior) — `aps --version` works and `aps` with no args exits with usage code `2`.
3. [Expand tilde in root paths and format home paths consistently](#3-expand-tilde-in-root-paths-and-format-home-paths-consistently) — `--root ~/repo` resolves correctly and printed paths use `~` consistently.
4. [Standardize adapter ordering and multi-adapter selection semantics](#4-standardize-adapter-ordering-and-multi-adapter-selection-semantics) — adapter lists order identically and `--platform` supports comma-separated and repeated values.
5. [Stabilize doctor detection ordering](#5-stabilize-doctor-detection-ordering) — detected adapter output order is deterministic across filesystems and OSes.
6. [Preserve timestamps when copying payload and templates](#6-preserve-timestamps-when-copying-payload-and-templates) — installation does not introduce unnecessary timestamp churn across implementations.
7. [Align detection marker validation strictness](#7-align-detection-marker-validation-strictness) — invalid marker objects are rejected consistently across CLIs.
8. [Provide consistent alias entry point across distributions](#8-provide-consistent-alias-entry-point-across-distributions) — `agnostic-prompt-aps` invokes the same CLI behavior as `aps`.

## Consequences

### Positive
- Automation becomes reliable: `aps doctor --json` output is machine-readable and stable for CI and scripting.
- CLI UX becomes predictable: global flags, help behavior, adapter ordering, and platform selection semantics match across implementations.
- Cross-platform path handling improves: `~` works consistently for `--root` and interactive root prompts.
- Configuration errors surface earlier: invalid detection marker objects fail validation consistently.

### Negative
- Stricter schema validation can break previously-tolerated (but invalid) manifests that used non-`file|dir` marker kinds.
- Preserving timestamps can be marginally slower than basic content-only copies in some environments.
- Users relying on Rich-styled JSON output (rather than plain JSON) must adjust.

### Neutral
- Documentation updates reflect the unified invocation patterns and supported multi-adapter flag usage.

## Decisions

### 1. Emit raw JSON for doctor JSON mode

**Decision:** `aps doctor --json` outputs plain JSON without terminal formatting in both CLIs.

**Behavior:**  
The CLI prints a single JSON object to stdout when `--json` is provided. The JSON contains:
- `workspace_root`: string or `null`
- `detected_adapters`: object or `null`
- `installations`: array of objects with `{ scope, path, installed }`

The output includes no ANSI escape sequences and is suitable for piping to tools like `jq` or redirecting to files.

**Rationale:**  
Machine-readable output is required for scripting and CI. Rich/pretty JSON output can embed formatting or terminal control sequences that break parsers. Node already printed raw JSON; Python is aligned to do the same rather than relying on terminal-aware rendering.

---

### 2. Expose top-level version flag and consistent no-command exit behavior

**Decision:** Python CLI provides `aps --version`, and invoking `aps` with no subcommand exits with usage code `2` after printing help.

**Behavior:**  
- `aps --version` prints the version string and exits successfully.
- `aps version` prints the same version string.
- Invoking `aps` with no command prints help text and exits with code `2`.

**Rationale:**  
Node’s Commander-based CLI supports a top-level version flag and uses a non-zero usage code when invoked without a command. Aligning Python to these semantics prevents cross-implementation surprises and matches common CLI conventions for scripting and documentation.

---

### 3. Expand tilde in root paths and format home paths consistently

**Decision:** Node expands a leading `~` in `--root` and interactive workspace root input, and formats displayed paths using `~` based on the real home directory.

**Behavior:**  
- If `--root` begins with `~` (e.g., `~/repo`), Node resolves it to the user’s home directory before `path.resolve`.
- When printing planned actions, the CLI displays paths under the user’s home directory using `~` prefix.
- Python continues to use `Path(...).expanduser()` and `Path.home()` for the same behavior.

**Rationale:**  
Python already supports `~` expansion; Node did not, leading to “works in Python but not Node” behavior. Aligning resolution and display prevents cross-shell and cross-OS surprises, particularly on macOS/Linux where `~` is common.

---

### 4. Standardize adapter ordering and multi-adapter selection semantics

**Decision:** Both CLIs use the same adapter ordering and the same `--platform` normalization rules.

**Behavior:**  
- Adapter ordering places known adapters first in `DEFAULT_ADAPTER_ORDER`:
  1) `vscode-copilot`  
  2) `claude-code`  
  3) `opencode`  
  Remaining adapters sort alphabetically by display name (case-insensitive).
- `--platform` accepts:
  - comma-separated values (e.g., `--platform vscode-copilot,claude-code`)
  - repeated flags (e.g., `--platform vscode-copilot --platform claude-code`)
- Passing `--platform none` results in an empty adapter selection.
- Duplicate platform IDs are removed while preserving first-seen order.

**Rationale:**  
Adapter selection is central to `aps init` behavior and template installation. Different ordering or selection semantics causes confusion and inconsistent installs. Normalizing both the UI order and parsing behavior ensures identical results from equivalent invocations.

---

### 5. Stabilize doctor detection ordering

**Decision:** Both CLIs perform detection using a consistently ordered platform list to keep output deterministic.

**Behavior:**  
- Platforms are loaded and ordered consistently (known adapters first, then by display name).
- Detection iterates in that order and produces stable printed output for “Detected adapters”.
- JSON output remains structurally identical, and insertion-order-dependent output remains deterministic given stable platform iteration.

**Rationale:**  
Filesystem iteration order can vary between OSes and filesystems, producing inconsistent output order even when the underlying detection results are the same. Stable ordering improves diffability, log review, and automated comparisons.

---

### 6. Preserve timestamps when copying payload and templates

**Decision:** Node copy operations preserve file timestamps to match Python’s metadata-preserving copy behavior.

**Behavior:**  
- Installing the APS payload preserves timestamps where supported by the platform.
- Copying template files preserves timestamps where supported.
- Existing files are not overwritten unless `--force` is used (or overwrite is confirmed in interactive mode where applicable).

**Rationale:**  
Python’s `shutil.copytree` and `shutil.copy2` preserve metadata by default. Node’s prior content-only copy behavior introduced unnecessary timestamp churn, which can cause noisy diffs and confusion in repos. Aligning Node to preserve timestamps improves parity and reduces “everything changed” noise.

---

### 7. Align detection marker validation strictness

**Decision:** Python validates detection marker objects strictly to match Node’s schema expectations.

**Behavior:**  
- Detection marker objects require:
  - `kind` matching `file` or `dir`
  - `label` (string)
  - `relPath` (string)
- String marker entries remain supported and normalize to:
  - `dir` when the string ends with `/`
  - `file` otherwise
- Invalid marker objects fail schema validation and are not silently normalized.

**Rationale:**  
Node’s Zod schema rejects invalid marker objects, while Python previously allowed arbitrary dicts that could result in false positives or inconsistent detection behavior. Aligning strictness ensures configuration mistakes are caught early and prevents divergence in detection outcomes.

---

### 8. Provide consistent alias entry point across distributions

**Decision:** The Node distribution provides an alias executable name that matches the Python distribution’s alternate entry point.

**Behavior:**  
- `aps` remains the primary executable.
- `agnostic-prompt-aps` invokes the same CLI entry point and behavior as `aps`.

**Rationale:**  
Users frequently share commands across ecosystems (pipx vs npm/npx). Providing a consistent alias reduces friction, particularly in documentation and cross-team environments where both CLIs may be used.
