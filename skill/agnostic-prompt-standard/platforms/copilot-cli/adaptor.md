<instructions>
Generate artifacts for the standalone GitHub Copilot CLI (`copilot` binary) using the constants and format contracts in this adapter.
This adapter targets the standalone CLI, not the VS Code extension; use the `vscode-copilot` adapter for the editor surface.
Tool names use snake_case with optional paren-arg specifiers (e.g., `shell(git commit)`, `shell(git:*)`, `web_fetch`).
Built-in tools are `shell`, `read`, `write`, and `web_fetch`; MCP tools follow the pattern `<ServerName>(<tool_name>)`.
Project agents live in `.github/agents/*.agent.md`; personal agents live in `~/.copilot/agents/*.agent.md`.
When an agent name collides between project and personal scopes, the personal (home directory) agent wins.
Project skills live in any of `.github/skills/`, `.claude/skills/`, or `.agents/skills/`; personal skills live in any of `~/.copilot/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`.
Project instructions live in `.github/copilot-instructions.md`; personal instructions live in `~/.copilot/copilot-instructions.md`.
Scoped instructions live in `.github/instructions/*.instructions.md` and apply to files matching their `applyTo` glob.
Hooks are first-class lifecycle scripts configured in `hooks.json` (cwd) or `.github/hooks/hooks.json` (repo).
MCP servers are configured in `~/.copilot/mcp-config.json` (personal), `.mcp.json`, `.github/mcp.json`, or `.vscode/mcp.json` (project, in precedence order).
Tool permissions are persisted in `~/.copilot/permissions-config.json` and can be set per-session via `--allow-tool` and `--deny-tool`.
Deny rules always override allow rules in the permissions resolver.
The configuration directory defaults to `~/.copilot` and can be relocated by setting `COPILOT_HOME` or passing `--config-dir`.
Subagents are spawned via the `/fleet [PROMPT]` slash command (interactive REPL) or the `--autopilot` flag (non-interactive).
You MUST load `guides/subagent-architecture-v1.0.0.guide.md` before authoring orchestrator or worker agents.
You MUST treat `.agent.md` workers as leaf workers because the docs do not document nested `/fleet` delegation; we apply `depth-1-only` for portability.
You MUST map worker APS `<input>` fields to caller dispatch process args one-for-one.
Generated frontmatter MUST NOT contain YAML comments.
Description fields MUST be a single-line quoted string (avoid YAML block scalars).
Skills installed under `.claude/skills/` or `~/.claude/skills/` by `aps init --platform claude-code` are automatically discoverable by the Copilot CLI per official docs; cross-platform skill reuse is supported with no extra wiring.
</instructions>

<constants>
PLATFORM_ID: "copilot-cli"
DISPLAY_NAME: "GitHub Copilot CLI"
ADAPTER_VERSION: "1.0.0"
LAST_UPDATED: "2026-04-08"

