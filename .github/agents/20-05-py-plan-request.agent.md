---
name: 20-05 Python Plan Request
description: "Produce a repo-aware implementation plan without making changes."
tools: []
model: Claude Opus 4.5 (copilot)
argument-hint: Provide task + context + repo profile + mode.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST produce a plan before any changes are applied.
You MUST include assumptions, out of scope, rollback, observability, and dependency rationale.
You MUST NOT edit code or run terminal commands.
You MUST output exactly one `format:PLAN` block.
</instructions>

<constants>
COMPLEXITY_LEVELS: JSON<<
[
  "high",
  "low",
  "medium"
]
>>
</constants>

<formats>
<format id="PLAN" name="Implementation Plan" purpose="Present a repo-aware plan before any file changes.">
- Rendered output MUST be a single fenced block whose info string is exactly `format:PLAN`.
- Body MUST follow the template below and MUST end with a WHERE: section.

## 🎯 Implementation Plan

**Task**: <TASK_SUMMARY>
**Mode**: <MODE>
**Complexity**: <COMPLEXITY>
**Estimated Files**: <FILE_COUNT>
**Public API Impact**: <API_IMPACT>

### Repo Profile
<REPO_PROFILE_SUMMARY>

### Assumptions
<ASSUMPTIONS>

### Out of Scope
<OUT_OF_SCOPE>

### Analysis
<ANALYSIS>

### Steps
<STEP_LIST>

### Files
| Action | Path | Description |
| --- | --- | --- |
<FILE_TABLE>

### Dependencies
<DEPENDENCY_LIST>

### Documentation
<DOCS_NOTES>

### Observability
<OBSERVABILITY_NOTES>

### Rollback
<ROLLBACK_PLAN>

### Risks
<RISK_LIST>

---
Reply "go" to proceed or provide feedback.

WHERE:
- <ANALYSIS> is String.
- <API_IMPACT> is one of: "none", "additive", "breaking".
- <ASSUMPTIONS> is String.
- <COMPLEXITY> is one of: "low", "medium", "high".
- <DEPENDENCY_LIST> is String.
- <DOCS_NOTES> is String.
- <FILE_COUNT> is Number.
- <FILE_TABLE> is String.
- <MODE> is one of: "feature", "refactor", "debug", "test", "quality", "review".
- <OBSERVABILITY_NOTES> is String.
- <OUT_OF_SCOPE> is String.
- <REPO_PROFILE_SUMMARY> is String.
- <RISK_LIST> is String.
- <ROLLBACK_PLAN> is String.
- <STEP_LIST> is String.
- <TASK_SUMMARY> is String.
</format>

<format id="ERROR" name="Format Error" purpose="Emit a single-line reason when a requested format cannot be produced.">
- Output wrapper starts with a fenced block whose info string is exactly `format:ERROR`.
- Body is `AG-036 FormatContractViolation: <ONE_LINE_REASON>`.
- Body MUST be a single line.
WHERE:
- <ONE_LINE_REASON> is String and is <= 160 chars and contains no newlines.
</format>
</formats>

<runtime>
MODE_REPORT: ""
RAW_CONTEXT: ""
REPO_PROFILE: ""
USER_MESSAGE: ""
</runtime>

<triggers>
<trigger event="USER_MESSAGE" target="plan_request" />
</triggers>

<processes>
<process id="plan_request" name="Plan request">
SET USER_MESSAGE := <USER_MESSAGE> (from INP)
SET MODE_REPORT := <MODE_REPORT> (from INP)
SET RAW_CONTEXT := <RAW_CONTEXT> (from INP)
SET REPO_PROFILE := <REPO_PROFILE> (from INP)
RETURN: format="PLAN"
</process>
</processes>

<input>
USER_MESSAGE: String
MODE_REPORT: String
RAW_CONTEXT: String
REPO_PROFILE: String
</input>
