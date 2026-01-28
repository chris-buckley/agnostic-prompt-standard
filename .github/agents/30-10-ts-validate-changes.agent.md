---
name: 30-10 TypeScript Validate Changes
description: "Run repo-aligned fast validation checks and report results."
tools: ["read", "read/problems", "execute"]
model: Claude Opus 4.5 (copilot)
argument-hint: Validate changes after edits.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST validate changes after edits using repository-aligned tooling when available (prefer package.json scripts).
You SHOULD run fast tests by default.
You MUST run a dependency vulnerability scan when available.
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
CMD_SCRIPT_TEST_FAST: "npm run test:fast"
CMD_SCRIPT_TEST: "npm test"

# Fallback direct commands
CMD_PRETTIER_CHECK: "npx prettier -c ."
CMD_BIOME_CHECK: "npx biome check ."
CMD_ESLINT: "npx eslint . --ext .ts,.tsx,.js,.jsx --max-warnings=0"
CMD_TSC_NO_EMIT: "npx tsc --noEmit"
CMD_VITEST: "npx vitest run"
CMD_JEST_FAST: "npx jest --runInBand"

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
