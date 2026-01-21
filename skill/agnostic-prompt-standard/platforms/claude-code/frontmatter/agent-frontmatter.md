```yaml
---
# Custom subagent frontmatter for Claude Code
# Subagents are stored in .claude/agents/*.md

# Required: unique identifier (lowercase, hyphens only)
name: my-subagent

# Required: description that triggers this subagent
description: "What this subagent does and when to use it."

# Optional: AI model to use
# Options: sonnet, opus, haiku, inherit (default: sonnet)
model: inherit

# Optional: allowed tools (allowlist)
# Comma-separated tool names
tools: Read, Grep, Glob, Bash

# Optional: denied tools (denylist)
# Comma-separated tool names
disallowedTools: Write, Edit

# Optional: permission handling mode
# Options: default, acceptEdits, dontAsk, bypassPermissions, plan
permissionMode: default

# Optional: skills to inject
# Comma-separated skill names
skills: ""

# Optional: lifecycle hooks (only apply during subagent execution)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---
```

Notes:
- Claude Code loads subagents from `.claude/agents/*.md` (project) and `~/.claude/agents/*.md` (user).
- Subagents are invoked via the `Task` tool when their description matches the request.
- The `name` field must be unique across all loaded subagents.
- Both `tools` (allowlist) and `disallowedTools` (denylist) can be used together.

Permission modes:

| Mode | Description |
|------|-------------|
| `default` | Normal permission prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Minimal prompts |
| `bypassPermissions` | Skip all prompts (use with caution) |
| `plan` | Plan mode — research only, no edits |

Examples:

```yaml
---
# Read-only research agent
name: researcher
description: Research and explore the codebase without making changes
model: haiku
tools: Read, Grep, Glob, WebFetch, WebSearch
disallowedTools: Write, Edit, Bash
permissionMode: plan
---
```

```yaml
---
# Code reviewer with validation hooks
name: code-reviewer
description: Expert code review specialist for reviewing changes
model: inherit
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo 'Running: $TOOL_INPUT'"
---
```

```yaml
---
# Test runner agent
name: test-runner
description: Run tests and report results
model: sonnet
tools: Bash, Read, Glob
permissionMode: acceptEdits
---
```
