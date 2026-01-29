# ADR-002: Require fileConventions in Platform Manifest

**Date:** 2026-01-22
**Status:** Accepted
**Deciders:** APS maintainers
**PR/Issue:** N/A

## Context

The APS platform manifest schema previously did not require `fileConventions` at the top level, allowing adapters to validate without specifying file discovery conventions. This creates a gap where tooling cannot reliably assume `fileConventions` is present, forcing defensive checks throughout the codebase. All existing platform adapters already define `fileConventions` with at least an `instructions` array, making this a formalization of existing practice rather than a breaking change.

## Quick Reference

1. [Require fileConventions Field](#1-require-fileconventions-field) — `fileConventions` is mandatory at the top level of every platform manifest.
2. [Require Instructions Array](#2-require-instructions-array) — The `instructions` array within `fileConventions` remains required.
3. [Add Regression Tests](#3-add-regression-tests) — Tests ensure schema and manifests stay synchronized.

## Consequences

### Positive
- Agents and tooling can treat `fileConventions` as always present without defensive checks
- Tests ensure the schema and all manifests stay in sync

### Negative
- Any future platform adapters must include `fileConventions` to validate

### Neutral
- Existing adapters already comply; no migration needed

## Decisions

### 1. Require fileConventions Field

**Decision:** `fileConventions` is required at the top level of every platform manifest.

**Behavior:** Platform manifest validation fails if `fileConventions` is missing. The CLI and any tooling that loads manifests can assume this field is always present.

**Rationale:** All existing adapters already include this field. Formalizing the requirement eliminates defensive coding patterns and makes the contract explicit for future adapter authors.

---

### 2. Require Instructions Array

**Decision:** The `instructions` array within `fileConventions` remains required.

**Behavior:** The `instructions` field must be an array of strings specifying file patterns for instruction files. Empty arrays are valid but the field must be present.

**Rationale:** Instruction file discovery is the minimum functionality expected from a platform adapter. Requiring this field ensures every adapter provides at least basic file convention information.

---

### 3. Add Regression Tests

**Decision:** Regression tests are added to both Node and Python CLI packages to prevent schema drift.

**Behavior:** Test suites validate that:
- The JSON schema requires `fileConventions`
- All bundled manifests pass schema validation
- Schema changes that would remove required fields cause test failures

**Rationale:** Schema drift between the specification and bundled manifests can cause subtle bugs. Automated tests catch these issues before they reach users.
