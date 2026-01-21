# Claude Code CLI adapter

This adapter documents **how APS fits into Claude Code's configuration system**.

## What this adapter provides

- `manifest.json` — file conventions, docs links, hooks/imports/permissions
- `tools-registry.json` — built-in tools with risk levels and capabilities
- `frontmatter/` — YAML templates for rules and subagents

## Quickstart

1. Install this APS skill into your repo at:
   - `.github/skills/agnostic-prompt-standard/`
   - OR `.claude/skills/agnostic-prompt-standard/`

## Claude Code file locations (summary)

Claude Code discovers these files:

### Memory (instructions)
- `./CLAUDE.md` — project-level memory (checked into repo)
- `./.claude/CLAUDE.md` — alternative project memory location
- `./.claude/rules/*.md` — path-scoped rules with glob patterns
- `./CLAUDE.local.md` — local overrides (gitignored)
- `~/.claude/CLAUDE.md` — user-level memory
- `~/.claude/rules/*.md` — user-level rules

### Settings
- `./.claude/settings.json` — project settings (checked into repo)
- `./.claude/settings.local.json` — local settings (gitignored)
- `~/.claude/settings.json` — user settings

### Custom subagents
- `./.claude/agents/*.md` — project-level subagents
- `~/.claude/agents/*.md` — user-level subagents (all projects)

### MCP servers
- `./.mcp.json` — MCP server configuration

See `manifest.json` for the full matrix.

## Memory hierarchy

Claude Code loads memory in this order (later overrides earlier):

1. **Enterprise** — managed by organization admins
2. **Project** — `./CLAUDE.md`, `./.claude/CLAUDE.md`
3. **Rules** — `./.claude/rules/*.md` (path-scoped)
4. **User** — `~/.claude/CLAUDE.md`, `./CLAUDE.local.md`

## @path imports

Claude Code supports importing file content using `@path` syntax:

```markdown
@README.md
@docs/architecture.md
@~/.claude/shared-rules.md
```

The referenced file content is injected into the memory context.

## Path-scoped rules

Rules in `.claude/rules/*.md` can be scoped to specific paths using frontmatter:

```yaml
---
paths:
  - "src/**/*.ts"
  - "src/**/*.tsx"
---
```

When a rule has `paths:` frontmatter, it only applies when working with files matching those globs.

## Hooks system

Claude Code supports hooks that execute shell commands at various lifecycle events:

| Hook | When it fires |
|------|---------------|
| PreToolUse | Before a tool executes |
| PostToolUse | After a tool executes |
| PermissionRequest | When permission is needed |
| Stop | When Claude stops |
| SubagentStop | When a subagent stops |
| UserPromptSubmit | When user submits a prompt |
| SessionStart | When a session begins |
| SessionEnd | When a session ends |
| PreCompact | Before context compaction |
| Notification | When a notification fires |

Configure hooks in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "echo 'About to run bash'"
      }
    ]
  }
}
```

## Permission rules

Control tool permissions in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(rm -rf *)"
    ],
    "ask": [
      "Write",
      "Edit"
    ]
  }
}
```

## Custom subagents

Claude Code supports custom subagents — specialized agents with their own instructions, tool permissions, and behaviors. Subagents are invoked via the `Task` tool when their description matches the user's request.

### Subagent file locations

| Location | Scope |
|----------|-------|
| `.claude/agents/*.md` | Project-level |
| `~/.claude/agents/*.md` | User-level (all projects) |
| `plugins/agents/` | Plugin-provided |
| `--agents` CLI flag | Session-only |

### Subagent frontmatter fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | String | Unique identifier (lowercase, hyphens) |
| `description` | Yes | String | Triggers when Claude recognizes this description |
| `model` | No | String | AI model: `sonnet`, `opus`, `haiku`, `inherit` (default: sonnet) |
| `tools` | No | Comma-separated | Allowed tools (allowlist) |
| `disallowedTools` | No | Comma-separated | Denied tools (denylist) |
| `permissionMode` | No | String | Permission handling mode |
| `skills` | No | Comma-separated | Skills to inject |
| `hooks` | No | Object | Lifecycle hooks (PreToolUse, PostToolUse, Stop) |

### Permission modes

| Mode | Description |
|------|-------------|
| `default` | Normal permission prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Minimal prompts |
| `bypassPermissions` | Skip all prompts (use with caution) |
| `plan` | Plan mode — research only, no edits |

### Subagent example

```yaml
---
name: code-reviewer
description: Expert code review specialist. Use after writing or modifying code.
model: inherit
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
permissionMode: default
---

You are a senior code reviewer ensuring high standards of code quality.

When invoked:
1. Run git diff to see recent changes
2. Review modified files for:
   - Code style consistency
   - Potential bugs
   - Performance issues
   - Security concerns
3. Provide actionable feedback
```

### Subagent hooks

Subagents can define their own hooks that only apply during subagent execution:

```yaml
---
name: safe-bash-runner
description: Run bash commands with validation
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
---
```

See `frontmatter/agent-frontmatter.md` for the full YAML template.

## Tools: built-in tools

Claude Code provides built-in tools directly by name (no qualification needed):

- `Read` — read file contents
- `Write` — create/overwrite files
- `Edit` — edit existing files
- `Bash` — execute shell commands
- `Glob` — find files by pattern
- `Grep` — search file contents
- `WebFetch` — fetch URL content
- `WebSearch` — web search
- `Task` — run subagents
- `TodoWrite` — manage task list
- `NotebookEdit` — edit Jupyter notebooks
- `AskUserQuestion` — ask user questions

### MCP tools

MCP tools use the pattern: `mcp__<server>__<tool>`

For example: `mcp__filesystem__read_file`

See `tools-registry.json` for the full tool catalog with risk levels.

## Differences from VS Code Copilot

| Aspect | VS Code Copilot | Claude Code |
|--------|-----------------|-------------|
| Instructions | `.github/copilot-instructions.md` | `CLAUDE.md`, `.claude/rules/*.md` |
| Agents | `.github/agents/*.agent.md` | `.claude/agents/*.md` |
| Prompts | `.github/prompts/*.prompt.md` | N/A (uses slash commands) |
| Skills | `.github/skills/<id>/SKILL.md` | N/A (uses MCP servers) |
| Settings | VS Code settings.json | `.claude/settings.json` |
| Tool syntax | `#tool` mentions, qualified names | Direct tool names |
| Extensions | MCP servers, extensions | MCP servers, hooks, plugins |
