```yaml
---
# description: Brief description shown as placeholder text in the chat input field.
description: Generate an implementation plan for new features or refactoring

# name: Name of the custom agent; defaults to the file name when unspecified.
name: Planner

# argument-hint: Optional hint that appears in the chat input to guide users on
# how to interact with the agent.
argument-hint: Describe the feature you want to plan

# tools: List of available tool or tool-set names (built-in tools, tool sets,
# MCP tools, or tools contributed by extensions). To include all tools from a
# specific MCP server, use `<server name>/*`.
# Note: If a specified tool is unavailable, it will be ignored.
tools:
  - fetch
  - githubRepo
  - search
  - usages

# model: Specifies the AI model used for prompts; if omitted, the currently
# selected model is used.
# Models currently available: "Claude Haiku 4.5 (copilot)"|"Claude Opus 4.5 (copilot)"|"Claude Sonnet 4 (copilot)"|"Claude Sonnet 4.5 (copilot)"|"Gemini 2.5 Pro (copilot)"|"Gemini 3 Flash (Preview) (copilot)"|"Gemini 3 Pro (Preview) (copilot)"|"GPT-4.1 (copilot)"
# Prefer "Claude Opus 4.5 (copilot)" or "Claude Sonnet 4 (copilot)" for best performance unless user specifies otherwise.
model: Claude Opus 4.5 (copilot)

# infer: Boolean flag (default true) to allow the custom agent to run as a subagent.
infer: true

# target: Target environment for the agent, either `vscode` or `github-copilot`.
target: vscode

# mcp-servers: Optional list of Model Context Protocol (MCP) server configuration
# JSON objects, used when the target is `github-copilot`.
mcp-servers: []

# handoffs: Optional list of suggested actions to transition between agents.
# Each handoff entry specifies:
#   - label: Text displayed on the handoff button.
#   - agent: Identifier of the target agent to switch to. Note that the name comes from the frontmatter `name` field of the target agent's file.
#   - prompt: Prompt text sent to the target agent.
#   - send: Optional boolean; when true, the prompt auto-submits (default false).
handoffs:
  - label: Implement Plan
    agent: implementation
    prompt: Implement the plan outlined above.
    send: false
---
```

## Field Requirements & Defaults

"Relevant fields" means: all **Required** fields, all **Recommended** fields with their default values, plus **Conditional** fields when their conditions are met.

**Field ordering:** Required → Recommended → Conditional (within each category, follow table order below).

| Field | Requirement | Default Value | Notes |
|-------|-------------|---------------|-------|
| `name` | Required | — | Must be provided; no default |
| `description` | Required | — | Must be provided; no default |
| `tools` | Recommended | `[]` | Empty array if no tools needed; YAML array syntax |
| `infer` | Recommended | `true` | Always include for subagents |
| `target` | Recommended | `vscode` | Include explicitly for clarity |
| `model` | Conditional | *(omit)* | Only include if specific model required; omit to use user's selected model |
| `argument-hint` | Conditional | *(omit)* | Only include if agent accepts user input |
| `mcp-servers` | Conditional | *(omit)* | Only include when `target: github-copilot` |
| `handoffs` | Conditional | *(omit)* | Only include if agent should suggest transitions to other agents |

## Tool Naming System

VS Code Copilot uses a **three-tier tool naming system**:

| Tier | Name | Usage | Example |
|------|------|-------|---------|
| **Tool Set** | Set name | Selects ALL tools in the set | `execute` |
| **Qualified Name** | `toolSet/camelCaseName` | Selects individual tool | `execute/runInTerminal` |
| **Function Name** | `snake_case_name` | Used by model at runtime | `run_in_terminal` |

### Using Tool Sets vs Individual Tools

**Include specific tools (recommended)** — use qualified names:
Default to individual (qualified) tool names to minimize injected tokens. Use toolset names only when ALL tools in the set are genuinely needed.
```yaml
tools:
  - execute/runInTerminal
  - execute/getTerminalOutput
  - search/codebase
```

**Include entire tool set** — use the set name:
Toolset names expand to every tool in the set, which increases injected tokens. Only use when the agent genuinely needs all tools in the set.
```yaml
tools:
  - execute    # Includes all: runInTerminal, getTerminalOutput, runTask, etc.
  - search     # Includes all: codebase, fileSearch, textSearch, etc.
```

**Mixed approach**:
```yaml
tools:
  - search              # All search tools
  - execute/runInTerminal  # Only terminal execution
  - read/readFile       # Only file reading
```

### Tool Sets Reference

| Tool Set | Description | Included Tools |
|----------|-------------|----------------|
| `search` | Search the workspace | `codebase`, `fileSearch`, `textSearch`, `searchResults`, `changes`, `usages` |
| `read` | Read workspace context | `readFile`, `problems`, `terminalLastCommand`, `terminalSelection` |
| `edit` | Edit and create files | `createDirectory`, `createFile`, `editFiles`, `editNotebook` |
| `execute` | Execute code and applications | `runInTerminal`, `getTerminalOutput`, `runTask`, `createAndRunTask`, `runTests`, `runNotebookCell`, `testFailure` |
| `web` | Fetch external information | `fetch`, `githubRepo` |
| `vscode` | VS Code IDE helpers | `runCommand`, `extensions`, `installExtension`, `getProjectSetupInfo`, `openSimpleBrowser`, `newWorkspace`, `vscodeAPI` |

### Standalone Tools (No Tool Set)

| Qualified Name | Function Name | Description |
|----------------|---------------|-------------|
| `selection` | `get_selection` | Get current editor selection |
| `todo` | `create_todo` | Track implementation with TODO list |

### Complete Tool Reference

| Tool Set | Qualified Name | Function Name | Description |
|----------|----------------|---------------|-------------|
| `search` | `search/codebase` | `codebase_search` | Search workspace for relevant context |
| `search` | `search/changes` | `get_changed_files` | List source control changes |
| `search` | `search/usages` | `find_usages` | Find references/implementations/definitions |
| `search` | `search/fileSearch` | `file_search` | Search for files using glob patterns |
| `search` | `search/textSearch` | `text_search` | Find text in files |
| `search` | `search/searchResults` | `get_search_results` | Read results from Search view |
| `read` | `read/readFile` | `read_file` | Read file content |
| `read` | `read/problems` | `get_errors` | Get workspace issues from Problems panel |
| `read` | `read/terminalLastCommand` | `get_terminal_last_command` | Get last terminal command output |
| `read` | `read/terminalSelection` | `get_terminal_selection` | Get terminal selection |
| `edit` | `edit/createDirectory` | `create_directory` | Create directory |
| `edit` | `edit/createFile` | `create_file` | Create file |
| `edit` | `edit/editFiles` | `edit_file` | Apply edits to files |
| `edit` | `edit/editNotebook` | `edit_notebook` | Edit notebook |
| `execute` | `execute/runInTerminal` | `run_in_terminal` | Run shell command |
| `execute` | `execute/getTerminalOutput` | `get_terminal_output` | Get terminal output |
| `execute` | `execute/runTask` | `run_task` | Run VS Code task |
| `execute` | `execute/createAndRunTask` | `create_and_run_task` | Create and run task |
| `execute` | `execute/runTests` | `run_tests` | Run tests |
| `execute` | `execute/runNotebookCell` | `run_notebook_cell` | Run notebook cell |
| `execute` | `execute/testFailure` | `test_failure` | Get test failure info |
| `web` | `web/fetch` | `fetch` | Fetch web page content |
| `web` | `web/githubRepo` | `github_repo` | Search GitHub repository |
| `vscode` | `vscode/runCommand` | `run_vscode_command` | Run VS Code command |
| `vscode` | `vscode/extensions` | `get_extensions` | Search extensions |
| `vscode` | `vscode/installExtension` | `install_extension` | Install extension |
| `vscode` | `vscode/getProjectSetupInfo` | `get_project_setup_info` | Get project scaffolding info |
| `vscode` | `vscode/openSimpleBrowser` | `open_simple_browser` | Open Simple Browser |
| `vscode` | `vscode/newWorkspace` | `new_workspace` | Create workspace |
| `vscode` | `vscode/vscodeAPI` | `vscode_api` | VS Code API help |
| — | `selection` | `get_selection` | Get editor selection |
| — | `todo` | `create_todo` | Track TODOs |

## Syntax Rules

- Tools use **YAML array** syntax (not comma-separated strings)
- Generated frontmatter MUST NOT contain YAML comments
- Description MUST be a single-line quoted string (avoid YAML block scalars like `description: >`)
- If a specified tool is unavailable, it will be ignored
- To include all tools from a specific MCP server, use `<server name>/*`

## Examples

### Minimal Agent
```yaml
---
name: my-agent
description: "Brief description of what this agent does."
tools: []
infer: true
target: vscode
---
```

### Agent with Tool Sets
```yaml
---
name: code-implementer
description: "Implements features with full access to search, read, edit, and execute."
tools:
  - search
  - read
  - edit
  - execute
infer: true
target: vscode
---
```

### Agent with Specific Tools
```yaml
---
name: code-reviewer
description: "Reviews code changes and suggests improvements."
tools:
  - search/codebase
  - search/changes
  - read/readFile
  - read/problems
infer: true
target: vscode
---
```

### Agent with Mixed Tool Selection
```yaml
---
name: test-runner
description: "Runs and monitors tests."
tools:
  - search
  - read/readFile
  - read/problems
  - execute/runTests
  - execute/runInTerminal
  - execute/getTerminalOutput
infer: true
target: vscode
---
```

### Agent with Handoffs
```yaml
---
name: planner
description: "Creates detailed implementation plans."
tools:
  - search
  - read
  - todo
infer: true
target: vscode
handoffs:
  - label: Implement Plan
    agent: implementer
    prompt: Implement the plan outlined above.
    send: false
---
```

## Notes

- If you see "Unexpected indentation" diagnostics, keep `description` as a **single-line** string
- The function name (snake_case) is what the model actually calls at runtime — you don't need to specify it
- Chat mentions use `#` prefix (e.g., `#codebase`, `#problems`)
