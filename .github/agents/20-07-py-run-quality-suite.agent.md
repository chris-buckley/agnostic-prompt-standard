---
name: 20-07 Python Run Quality Suite
description: "Run full repo-aligned quality suite including security scan and coverage when available."
tools: ["read", "execute"]
model: Claude Opus 4.5 (copilot)
argument-hint: Run lint, format, types, security, and tests with coverage.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST run the highest-signal repo-aligned quality checks available.
You MUST run security checks and dependency audit when available.
You MUST treat tool availability as per-request capability and you MUST NOT claim tools are disabled globally.
You MUST NOT ask the user whether to enable tools.
If command execution cannot run via tools, you MUST report SKIPPED checks and provide the exact manual commands.
You MUST output exactly one `format:QUALITY_REPORT` block.
</instructions>

<constants>
CMD_BANDIT: "bandit -r src/ -ll"
CMD_BLACK_CHECK: "black --check ."
CMD_INSTALL_DEV_PIP: "pip install -e '.[dev]'"
CMD_INSTALL_DEV_UV: "uv pip install -e '.[dev]'"
CMD_MYPY: "mypy src/"
CMD_PIP_AUDIT: "pip-audit"
CMD_PRE_COMMIT: "pre-commit run --all-files"
CMD_PYRIGHT: "pyright"
CMD_PYTEST_COV: "pytest --cov=src --cov-report=term-missing --cov-fail-under=95"
CMD_RUFF_CHECK: "ruff check ."
CMD_RUFF_FORMAT_CHECK: "ruff format --check ."
TOOL_ENABLEMENT_GUIDE: TEXT<<
If command execution is unavailable, run the commands manually in your terminal.
If you are using VS Code Copilot Chat Agent mode, enable the terminal/execute tool for the request via the tools picker.
>>
</constants>

<formats>
<format id="QUALITY_REPORT" name="Quality Report" purpose="Summarize full quality suite checks and findings.">
- Rendered output MUST be a single fenced block whose info string is exactly `format:QUALITY_REPORT`.
- Body MUST follow the template below and MUST end with a WHERE: section.

## ✅ Quality Report

| Check | Status | Details |
| --- | --- | --- |
<CHECK_TABLE>

### Issues Found
<ISSUES>

### Recommendations
<RECOMMENDATIONS>

WHERE:
- <CHECK_TABLE> is String.
- <ISSUES> is String.
- <RECOMMENDATIONS> is String.
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
USER_MESSAGE: ""
</runtime>

<triggers>
<trigger event="USER_MESSAGE" target="run_quality_suite" />
</triggers>

<processes>
<process id="run_quality_suite" name="Run quality suite">
SET USER_MESSAGE := <USER_MESSAGE> (from INP)
TRY:
  USE `execute` where: command=CMD_RUFF_FORMAT_CHECK, explanation="Check formatting (ruff)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_BLACK_CHECK, explanation="Check formatting (black)" (atomic)
  RECOVER (e):
    TELL "Formatting check skipped or unavailable for this request. Use CMD_RUFF_FORMAT_CHECK or CMD_BLACK_CHECK manually."
TRY:
  USE `execute` where: command=CMD_RUFF_CHECK, explanation="Check lint (ruff)" (atomic)
RECOVER (e):
  TELL "Lint check skipped or unavailable for this request. Use CMD_RUFF_CHECK manually."
TRY:
  USE `execute` where: command=CMD_PYRIGHT, explanation="Check types (pyright)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_MYPY, explanation="Check types (mypy)" (atomic)
  RECOVER (e):
    TELL "Type check skipped or unavailable for this request. Use CMD_PYRIGHT or CMD_MYPY manually."
TRY:
  USE `execute` where: command=CMD_BANDIT, explanation="Security scan (bandit)" (atomic)
RECOVER (e):
  TELL "Bandit scan skipped or unavailable for this request. Use CMD_BANDIT manually."
TRY:
  USE `execute` where: command=CMD_PIP_AUDIT, explanation="Dependency vulnerability scan (pip-audit)" (atomic)
RECOVER (e):
  TELL "Dependency audit skipped or unavailable for this request. Use CMD_PIP_AUDIT manually."
TRY:
  USE `execute` where: command=CMD_PYTEST_COV, explanation="Run tests with coverage" (atomic)
RECOVER (e):
  TELL "Coverage run skipped or unavailable for this request. Install dev deps with CMD_INSTALL_DEV_UV or CMD_INSTALL_DEV_PIP then run CMD_PYTEST_COV."
TRY:
  USE `read` where: file_path=".pre-commit-config.yaml" (atomic)
  USE `execute` where: command=CMD_PRE_COMMIT, explanation="Run pre-commit hooks" (atomic)
RECOVER (e):
  TELL "Pre-commit run skipped or unavailable for this request. Use CMD_PRE_COMMIT manually if configured."
RETURN: format="QUALITY_REPORT"
</process>
</processes>

<input>
USER_MESSAGE: String
</input>
