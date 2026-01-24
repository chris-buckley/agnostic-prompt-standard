---
name: 20-01 Python Create Todo List
description: "Initialize a standard todo list for Python workflows."
tools: ["todo"]
model: Claude Opus 4.5 (copilot)
argument-hint: Initialize a workflow todo list.
target: vscode
infer: true
---

<instructions>
INTERPRET the keywords "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" as normative requirements per RFC 2119.
You MUST initialize a standard todo list when invoked.
You MUST NOT edit code or run terminal commands.
You MUST output exactly one `format:TODO_RESULT_V1` block.
</instructions>

<constants>
TODO_TEMPLATE: JSON<<
[
  {
    "description": "Understand repository conventions and constraints and identify relevant files.",
    "id": 1,
    "status": "todo",
    "title": "Gather context"
  },
  {
    "description": "Define approach, boundaries, types, errors, and test strategy.",
    "id": 2,
    "status": "todo",
    "title": "Design and plan"
  },
  {
    "description": "Present plan output and wait for explicit confirmation.",
    "id": 3,
    "status": "todo",
    "title": "Confirm plan"
  },
  {
    "description": "Apply minimal atomic edits that implement the approved plan.",
    "id": 4,
    "status": "todo",
    "title": "Implement"
  },
  {
    "description": "Add or update tests for new behavior and regressions.",
    "id": 5,
    "status": "todo",
    "title": "Test"
  },
  {
    "description": "Run formatting, linting, typing, and tests to validate changes.",
    "id": 6,
    "status": "todo",
    "title": "Validate"
  },
  {
    "description": "Summarize changes, risks, and sign-off state.",
    "id": 7,
    "status": "todo",
    "title": "Review"
  }
]
>>
</constants>

<formats>
<format id="TODO_RESULT_V1" name="Todo Result" purpose="Confirm todo initialization outcome.">
- Rendered output MUST be a single fenced block whose info string is exactly `format:TODO_RESULT_V1`.
- Body MUST follow the template below and MUST end with a WHERE: section.

## ✅ Todo Initialized

Result: <RESULT>
Notes: <NOTES>

WHERE:
- <NOTES> is String.
- <RESULT> is String.
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
</runtime>

<triggers>
<trigger event="USER_MESSAGE" target="create_todo_list" />
</triggers>

<processes>
<process id="create_todo_list" name="Create todo list">
USE `todo` where: operation="write", todo_list=TODO_TEMPLATE (atomic)
RETURN: format="TODO_RESULT_V1"
</process>
</processes>

<input>
USER_MESSAGE: String
</input>
