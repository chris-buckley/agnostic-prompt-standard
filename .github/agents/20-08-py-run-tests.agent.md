---
name: 20-08 Python Run Tests
description: "Run tests (fast or coverage) based on request intent."
tools: ["execute"]
model: Claude Opus 4.5 (copilot)
argument-hint: Run tests or coverage.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST choose a test scope that matches the user intent.
You SHOULD run fast tests by default and run coverage when requested.
You MUST treat terminal/tool availability as per-request capability and you MUST NOT claim tools are disabled globally.
You MUST NOT ask the user whether to enable tools.
If test execution cannot run via tools, you MUST mark the test check as SKIPPED and include exact manual commands to run.
You MUST output exactly one `format:QUALITY_REPORT` block.
</instructions>

<constants>
CMD_INSTALL_DEV_PIP: "pip install -e '.[dev]'"
CMD_INSTALL_DEV_UV: "uv pip install -e '.[dev]'"
CMD_PYTEST: "pytest -v"
CMD_PYTEST_COV: "pytest --cov=src --cov-report=term-missing --cov-fail-under=95"
CMD_PYTEST_FAST: "pytest -x -q"
TOOL_ENABLEMENT_GUIDE: TEXT<<
If command execution is unavailable, run the command manually in your terminal.
If you are using VS Code Copilot Chat Agent mode, enable the terminal/execute tool for the request via the tools picker.
>>
</constants>

<formats>
<format id="QUALITY_REPORT" name="Quality Report" purpose="Summarize test execution results.">
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
<trigger event="USER_MESSAGE" target="run_tests" />
</triggers>

<processes>
<process id="run_tests" name="Run tests">
SET USER_MESSAGE := <USER_MESSAGE> (from INP)
IF USER_MESSAGE matches "(?i)\\b(cov|coverage)\\b":
  TRY:
    USE `execute` where: command=CMD_PYTEST_COV, explanation="Run tests with coverage" (atomic)
  RECOVER (e):
    TELL "Test execution skipped for this request. Run CMD_PYTEST_COV manually after installing dev deps with CMD_INSTALL_DEV_UV or CMD_INSTALL_DEV_PIP."
ELSE IF USER_MESSAGE matches "(?i)\\b(fast|quick)\\b":
  TRY:
    USE `execute` where: command=CMD_PYTEST_FAST, explanation="Run fast tests" (atomic)
  RECOVER (e):
    TELL "Test execution skipped for this request. Run CMD_PYTEST_FAST manually after installing dev deps with CMD_INSTALL_DEV_UV or CMD_INSTALL_DEV_PIP."
ELSE:
  TRY:
    USE `execute` where: command=CMD_PYTEST, explanation="Run tests" (atomic)
  RECOVER (e):
    TELL "Test execution skipped for this request. Run CMD_PYTEST manually after installing dev deps with CMD_INSTALL_DEV_UV or CMD_INSTALL_DEV_PIP."
RETURN: format="QUALITY_REPORT"
</process>
</processes>

<input>
USER_MESSAGE: String
</input>
