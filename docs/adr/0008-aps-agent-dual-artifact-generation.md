# ADR-0008: APS Agent Dual Artifact Generation

**Date:** 2026-02-04
**Status:** Accepted
**Deciders:** Chris Buckley, Juan Burckhardt
**PR/Issue:** #15

## Context

The APS agent template for VS Code Copilot was hardcoded to generate only `.prompt.md` files. When users explicitly requested "create an agent," the system would still output a `.prompt.md` file, violating user intent. This caused confusion because VS Code Copilot distinguishes between:

- **Agents** (`.github/agents/*.agent.md`) — autonomous workflows with tools
- **Prompts** (`.github/prompts/*.prompt.md`) — reusable prompt templates

The original implementation had `PROMPTS_DIR` and `PROMPT_EXT` constants with no equivalent for agents, and the `generate` process always wrote to the prompts directory.

## Quick Reference

1. [Intent-Based Artifact Type Detection](#1-intent-based-artifact-type-detection) — Detect whether user wants agent or prompt from keywords
2. [Dual Directory Routing](#2-dual-directory-routing) — Route output to correct directory based on detected type
3. [Dynamic Frontmatter Loading](#3-dynamic-frontmatter-loading) — Load correct frontmatter template for artifact type
4. [Ambiguity Resolution](#4-ambiguity-resolution) — Ask user when intent is unclear

## Consequences

### Positive

- Users who say "create an agent" get an `.agent.md` file
- Users who say "create a prompt" get a `.prompt.md` file
- System respects explicit user intent
- Frontmatter matches the artifact type (agent fields vs prompt fields)

### Negative

- Added complexity to the `refine` process with type detection logic
- Three possible states for `ARTIFACT_TYPE` (`agent`, `prompt`, `ask`) instead of implicit prompt-only

### Neutral

- Renamed variables from `PROMPT_*` to `ARTIFACT_*` for generality
- Added new constants (`AGENTS_DIR`, `AGENT_EXT`, frontmatter paths, `TYPE_RULES`)

## Decisions

### 1. Intent-Based Artifact Type Detection

**Decision:** The `refine` process detects artifact type from user input using keyword matching rules.

**Behavior:** The agent sets `ARTIFACT_TYPE` based on `TYPE_RULES` before generating any output. Keywords like "agent", "create an agent", "autonomous", "workflow agent" map to `agent`. Keywords like "prompt", "create a prompt", "reusable prompt", "snippet" map to `prompt`. Requests describing autonomous/multi-step behavior with tools default to `agent`. Requests describing reusable templates default to `prompt`.

**Rationale:** Explicit keyword detection is deterministic and debuggable. Users naturally use these terms when describing what they want. This approach handles the common case without requiring an extra question.

---

### 2. Dual Directory Routing

**Decision:** The `generate` process conditionally routes output to either `.github/agents/` or `.github/prompts/` based on `ARTIFACT_TYPE`.

**Behavior:** When `ARTIFACT_TYPE = "agent"`, the file path uses `AGENTS_DIR` (`.github/agents/`) and `AGENT_EXT` (`.agent.md`). When `ARTIFACT_TYPE = "prompt"`, the file path uses `PROMPTS_DIR` (`.github/prompts/`) and `PROMPT_EXT` (`.prompt.md`). The `TARGET_DIR` runtime variable tracks which directory to create before writing.

**Rationale:** VS Code Copilot requires files in specific directories with specific extensions. Routing based on detected type ensures the output is valid for the platform.

---

### 3. Dynamic Frontmatter Loading

**Decision:** The `generate` process loads the appropriate frontmatter template based on `ARTIFACT_TYPE`.

**Behavior:** The agent reads either `AGENT_FRONTMATTER_PATH` or `PROMPT_FRONTMATTER_PATH` into `FM_CONTENT` before generating the artifact. The frontmatter template provides the correct YAML fields for the artifact type (e.g., `infer`, `handoffs` for agents; `agent` for prompts).

**Rationale:** Agents and prompts have different frontmatter schemas. Loading the correct template ensures generated files are valid and include type-appropriate fields.

---

### 4. Ambiguity Resolution

**Decision:** When user intent is ambiguous, the agent asks which type they want instead of guessing.

**Behavior:** If `ARTIFACT_TYPE = "ask"` after applying `TYPE_RULES`, the `refine` process sets `INTENT_OK := false` and returns a clarification question with options: (a) Agent, (b) Prompt, (c) Describe use case, (d) Cancel. This happens before any generation occurs.

**Rationale:** Asking is better than guessing wrong. The question is presented only when necessary, not on every request. This preserves the conversational flow while ensuring correct output.
