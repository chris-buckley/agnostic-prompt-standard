```yaml
---
name: Your Agent Name
description: "What this agent does and when to use it."
# Optional: a short hint shown in the UI
argument-hint: "Describe the task…"
# Optional: list of tools/tool-sets available to this agent
tools: ['execute/runInTerminal', 'read/readFile', 'edit/createDirectory', 'edit/createFile', 'edit/editFiles', 'web/fetch', 'todo']
# Optional: default model for this agent (if your org enables model selection)
model: "GPT-4.1"
# Optional: allow VS Code to run subagents (isolated contexts)
infer: true
# Optional: platform target (helps portability)
target: vscode
# Optional: tool servers + handoffs (advanced)
mcp-servers: []
handoffs: []
---
```

Notes:
- VS Code loads custom agents from `.github/agents/*.agent.md`.
- If you see “Unexpected indentation” diagnostics, keep `description` as a **single-line** string (avoid YAML block scalars like `description: >`).
- Tool names in `tools:` may be qualified (for example: `search/codebase`, `read/problems`, `web/fetch`). Prefer the exact tool name shown by VS Code’s tools picker.
