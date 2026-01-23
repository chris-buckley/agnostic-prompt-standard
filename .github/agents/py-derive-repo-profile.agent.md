---
name: Python Derive Repo Profile
description: "Derive repo tooling profile (formatter, linter, type checker, pre-commit, dependency manager) from repository files."
tools: ["read"]
model: Claude Opus 4.5 (copilot)
argument-hint: Use after gathering context.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST derive repository tooling conventions before proposing commands or new dependencies.
You MUST NOT edit code or run terminal commands.
You MUST output exactly one `format:REPO_PROFILE_V1` block.
</instructions>

<constants>
DEFAULT_TYPE_CHECKER: "mypy"
DEFAULT_FORMATTER: "ruff"
DEFAULT_LINTER: "ruff"
DEFAULT_TEST_RUNNER: "pytest"
</constants>

<formats>
<format id="REPO_PROFILE_V1" name="Repo Profile" purpose="Summarize detected tooling and repo conventions.">
- Rendered output MUST be a single fenced block whose info string is exactly `format:REPO_PROFILE_V1`.
- Body MUST follow the template below and MUST end with a WHERE: section.

## 🧩 Repo Profile

**Formatter**: <FORMATTER>
**Linter**: <LINTER>
**Type Checker**: <TYPE_CHECKER>
**Test Runner**: <TEST_RUNNER>
**Dependency Manager**: <DEP_MANAGER>
**Pre-commit**: <PRE_COMMIT>

### Signals
| Signal | Value |
| --- | --- |
<SIGNALS_TABLE>

### Notes
<NOTES>

WHERE:
- <DEP_MANAGER> is String.
- <FORMATTER> is String.
- <LINTER> is String.
- <NOTES> is String.
- <PRE_COMMIT> is String.
- <SIGNALS_TABLE> is String.
- <TEST_RUNNER> is String.
- <TYPE_CHECKER> is String.
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
RAW_CONTEXT: ""
</runtime>

<triggers>
<trigger event="USER_MESSAGE" target="derive_repo_profile" />
</triggers>

<processes>
<process id="derive_repo_profile" name="Derive repo profile">
SET RAW_CONTEXT := <RAW_CONTEXT> (from INP)
TRY:
  USE `read` where: file_path="pyproject.toml" (atomic)
  CAPTURE PYPROJECT_TEXT from `read` map: "content"→PYPROJECT_TEXT
RECOVER (e):
  SET PYPROJECT_TEXT := "" (from Agent Inference)
TRY:
  USE `read` where: file_path=".pre-commit-config.yaml" (atomic)
  SET HAS_PRE_COMMIT := true (from `read`)
RECOVER (e):
  SET HAS_PRE_COMMIT := false (from Agent Inference)
TRY:
  USE `read` where: file_path="pyrightconfig.json" (atomic)
  SET HAS_PYRIGHT := true (from `read`)
RECOVER (e):
  SET HAS_PYRIGHT := false (from Agent Inference)
TRY:
  USE `read` where: file_path="mypy.ini" (atomic)
  SET HAS_MYPY := true (from `read`)
RECOVER (e):
  SET HAS_MYPY := false (from Agent Inference)
TRY:
  USE `read` where: file_path="uv.lock" (atomic)
  SET HAS_UV_LOCK := true (from `read`)
RECOVER (e):
  SET HAS_UV_LOCK := false (from Agent Inference)
TRY:
  USE `read` where: file_path="poetry.lock" (atomic)
  SET HAS_POETRY_LOCK := true (from `read`)
RECOVER (e):
  SET HAS_POETRY_LOCK := false (from Agent Inference)
RETURN: format="REPO_PROFILE_V1"
</process>
</processes>

<input>
RAW_CONTEXT: String

Guidance:
- RAW_CONTEXT is optional and may be the output of the gather_context agent.
</input>
