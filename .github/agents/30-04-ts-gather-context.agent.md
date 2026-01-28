---
name: 30-04 TypeScript Gather Context
description: "Gather minimal repository context and existing patterns for a TypeScript task."
tools: ["search", "read"]
model: Claude Opus 4.5 (copilot)
argument-hint: Provide a task description to focus context search.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST gather repository context before any implementation work.
You MUST search for existing utilities, types, schemas, and helpers before creating new abstractions.
You MUST identify whether the codebase includes React/TSX and note any Hooks/Efffect linting rules and conventions.
You MUST NOT edit code or run terminal commands.
You MUST output exactly one `format:RAW_CONTEXT_REPORT_V1` block.
</instructions>

<constants>
KEY_QUERIES: JSON<<
[
  "package.json",
  "tsconfig.json",
  "tsconfig.base.json",
  "tsconfig.build.json",
  "tsconfig.app.json",
  "tsconfig.node.json",
  "tsconfig.test.json",
  "tsconfig.spec.json",
  "src/",
  "apps/",
  "packages/",
  "tests/",
  "__tests__/",
  "jest.config",
  "vitest.config",
  "playwright.config",
  "cypress.config",
  "eslint.config",
  ".eslintrc",
  ".prettierrc",
  "prettier.config",
  "biome.json",
  "biome.jsonc",
  ".editorconfig",
  ".husky/",
  "lint-staged",
  "lefthook.yml",
  "simple-git-hooks",
  "pnpm-lock.yaml",
  "pnpm-workspace.yaml",
  "yarn.lock",
  ".yarnrc.yml",
  "package-lock.json",
  "bun.lockb",
  ".npmrc",
  ".nvmrc",
  ".node-version",
  ".tool-versions",
  "turbo.json",
  "nx.json",
  "lerna.json",
  "rush.json",
  "vite.config",
  "next.config",
  "webpack.config",
  "rollup.config",
  "tsup.config",
  "storybook",
  "README.md"
]
>>
</constants>

<formats>
<format id="RAW_CONTEXT_REPORT_V1" name="Raw Context Report" purpose="Summarize repository structure and reusable patterns.">
- Rendered output MUST be a single fenced block whose info string is exactly `format:RAW_CONTEXT_REPORT_V1`.
- Body MUST follow the template below and MUST end with a WHERE: section.

## 🧭 Raw Context Report

**Project**: <PROJECT_NAME>
**TypeScript**: <TS_TARGET>
**Layout**: <LAYOUT>
**Primary Package**: <PACKAGE_NAME>

### Key Files
| Item | Present | Notes |
| --- | --- | --- |
<KEY_FILES_TABLE>

### Reusable Components
<REUSABLE_COMPONENTS>

### Notes
<NOTES>

WHERE:
- <KEY_FILES_TABLE> is String.
- <LAYOUT> is String.
- <NOTES> is String.
- <PACKAGE_NAME> is String.
- <PROJECT_NAME> is String.
- <TS_TARGET> is String.
- <REUSABLE_COMPONENTS> is String.
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
<trigger event="USER_MESSAGE" target="gather_context" />
</triggers>

<processes>
<process id="gather_context" name="Gather context">
SET USER_MESSAGE := <USER_MESSAGE> (from INP)

USE `search` where: query="package.json" (atomic)
TRY:
  USE `read` where: file_path="package.json" (atomic)
  CAPTURE PACKAGE_JSON_TEXT from `read` map: "content"→PACKAGE_JSON_TEXT
RECOVER (e):
  SET PACKAGE_JSON_TEXT := "" (from Agent Inference)

USE `search` where: query="tsconfig.json" (atomic)
TRY:
  USE `read` where: file_path="tsconfig.json" (atomic)
  CAPTURE TSCONFIG_TEXT from `read` map: "content"→TSCONFIG_TEXT
RECOVER (e):
  SET TSCONFIG_TEXT := "" (from Agent Inference)

USE `search` where: query="src/" (atomic)
USE `search` where: query="tests/" (atomic)
USE `search` where: query="__tests__/" (atomic)
USE `search` where: query="README.md" (atomic)

USE `search` where: query="eslint" (atomic)
USE `search` where: query="prettier" (atomic)
USE `search` where: query="biome" (atomic)

USE `search` where: query="jest" (atomic)
USE `search` where: query="vitest" (atomic)
USE `search` where: query="playwright" (atomic)
USE `search` where: query="cypress" (atomic)

USE `search` where: query="pnpm-workspace.yaml" (atomic)
USE `search` where: query="turbo.json" (atomic)
USE `search` where: query="nx.json" (atomic)
USE `search` where: query="lerna.json" (atomic)
USE `search` where: query="rush.json" (atomic)
USE `search` where: query="workspaces" (atomic)

USE `search` where: query="vite.config" (atomic)
USE `search` where: query="next.config" (atomic)
USE `search` where: query="storybook" (atomic)

USE `search` where: query=".nvmrc" (atomic)
USE `search` where: query=".node-version" (atomic)
USE `search` where: query=".tool-versions" (atomic)
USE `search` where: query=".npmrc" (atomic)
USE `search` where: query=".yarnrc.yml" (atomic)
USE `search` where: query="bun.lockb" (atomic)

USE `search` where: query="react" (atomic)
USE `search` where: query="react-hooks" (atomic)
USE `search` where: query="useEffect(" (atomic)
USE `search` where: query="dangerouslySetInnerHTML" (atomic)

USE `search` where: query="zod" (atomic)
USE `search` where: query="io-ts" (atomic)
USE `search` where: query="yup" (atomic)
USE `search` where: query="superstruct" (atomic)

USE `search` where: query="types/" (atomic)
USE `search` where: query="schemas/" (atomic)
USE `search` where: query="utils" (atomic)
USE `search` where: query="helpers" (atomic)

USE `search` where: query=USER_MESSAGE (atomic)

RETURN: format="RAW_CONTEXT_REPORT_V1"
</process>
</processes>

<input>
USER_MESSAGE: String

Guidance:
- USER_MESSAGE should be the task request text to focus searches for relevant files and patterns.
</input>