ARTIFACT_TYPES: CSV<<
type,scope,file_pattern,frontmatter_format
agent,project,.github/agents/*.agent.md,COPILOT_CLI_AGENT_FRONTMATTER_V1
agent,personal,~/.copilot/agents/*.agent.md,COPILOT_CLI_AGENT_FRONTMATTER_V1
skill,project,.github/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,project,.claude/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,project,.agents/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,personal,~/.copilot/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,personal,~/.claude/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,personal,~/.agents/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
instructions,project,.github/copilot-instructions.md,
instructions,personal,~/.copilot/copilot-instructions.md,
scoped-instructions,project,.github/instructions/*.instructions.md,COPILOT_CLI_INSTRUCTIONS_FRONTMATTER_V1
hooks,project,.github/hooks/hooks.json,COPILOT_CLI_HOOKS_CONFIG_V1
hooks,project,hooks.json,COPILOT_CLI_HOOKS_CONFIG_V1
mcp-config,personal,~/.copilot/mcp-config.json,COPILOT_CLI_MCP_CONFIG_V1
mcp-config,project,.github/mcp.json,COPILOT_CLI_MCP_CONFIG_V1
mcp-config,project,.mcp.json,COPILOT_CLI_MCP_CONFIG_V1
permissions,personal,~/.copilot/permissions-config.json,COPILOT_CLI_PERMISSIONS_V1
config,personal,~/.copilot/config.json,COPILOT_CLI_CONFIG_V1
>>

SUBAGENT_AUTHORING_GUIDE: "guides/subagent-architecture-v1.0.0.guide.md"

SUBAGENT_ARCHITECTURE: JSON<<
{
  "coordinator_role": "Main copilot session (interactive REPL or non-interactive `copilot -p \"...\"` invocation)",
  "worker_role": "Custom .agent.md agent invoked via the /fleet slash command",
  "depth_policy": "depth-1-only",
  "documented_limit": "Nested /fleet delegation is not documented; the orchestrator decides feasibility per task. APS treats this as depth-1 for portability.",
  "invocation_surface": "/fleet [PROMPT] slash command (interactive) or --autopilot flag (non-interactive)",
  "definition_paths": [".github/agents/*.agent.md", "~/.copilot/agents/*.agent.md"],
  "name_collision_rule": "When the same agent name exists in both project and personal scopes, the personal (~/.copilot/agents/) version wins.",
  "default_inheritance": {
    "model": "inherits the orchestrator session model unless overridden",
    "tools": "inherits the orchestrator allow/deny set unless restricted via allowed-tools"
  },
  "controls": {
    "tool_allowlist": "allowed-tools",
    "permission_gate": "permissions-config.json + --allow-tool / --deny-tool",
    "hook_gate": "preToolUse hooks can deny a tool invocation by exiting non-zero"
  },
  "request_contract_rule": "Define the worker <input> as the public request interface and mirror it in the caller dispatch process args.",
  "response_contract_rule": "The worker returns a typed result or bounded summary that the orchestrator captures before continuing.",
  "portability_rule": "Author Copilot CLI workers as leaf workers. Keep host-specific /fleet routing in the caller dispatch layer."
}
>>

INSTRUCTION_FILE_PATHS: [".github/copilot-instructions.md", "~/.copilot/copilot-instructions.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"]
AGENT_FILE_PATHS: [".github/agents/*.agent.md", "~/.copilot/agents/*.agent.md"]
SKILL_FILE_PATHS: [".github/skills", ".claude/skills", ".agents/skills", "~/.copilot/skills", "~/.claude/skills", "~/.agents/skills"]
MCP_CONFIG_PATHS: ["~/.copilot/mcp-config.json", ".github/mcp.json", ".mcp.json", ".vscode/mcp.json"]
HOOK_CONFIG_PATHS: [".github/hooks/hooks.json", "hooks.json"]
PERMISSIONS_CONFIG_PATHS: ["~/.copilot/permissions-config.json"]

DETECTION_MARKERS: [".github/copilot-instructions.md", ".github/agents", ".github/skills", ".github/hooks", ".github/instructions", ".github/mcp.json", "~/.copilot/config.json", "~/.copilot/copilot-instructions.md"]

CONFIG_HOME_ENV: "COPILOT_HOME"
CONFIG_HOME_DEFAULT: "~/.copilot"
CONFIG_DIR_FLAG: "--config-dir"

TOOL_NAMING_STYLE: "snake_case with optional paren-arg specifiers (e.g., shell(git commit), shell(git:*), web_fetch)"
TOOL_NAMING_QUALIFICATION: "paren-arg for command-scoped or wildcard restrictions"
TOOL_BUILT_IN: ["shell", "read", "write", "web_fetch"]
TOOL_MCP_PATTERN: "<ServerName>(<tool_name>)"
TOOL_PERMISSION_PRECEDENCE: "deny overrides allow"

TOOLS: CSV<<
name,toolset,risk,side_effects,description,permission_examples
shell,builtin,high,executes,"Execute shell commands. Supports per-command scoping and wildcards.","[shell, shell(git commit), shell(git:*), shell(npm test)]"
read,builtin,low,reads,"Read file contents from the workspace.","[read, read(src/**)]"
write,builtin,medium,writes,"Create or overwrite files in the workspace.","[write, write(src/**)]"
web_fetch,builtin,medium,network,"Fetch and process URL content.","[web_fetch]"
>>

SUBAGENT_INVOCATION_COMMANDS: ["/fleet", "--autopilot"]
SLASH_COMMANDS: ["/fleet", "/help", "/login", "/logout", "/model", "/skills", "/agents", "/quit"]

HOOK_EVENTS: ["sessionStart", "sessionEnd", "userPromptSubmitted", "preToolUse", "postToolUse", "errorOccurred"]
HOOK_PLATFORMS: ["bash", "powershell"]
HOOK_DENY_RULE: "preToolUse hooks can deny a tool invocation by exiting with a non-zero status."

INSTALLATION_METHODS: ["npm install -g @github/copilot", "brew install copilot-cli", "winget install GitHub.Copilot", "curl -fsSL https://gh.io/copilot-install | bash"]

AGENT_VERSIONING: JSON<<
{
  "templates": [
    {
      "path": "templates/.github/agents/aps-v{major}.{minor}.{patch}.agent.md",
      "current_path": "templates/.github/agents/aps-v1.2.1.agent.md",
      "frontmatter": {
        "name_pattern": "APS v{major}.{minor}.{patch} Agent",
        "description_pattern": "Generate APS v{major}.{minor}.{patch} .agent.md files for the Copilot CLI: detect artifact type from user intent, load APS+Copilot CLI adapter, extract intent, then generate+write+lint."
      }
    }
  ]
}
>>

SKILL_AUTHORING_RESOURCES: JSON<<
{
  "guide": "guides/skill-authoring-v1.0.0.guide.md",
  "template": "_template/",
  "build_process": "processes/build-skill.md"
}
>>

CROSS_PLATFORM_INTEROP: JSON<<
{
  "shared_skill_paths": [".claude/skills", "~/.claude/skills", ".agents/skills", "~/.agents/skills"],
  "rationale": "Per docs.github.com, the Copilot CLI also reads .claude/skills, ~/.claude/skills, .agents/skills, and ~/.agents/skills. Skills installed via `aps init --platform claude-code` are therefore automatically discoverable by the Copilot CLI without re-running init.",
  "shared_agent_paths": [],
  "shared_instruction_paths": ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]
}
>>

DOCS_HOME_URL: "https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli"
DOCS_AGENTS_URL: "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli"
DOCS_SKILLS_URL: "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills"
DOCS_INSTRUCTIONS_URL: "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions"
DOCS_HOOKS_URL: "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks"
DOCS_MCP_URL: "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers"
DOCS_TOOLS_URL: "https://docs.github.com/en/copilot/how-tos/copilot-cli/allowing-tools"
DOCS_FLEET_URL: "https://docs.github.com/en/copilot/concepts/agents/copilot-cli/fleet"
DOCS_CONFIG_DIR_URL: "https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference"
</constants>

<formats>
<format id="COPILOT_CLI_AGENT_FRONTMATTER_V1" name="Copilot CLI Agent Frontmatter" purpose="YAML frontmatter contract for .github/agents/*.agent.md and ~/.copilot/agents/*.agent.md custom agent files.">
---
name: <AGENT_NAME>
description: "<AGENT_DESCRIPTION>"
model: <MODEL>
allowed-tools: <ALLOWED_TOOLS_ARRAY>
mcp-servers: <MCP_SERVERS_ARRAY>
---

WHERE:
- <AGENT_NAME> is String; lowercase-hyphenated agent identifier; the markdown filename minus the `.agent.md` suffix is used when omitted.
- <AGENT_DESCRIPTION> is String; single-line double-quoted description shown when the agent is listed or invoked.
- <MODEL> is String; optional model id; omit to inherit the orchestrator session model.
- <ALLOWED_TOOLS_ARRAY> is YAML array of snake_case tool names or paren-arg patterns from TOOLS (e.g., `shell(git:*)`, `read`, `write`, `web_fetch`); omit to inherit the orchestrator allow set.
- <MCP_SERVERS_ARRAY> is YAML array of MCP server ids that the agent may use; omit to inherit the session set.
</format>

<format id="COPILOT_CLI_SKILL_FRONTMATTER_V1" name="Copilot CLI Skill Frontmatter" purpose="YAML frontmatter contract for SKILL.md files under .github/skills/, .claude/skills/, .agents/skills/, ~/.copilot/skills/, ~/.claude/skills/, or ~/.agents/skills/.">
---
name: <SKILL_NAME>
description: "<SKILL_DESCRIPTION>"
license: <LICENSE>
allowed-tools: <ALLOWED_TOOLS_ARRAY>
---

WHERE:
- <SKILL_NAME> is String; lowercase hyphenated skill identifier such as `agnostic-prompt-standard`.
- <SKILL_DESCRIPTION> is String; single-line double-quoted description so the CLI can auto-load the skill when relevant.
- <LICENSE> is String; optional SPDX license id (e.g., `MIT`, `Apache-2.0`).
- <ALLOWED_TOOLS_ARRAY> is YAML array of snake_case tool names or paren-arg patterns; omit to inherit the session allow set.
</format>

<format id="COPILOT_CLI_INSTRUCTIONS_FRONTMATTER_V1" name="Copilot CLI Instructions Frontmatter" purpose="YAML frontmatter contract for .github/instructions/*.instructions.md path-scoped instructions.">
---
applyTo: "<GLOB_PATTERN>"
description: "<INSTRUCTIONS_DESCRIPTION>"
---

WHERE:
- <GLOB_PATTERN> is String; comma-separated glob patterns such as `**/*.ts,**/*.tsx`.
- <INSTRUCTIONS_DESCRIPTION> is String; single-line double-quoted description of the conventions captured in this file.
</format>

<format id="COPILOT_CLI_HOOKS_CONFIG_V1" name="Copilot CLI Hooks Config" purpose="JSON structure for hooks.json (cwd) or .github/hooks/hooks.json (repo).">
{
  "<HOOK_EVENT>": [
    {
      "matcher": "<MATCHER_PATTERN>",
      "bash": "<BASH_COMMAND>",
      "powershell": "<POWERSHELL_COMMAND>",
      "cwd": "<CWD_PATH>",
      "timeoutSec": <TIMEOUT_SEC>,
      "env": {
        "<ENV_KEY>": "<ENV_VALUE>"
      }
    }
  ]
}

WHERE:
- <HOOK_EVENT> is one of HOOK_EVENTS.
- <MATCHER_PATTERN> is String; tool name or paren-arg pattern to match (e.g., `shell(git commit)`); omit for unconditional hooks.
- <BASH_COMMAND> is String; shell command to execute on POSIX systems.
- <POWERSHELL_COMMAND> is String; shell command to execute on Windows systems.
- <CWD_PATH> is String; optional working directory for the hook command.
- <TIMEOUT_SEC> is Integer; optional timeout in seconds before the hook is killed.
- <ENV_KEY> and <ENV_VALUE> are Strings; optional environment variables passed to the hook process.
- A `preToolUse` hook that exits non-zero denies the matching tool invocation.
</format>

<format id="COPILOT_CLI_MCP_CONFIG_V1" name="Copilot CLI MCP Config" purpose="JSON structure for ~/.copilot/mcp-config.json, .mcp.json, .github/mcp.json, or .vscode/mcp.json.">
{
  "mcpServers": {
    "<SERVER_NAME>": {
      "type": "<SERVER_TYPE>",
      "command": "<COMMAND>",
      "args": ["<ARG>"],
      "url": "<URL>",
      "headers": {
        "<HEADER_KEY>": "<HEADER_VALUE>"
      },
      "env": {
        "<ENV_KEY>": "<ENV_VALUE>"
      },
      "tools": ["<TOOL_NAME>"]
    }
  }
}

WHERE:
- <SERVER_NAME> is String; unique server id used in `<ServerName>(<tool_name>)` tool references.
- <SERVER_TYPE> is one of `local`, `stdio`, `http`, `sse`.
- <COMMAND> is String; executable for `local` or `stdio` servers; omit for `http`/`sse`.
- <ARG> is String; command-line argument for `local`/`stdio` servers.
- <URL> is String; endpoint URL for `http` or `sse` servers; omit for `local`/`stdio`.
- <HEADER_KEY>/<HEADER_VALUE> are Strings; optional HTTP headers for `http`/`sse` servers.
- <ENV_KEY>/<ENV_VALUE> are Strings; optional environment variables for `local`/`stdio` servers.
- <TOOL_NAME> is String; optional allowlist of tool names exposed by the server; omit to expose all advertised tools.
- The built-in GitHub MCP server is enabled by default; disable it with the `--disable-builtin-mcps` flag.
</format>

<format id="COPILOT_CLI_PERMISSIONS_V1" name="Copilot CLI Permissions Config" purpose="JSON structure for ~/.copilot/permissions-config.json.">
{
  "allow": ["<TOOL_PATTERN>"],
  "deny": ["<TOOL_PATTERN>"]
}

WHERE:
- <TOOL_PATTERN> is String; snake_case tool name or paren-arg pattern (e.g., `shell`, `shell(git:*)`, `web_fetch`, `<ServerName>(<tool_name>)`).
- Deny rules always override allow rules.
- Patterns added at runtime via `--allow-tool` and `--deny-tool` are merged into this file.
</format>

<format id="COPILOT_CLI_CONFIG_V1" name="Copilot CLI Config" purpose="JSON structure for ~/.copilot/config.json.">
{
  "model": "<MODEL>",
  "theme": "<THEME>",
  "trusted_folders": ["<FOLDER_PATH>"],
  "telemetry": <TELEMETRY>
}

WHERE:
- <MODEL> is String; default model id used when no per-session override is supplied.
- <THEME> is String; UI theme id (e.g., `dark`, `light`).
- <FOLDER_PATH> is String; absolute path to a folder the user has marked as trusted.
- <TELEMETRY> is Boolean; whether anonymized telemetry is enabled.
</format>
</formats>
