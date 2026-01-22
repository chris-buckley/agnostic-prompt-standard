# 2. Require fileConventions in Platform Manifest

Date: 2026-01-22

## Status
Accepted

## Context
The APS platform manifest schema previously did not require `fileConventions` at the top level, allowing adapters to validate without specifying file discovery conventions. This creates a gap where tooling cannot reliably assume `fileConventions` is present, forcing defensive checks throughout the codebase.

All existing platform adapters already define `fileConventions` with at least an `instructions` array, making this a formalization of existing practice rather than a breaking change.

## Decision
1. `fileConventions` is now REQUIRED at the top level of every platform manifest.
2. Within `fileConventions`, the `instructions` array remains required (already enforced by schema).
3. Regression tests are added to both Node and Python CLI packages to prevent schema drift.

## Consequences
*   **Positive:** Agents and tooling can treat `fileConventions` as always present without defensive checks.
*   **Positive:** Tests ensure the schema and all manifests stay in sync.
*   **Negative:** Any future platform adapters must include `fileConventions` to validate.
