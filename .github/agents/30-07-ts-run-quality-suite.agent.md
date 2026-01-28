---
name: 30-07 TypeScript Run Quality Suite
description: "Run full repo-aligned quality suite including security audit and coverage when available."
tools: ["read", "execute"]
model: Claude Opus 4.5 (copilot)
argument-hint: Run format, lint, types, security, and tests with coverage.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST run the highest-signal repo-aligned quality checks available (prefer package.json scripts).
You MUST run a dependency vulnerability scan (`npm audit`/equivalent) when available.
You MUST treat tool availability as per-request capability and you MUST NOT claim tools are disabled globally.
You MUST NOT ask the user whether to enable tools.
If command execution cannot run via tools, you MUST report SKIPPED checks and provide the exact manual commands.
You MUST output exactly one `format:QUALITY_REPORT` block.
</instructions>

<constants>
# Install commands (choose based on lockfile)
CMD_INSTALL_NPM: "npm ci"
CMD_INSTALL_PNPM: "pnpm install --frozen-lockfile"
CMD_INSTALL_YARN_BERRY: "yarn install --immutable"
CMD_INSTALL_BUN: "bun install --frozen-lockfile"

# Prefer repo scripts when available
CMD_SCRIPT_FORMAT_CHECK: "npm run format:check"
CMD_SCRIPT_LINT: "npm run lint"
CMD_SCRIPT_TYPECHECK: "npm run typecheck"
CMD_SCRIPT_TEST_COV: "npm run test -- --coverage"

# Fallback direct commands (when scripts are absent)
CMD_PRETTIER_CHECK: "npx prettier -c ."
CMD_BIOME_CHECK: "npx biome check ."
CMD_ESLINT: "npx eslint . --ext .ts,.tsx,.js,.jsx --max-warnings=0"
CMD_TSC_NO_EMIT: "npx tsc --noEmit"
CMD_JEST_COV: "npx jest --coverage"
CMD_VITEST_COV: "npx vitest run --coverage"

# Hooks / pre-commit equivalents
CMD_LINT_STAGED: "npx lint-staged"

# Dependency audits (choose based on package manager)
CMD_NPM_AUDIT: "npm audit --audit-level=high"
CMD_PNPM_AUDIT: "pnpm audit --audit-level=high"
CMD_YARN_NPM_AUDIT: "yarn npm audit --all --severity high"
CMD_BUN_AUDIT: "bun audit"

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

# Prefer package.json scripts if present; otherwise fall back to direct tools.
TRY:
  USE `execute` where: command=CMD_SCRIPT_FORMAT_CHECK, explanation="Check formatting (repo script)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_PRETTIER_CHECK, explanation="Check formatting (prettier)" (atomic)
  RECOVER (e2):
    TRY:
      USE `execute` where: command=CMD_BIOME_CHECK, explanation="Check formatting/lint (biome)" (atomic)
    RECOVER (e3):
      TELL "Formatting check skipped or unavailable for this request. Use CMD_SCRIPT_FORMAT_CHECK, CMD_PRETTIER_CHECK, or CMD_BIOME_CHECK manually."

TRY:
  USE `execute` where: command=CMD_SCRIPT_LINT, explanation="Check lint (repo script)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_ESLINT, explanation="Check lint (eslint)" (atomic)
  RECOVER (e2):
    TRY:
      USE `execute` where: command=CMD_BIOME_CHECK, explanation="Check lint (biome)" (atomic)
    RECOVER (e3):
      TELL "Lint check skipped or unavailable for this request. Use CMD_SCRIPT_LINT or CMD_ESLINT manually."

TRY:
  USE `execute` where: command=CMD_SCRIPT_TYPECHECK, explanation="Check types (repo script)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_TSC_NO_EMIT, explanation="Check types (tsc --noEmit)" (atomic)
  RECOVER (e2):
    TELL "Type check skipped or unavailable for this request. Use CMD_SCRIPT_TYPECHECK or CMD_TSC_NO_EMIT manually."

# Coverage tests (prefer repo script, fall back to known runners)
TRY:
  USE `execute` where: command=CMD_SCRIPT_TEST_COV, explanation="Run tests with coverage (repo script)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_VITEST_COV, explanation="Run tests with coverage (vitest)" (atomic)
  RECOVER (e2):
    TRY:
      USE `execute` where: command=CMD_JEST_COV, explanation="Run tests with coverage (jest)" (atomic)
    RECOVER (e3):
      TELL "Coverage run skipped or unavailable for this request. Install deps (CMD_INSTALL_*) then run CMD_SCRIPT_TEST_COV, CMD_VITEST_COV, or CMD_JEST_COV."

# Pre-commit equivalents (husky + lint-staged)
TRY:
  USE `read` where: file_path=".lintstagedrc" (atomic)
  USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
RECOVER (e):
  TRY:
    USE `read` where: file_path=".lintstagedrc.json" (atomic)
    USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
  RECOVER (e2):
    TRY:
      USE `read` where: file_path=".lintstagedrc.yaml" (atomic)
      USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
    RECOVER (e3):
      TRY:
        USE `read` where: file_path=".lintstagedrc.yml" (atomic)
        USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
      RECOVER (e4):
        TRY:
          USE `read` where: file_path=".lintstagedrc.js" (atomic)
          USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
        RECOVER (e5):
          TRY:
            USE `read` where: file_path=".lintstagedrc.cjs" (atomic)
            USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
          RECOVER (e6):
            TRY:
              USE `read` where: file_path="lint-staged.config.js" (atomic)
              USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
            RECOVER (e7):
              TRY:
                USE `read` where: file_path="lint-staged.config.cjs" (atomic)
                USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
              RECOVER (e8):
                TRY:
                  USE `read` where: file_path="lint-staged.config.mjs" (atomic)
                  USE `execute` where: command=CMD_LINT_STAGED, explanation="Run lint-staged (pre-commit equivalent)" (atomic)
                RECOVER (e9):
                  # Note: lint-staged can also be configured inside package.json ("lint-staged" field). If so, run CMD_LINT_STAGED manually.
                  TELL "lint-staged run skipped or unavailable for this request. Use CMD_LINT_STAGED manually if configured."

# Dependency vulnerability scan
TRY:
  USE `execute` where: command=CMD_NPM_AUDIT, explanation="Dependency vulnerability scan (npm audit)" (atomic)
RECOVER (e):
  TRY:
    USE `execute` where: command=CMD_PNPM_AUDIT, explanation="Dependency vulnerability scan (pnpm audit)" (atomic)
  RECOVER (e2):
    TRY:
      USE `execute` where: command=CMD_YARN_NPM_AUDIT, explanation="Dependency vulnerability scan (yarn npm audit)" (atomic)
    RECOVER (e3):
      TRY:
        USE `execute` where: command=CMD_BUN_AUDIT, explanation="Dependency vulnerability scan (bun audit)" (atomic)
      RECOVER (e4):
        TELL "Dependency audit skipped or unavailable for this request. Use CMD_NPM_AUDIT / CMD_PNPM_AUDIT / CMD_YARN_NPM_AUDIT / CMD_BUN_AUDIT manually."

RETURN: format="QUALITY_REPORT"
</process>
</processes>

<input>
USER_MESSAGE: String
</input>
