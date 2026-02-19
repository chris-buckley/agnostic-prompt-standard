# ADR Decision Index

This index is auto-generated from individual ADR files.
Run `python tools/generate_decision_index.py` to regenerate.

---

**D001** — Remove Generic Scaffolding  
: Platform adapters do not include generic project scaffolding templates.  
: *Source:* [ADR-0001 §1](0001-adapter-scope-no-scaffolding.md#1-remove-generic-scaffolding)

**D002** — Require fileConventions Field  
: `fileConventions` is required at the top level of every platform manifest.  
: *Source:* [ADR-0002 §1](0002-platform-manifest-fileconventions-required.md#1-require-fileconventions-field)

**D003** — Require Instructions Array  
: The `instructions` array within `fileConventions` remains required.  
: *Source:* [ADR-0002 §2](0002-platform-manifest-fileconventions-required.md#2-require-instructions-array)

**D004** — Add Regression Tests  
: Regression tests are added to both Node and Python CLI packages to prevent schema drift.  
: *Source:* [ADR-0002 §3](0002-platform-manifest-fileconventions-required.md#3-add-regression-tests)

**D005** — Multiple Platform Selection  
: Both CLIs accept multiple platforms via the `--platform` option.  
: *Source:* [ADR-0003 §1](0003-cli-parity-and-multi-platform-selection.md#1-multiple-platform-selection)

**D006** — Doctor Command Root Option  
: Both CLIs support `--root <path>` on the `doctor` command.  
: *Source:* [ADR-0003 §2](0003-cli-parity-and-multi-platform-selection.md#2-doctor-command-root-option)

**D007** — Platform Detection from Manifests  
: Detection markers are read from manifest files, not hardcoded.  
: *Source:* [ADR-0003 §3](0003-cli-parity-and-multi-platform-selection.md#3-platform-detection-from-manifests)

**D008** — Doctor JSON Output Structure  
: Both CLIs produce identical JSON structure for `doctor --json`.  
: *Source:* [ADR-0003 §4](0003-cli-parity-and-multi-platform-selection.md#4-doctor-json-output-structure)

**D009** — Multi-Destination Skill Installation  
: Skills are installed to multiple destinations when mixed platforms are selected.  
: *Source:* [ADR-0003 §5](0003-cli-parity-and-multi-platform-selection.md#5-multi-destination-skill-installation)

**D010** — Platform Ordering in UI  
: Platforms display in a fixed order with known platforms first.  
: *Source:* [ADR-0003 §6](0003-cli-parity-and-multi-platform-selection.md#6-platform-ordering-in-ui)

**D011** — OpenCode Platform Status  
: OpenCode is an active platform; Crush is out of scope.  
: *Source:* [ADR-0003 §7](0003-cli-parity-and-multi-platform-selection.md#7-opencode-platform-status)

**D012** — Schema Validation Libraries  
: Python uses Pydantic v2; Node uses Zod.  
: *Source:* [ADR-0003 §8](0003-cli-parity-and-multi-platform-selection.md#8-schema-validation-libraries)

**D013** — Detection Marker Format  
: Markers support both string and object formats.  
: *Source:* [ADR-0003 §9](0003-cli-parity-and-multi-platform-selection.md#9-detection-marker-format)

**D014** — File Conventions Schema  
: `fileConventions` fields are arrays, not strings.  
: *Source:* [ADR-0003 §10](0003-cli-parity-and-multi-platform-selection.md#10-file-conventions-schema)

**D015** — Test Flexibility for Platform Availability  
: Tests handle missing platforms gracefully.  
: *Source:* [ADR-0003 §11](0003-cli-parity-and-multi-platform-selection.md#11-test-flexibility-for-platform-availability)

**D016** — Pydantic Configuration Style  
: Use `ConfigDict` instead of class-based `Config`.  
: *Source:* [ADR-0003 §12](0003-cli-parity-and-multi-platform-selection.md#12-pydantic-configuration-style)

**D017** — Validation Failure Handling  
: Validation failures log warnings and attempt partial extraction.  
: *Source:* [ADR-0003 §13](0003-cli-parity-and-multi-platform-selection.md#13-validation-failure-handling)

**D018** — Marker Normalization Function  
: Both CLIs implement `normalizeDetectionMarker()` for format conversion.  
: *Source:* [ADR-0003 §14](0003-cli-parity-and-multi-platform-selection.md#14-marker-normalization-function)

**D019** — Scope Flag Conflict Handling  
: When both `--repo` and `--personal` flags are passed to `aps init`, the CLI silently prioritizes `--personal` without raising an error.  
: *Source:* [ADR-0004 §1](0004-cli-parity-output-format-behavior-consistency.md#1-scope-flag-conflict-handling)

**D020** — Platform Sorting in Platforms Command  
: The `platforms` command applies `sortPlatformsForUi` to display platforms in consistent order.  
: *Source:* [ADR-0004 §2](0004-cli-parity-output-format-behavior-consistency.md#2-platform-sorting-in-platforms-command)

**D021** — Platforms Command Table Output  
: Both CLIs display the `platforms` command output as a formatted table with columns for `platform_id`, `display_name`, and `adapter_version`.  
: *Source:* [ADR-0004 §3](0004-cli-parity-output-format-behavior-consistency.md#3-platforms-command-table-output)

**D022** — Template Planning Synchronicity  
: Python's `_plan_platform_templates` function is synchronous.  
: *Source:* [ADR-0004 §4](0004-cli-parity-output-format-behavior-consistency.md#4-template-planning-synchronicity)

**D023** — Emit raw JSON for doctor JSON mode  
: `aps doctor --json` outputs plain JSON without terminal formatting in both CLIs.  
: *Source:* [ADR-0005 §1](0005-unify-aps-cli-behavior-across-node-and-python.md#1-emit-raw-json-for-doctor-json-mode)

**D024** — Expose top-level version flag and consistent no-command exit behavior  
: Python CLI provides `aps --version`, and invoking `aps` with no subcommand exits with usage code `2` after printing help.  
: *Source:* [ADR-0005 §2](0005-unify-aps-cli-behavior-across-node-and-python.md#2-expose-top-level-version-flag-and-consistent-no-command-exit-behavior)

**D025** — Expand tilde in root paths and format home paths consistently  
: Node expands a leading `~` in `--root` and interactive workspace root input, and formats displayed paths using `~` based on the real home directory.  
: *Source:* [ADR-0005 §3](0005-unify-aps-cli-behavior-across-node-and-python.md#3-expand-tilde-in-root-paths-and-format-home-paths-consistently)

**D026** — Standardize adapter ordering and multi-adapter selection semantics  
: Both CLIs use the same adapter ordering and the same `--platform` normalization rules.  
: *Source:* [ADR-0005 §4](0005-unify-aps-cli-behavior-across-node-and-python.md#4-standardize-adapter-ordering-and-multi-adapter-selection-semantics)

**D027** — Stabilize doctor detection ordering  
: Both CLIs perform detection using a consistently ordered platform list to keep output deterministic.  
: *Source:* [ADR-0005 §5](0005-unify-aps-cli-behavior-across-node-and-python.md#5-stabilize-doctor-detection-ordering)

**D028** — Preserve timestamps when copying payload and templates  
: Node copy operations preserve file timestamps to match Python’s metadata-preserving copy behavior.  
: *Source:* [ADR-0005 §6](0005-unify-aps-cli-behavior-across-node-and-python.md#6-preserve-timestamps-when-copying-payload-and-templates)

**D029** — Align detection marker validation strictness  
: Python validates detection marker objects strictly to match Node’s schema expectations.  
: *Source:* [ADR-0005 §7](0005-unify-aps-cli-behavior-across-node-and-python.md#7-align-detection-marker-validation-strictness)

**D030** — Provide consistent alias entry point across distributions  
: The Node distribution provides an alias executable name that matches the Python distribution’s alternate entry point.  
: *Source:* [ADR-0005 §8](0005-unify-aps-cli-behavior-across-node-and-python.md#8-provide-consistent-alias-entry-point-across-distributions)

**D031** — Root command behavior parity  
: Python adds a global `--version` flag and exits with code `2` when invoked without a subcommand.  
: *Source:* [ADR-0006 §1](0006-cli-parity-edge-case-alignment.md#1-root-command-behavior-parity)

**D032** — Deterministic platform ordering  
: Both CLIs sort platforms using `DEFAULT_ADAPTER_ORDER` first, then sort any remaining platforms by `displayName`.  
: *Source:* [ADR-0006 §2](0006-cli-parity-edge-case-alignment.md#2-deterministic-platform-ordering)

**D033** — Strict detection marker validation  
: Python validates detection marker objects (`detectionMarkers`) with the same constraints as Node.  
: *Source:* [ADR-0006 §3](0006-cli-parity-edge-case-alignment.md#3-strict-detection-marker-validation)

**D034** — Cross-platform path handling  
: Node expands `~` in user-provided roots and formats home paths without relying on `$HOME`.  
: *Source:* [ADR-0006 §4](0006-cli-parity-edge-case-alignment.md#4-cross-platform-path-handling)

**D035** — Metadata-preserving copy  
: Node preserves file timestamps when copying payload skills and platform templates.  
: *Source:* [ADR-0006 §5](0006-cli-parity-edge-case-alignment.md#5-metadata-preserving-copy)

**D036** — Node binary alias parity  
: The Node package exposes `agnostic-prompt-aps` as an additional executable name.  
: *Source:* [ADR-0006 §6](0006-cli-parity-edge-case-alignment.md#6-node-binary-alias-parity)

**D037** — Three-Number Semver in Agent Names  
: Agent versions use full semver format (v1.1.7 not v1.1).  
: *Source:* [ADR-0007 §1](0007-platform-agent-template-versioning.md#1-three-number-semver-in-agent-names)

**D038** — Agent Version Parity with CLI  
: Agent version must exactly match CLI version.  
: *Source:* [ADR-0007 §2](0007-platform-agent-template-versioning.md#2-agent-version-parity-with-cli)

**D039** — Simplified Agent Filename  
: Agent files use `aps-v{version}` naming pattern.  
: *Source:* [ADR-0007 §3](0007-platform-agent-template-versioning.md#3-simplified-agent-filename)

**D040** — Platform-Specific Versioning Config  
: Each platform's manifest.json defines its own versioning patterns.  
: *Source:* [ADR-0007 §4](0007-platform-agent-template-versioning.md#4-platform-specific-versioning-config)

**D041** — Automatic Version Bump  
: bump_version.py updates agent templates alongside core files.  
: *Source:* [ADR-0007 §5](0007-platform-agent-template-versioning.md#5-automatic-version-bump)

**D042** — Intent-Based Artifact Type Detection  
: The `refine` process detects artifact type from user input using keyword matching rules.  
: *Source:* [ADR-0008 §1](0008-aps-agent-dual-artifact-generation.md#1-intent-based-artifact-type-detection)

**D043** — Dual Directory Routing  
: The `generate` process conditionally routes output to either `.github/agents/` or `.github/prompts/` based on `ARTIFACT_TYPE`.  
: *Source:* [ADR-0008 §2](0008-aps-agent-dual-artifact-generation.md#2-dual-directory-routing)

**D044** — Dynamic Frontmatter Loading  
: The `generate` process loads the appropriate frontmatter template based on `ARTIFACT_TYPE`.  
: *Source:* [ADR-0008 §3](0008-aps-agent-dual-artifact-generation.md#3-dynamic-frontmatter-loading)

**D045** — Ambiguity Resolution  
: When user intent is ambiguous, the agent asks which type they want instead of guessing.  
: *Source:* [ADR-0008 §4](0008-aps-agent-dual-artifact-generation.md#4-ambiguity-resolution)

**D046** — Single adaptor.md per Platform  
: Each platform has exactly one `adaptor.md` file using the APS envelope format (`<instructions>`, `<constants>`, `<formats>`) as its single source of truth for all configuration, tools, and format contracts.  
: *Source:* [ADR-0009 §1](0009-adaptor-md-single-source-of-truth.md#1-single-adaptormd-per-platform)

**D047** — Remove Manifest Fallback  
: CLIs load platform configuration only from `adaptor.md`, with no fallback to `manifest.json`. If `adaptor.md` is missing or unparseable, the platform is skipped.  
: *Source:* [ADR-0009 §2](0009-adaptor-md-single-source-of-truth.md#2-remove-manifest-fallback)

**D048** — Delete Legacy Files  
: Remove `manifest.json`, `tools-registry.json`, `frontmatter/` directories, `_schemas/` directory, and per-platform `README.md` files from all platform directories.  
: *Source:* [ADR-0009 §3](0009-adaptor-md-single-source-of-truth.md#3-delete-legacy-files)

**D049** — Block Constants for Structured Data
: Use `CSV<<` block constants for tool registries and `JSON<<` block constants for agent versioning configuration within `adaptor.md`.
: *Source:* [ADR-0009 §4](0009-adaptor-md-single-source-of-truth.md#4-block-constants-for-structured-data)

**D050** — Composite Asset Category
: Introduce `assets/composites/` for reusable components that bundle both `<constants>` and `<formats>` in a single file where the format contract depends on the constants as its type vocabulary.
: *Source:* [ADR-0010 §1](0010-composite-assets.md#1-composite-asset-category)

**D051** — Self-Contained Envelope
: Each composite is a self-contained APS envelope with `<constants>` defining the type vocabulary and `<formats>` defining the contract that references those constants.
: *Source:* [ADR-0010 §2](0010-composite-assets.md#2-self-contained-envelope)

**D052** — Composite Naming Convention
: Composites use the existing `<name>-v<semver>.example.md` naming convention established by constants and formats assets.
: *Source:* [ADR-0010 §3](0010-composite-assets.md#3-naming-convention)
