# ADR-0010: Composite Assets

**Date:** 2026-02-19
**Status:** Accepted
**Deciders:** @chris-buckley
**PR/Issue:** #43

## Context

The APS skill `assets/` directory previously contained two subdirectories:

- `constants/` — standalone `<constants>` block examples (e.g., JSON, TEXT, CSV block syntax)
- `formats/` — standalone `<format>` contract examples (e.g., code maps, tables, plans)

These work well for simple, single-concern assets. However, some reusable components are inherently **self-contained systems** where constants and formats are tightly coupled — the format contract directly references the constants as its type vocabulary. Splitting them across two directories would break the coupling and force consumers to manually reunite them.

The GUI component specification is the first example: it defines design token vocabularies (spacing scales, color roles, typography styles) as constants, then uses a format contract that references those exact constant names in its `WHERE` clauses. Separating these into `constants/gui-tokens.md` and `formats/gui-component-spec.md` would lose the self-documenting relationship.

## Quick Reference

1. [Composite Asset Category](#1-composite-asset-category) — A third `assets/composites/` directory for bundled constants + formats.
2. [Self-Contained Envelope](#2-self-contained-envelope) — Each composite is a single file with `<constants>` and `<formats>` sections.
3. [Naming Convention](#3-naming-convention) — Composites follow the existing `<name>-v<semver>.example.md` pattern.

## Consequences

### Positive
- Tightly coupled constants and formats stay together as a single importable unit
- Composites are valid APS documents that demonstrate the envelope format in practice
- No changes to existing `constants/` or `formats/` directories — additive only

### Negative
- Introduces a third asset category, slightly increasing cognitive overhead

### Neutral
- SKILL.md and AGENTS.md need to document the new `composites/` directory
- The composite file format is identical to platform adaptor.md files (both use `<constants>` + `<formats>`)

---

## Decisions

### 1. Composite Asset Category

Add `assets/composites/` as a third subdirectory alongside `constants/` and `formats/`.

**Decision:** Introduce a `composites/` asset category for reusable components that bundle both `<constants>` and `<formats>` in a single file where the format contract depends on the constants as its type vocabulary.

**Rationale:** When a format contract's `WHERE` clauses reference constant names (e.g., `<COLOR_ROLE> is one of: COLOR_ROLE`), the constants and format are a single logical unit. Separating them would require consumers to manually pair the correct constants file with the correct format file, creating a fragile coupling across directories.

### 2. Self-Contained Envelope

Each composite file uses the standard APS envelope structure:

```
<constants>
SCALE_A: "value_1 | value_2 | value_3"
SCALE_B: "value_4 | value_5"
</constants>

<formats>
<format id="..." name="..." purpose="...">
...

WHERE:
- <PLACEHOLDER> is one of: SCALE_A.
</format>
</formats>
```

**Decision:** Each composite is a self-contained APS envelope with `<constants>` defining the type vocabulary and `<formats>` defining the contract that references those constants.

**Rationale:** This mirrors the structure already used in platform adaptor.md files, keeping the pattern consistent. An optional `<instructions>` section can be included if the composite needs generation guidance.

### 3. Naming Convention

Composites follow the same naming pattern as other assets:

```
<descriptive-name>-v<major>.<minor>.<patch>.example.md
```

Example: `gui-component-spec-v1.0.0.example.md`

**Decision:** Composites use the existing `<name>-v<semver>.example.md` naming convention established by constants and formats assets.

**Rationale:** Consistent naming across all asset categories reduces cognitive overhead and allows tooling to discover assets uniformly.
