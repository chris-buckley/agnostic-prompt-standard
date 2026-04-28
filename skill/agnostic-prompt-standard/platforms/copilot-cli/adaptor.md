<instructions>
Generate artifacts for the standalone GitHub Copilot CLI (`copilot` binary) using the constants and format contracts in this adapter.
This adapter targets the standalone CLI, not the VS Code extension; use the `vscode-copilot` adapter for the editor surface.
Copilot CLI uses TWO distinct grammars: tool names (used inside agent `tools:` arrays) and permission patterns (used by `--allow-tool`, `--deny-tool`, and `permissions-config.json`).
Tool names are bare snake_case identifiers from TOOL_BUILT_IN, plus `<server>/<tool>` slash notation for MCP tools (e.g., `bash`, `view`, `web_fetch`, `github-mcp-server/get_pull_request`).
Permission patterns use `kind(arg?)` form where kind is one of `shell`, `write`, `url`, or an MCP server name (e.g., `shell(git:*)`, `write`, `url(https://*.github.com)`, `github-mcp-server(get_pull_request)`).
The `shell(<command>:*)` form scopes a permission to a command family by stem prefix; `shell(git:*)` matches `git push` but not `gitea`.
The `write` permission category covers the `create` and `edit` tools but does NOT include shell redirections; use `--allow-all-tools` to allow shell redirections.
Deny rules always override allow rules in the permissions resolver, even `--allow-all-tools`.
Custom agents are stored in TWO supported formats: `.agent.yaml` (native, used by bundled Copilot CLI agents) and `.agent.md` (VSCode-format compatibility, parsed since the v1.0.x release per the changelog).
Native `.agent.yaml` files have the schema declared in COPILOT_CLI_AGENT_YAML_V1; VSCode-format `.agent.md` files have the schema declared in COPILOT_CLI_AGENT_MD_V1.
Project agents live in `.github/agents/`; personal agents live in `~/.copilot/agents/`.
When an agent name collides between project and personal scopes, the personal (home directory) agent wins.
Project skills live in any of `.github/skills/`, `.claude/skills/`, or `.agents/skills/`; personal skills live in any of `~/.copilot/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`.
Project instructions live in `.github/copilot-instructions.md`; personal instructions live in `~/.copilot/copilot-instructions.md`; the loader also reads `AGENTS.md` and related custom-instructions files.
Additional custom-instructions search directories can be added via the `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` environment variable.
Scoped instructions live in `.github/instructions/*.instructions.md` and apply to files matching their `applyTo` glob.
Lifecycle hooks are first-class and configured in `hooks.json` (cwd) or `hooks/hooks.json` (subdirectory variant); the loader also walks the project tree for these literal paths.
The hook event vocabulary in HOOK_EVENTS is deliberately Claude-Code-compatible per the SDK comment "Matches Claude Code terminology; extensible for future stop reasons."
A `preToolUse` hook that exits non-zero (or returns `decision: "block"` from the SDK) denies the matching tool invocation.
MCP servers are configured in `~/.copilot/mcp-config.json` (personal); per-session additions are passed via `--additional-mcp-config <json|@file>`.
The built-in MCP server is `github-mcp-server`; disable it with `--disable-builtin-mcps` or scope its tools with `--add-github-mcp-tool` and `--add-github-mcp-toolset`.
Tool permissions are persisted in `~/.copilot/permissions-config.json` and can be set per-session via `--allow-tool` and `--deny-tool`.
File access is restricted to the cwd and the system temp directory by default; expand with `--add-dir`, disable verification with `--allow-all-paths`, or block temp access with `--disallow-temp-dir`.
URL access is gated by `--allow-url` / `--deny-url` and the `allowed_urls` / `denied_urls` config keys; all URL patterns are protocol-aware.
The configuration directory defaults to `~/.copilot` and can be relocated by setting the `COPILOT_HOME` environment variable or passing `--config-dir <directory>`.
Subagents have multiple invocation surfaces: the built-in `task` tool (programmatic, used inside agent `tools:` arrays), the `/fleet` slash command (interactive REPL — enables fleet mode for parallel subagent execution), the `--agent <agent>` flag (selects the active agent for a session), and `--autopilot` (non-interactive continuation mode).
You MUST load `guides/subagent-architecture-v1.0.0.guide.md` before authoring orchestrator or worker agents.
You MUST treat custom workers as leaf workers because nested `/fleet` delegation is not documented; we apply `depth-1-only` for portability.
You MUST map worker APS `<input>` fields to caller dispatch process args one-for-one.
Generated frontmatter MUST NOT contain YAML comments.
Description fields MUST be a single-line quoted string (avoid YAML block scalars) when authoring `.agent.md` (VSCode-format) files; native `.agent.yaml` files MAY use YAML block scalars for `description` and `prompt`.
Skills installed under `.claude/skills/` or `~/.claude/skills/` by `aps init --platform claude-code` are automatically discoverable by the Copilot CLI per official docs; cross-platform skill reuse is supported with no extra wiring.
The Copilot CLI ships a built-in `fetch_copilot_cli_documentation` tool that the model can use to self-introspect against current GitHub docs; APS authors MAY rely on this tool when authoring agents that target Copilot CLI.
You MUST NOT use the `read` or `write` strings as tool names in agent `tools:` arrays — those are permission categories. Use `view` (read), `create` (new file), and `edit` (modify file) as tool names instead.
</instructions>

<constants>
PLATFORM_ID: "copilot-cli"
DISPLAY_NAME: "GitHub Copilot CLI"
ADAPTER_VERSION: "1.1.0"
LAST_UPDATED: "2026-04-08"
VERIFIED_AGAINST_BINARY_VERSION: "1.0.3"

ARTIFACT_TYPES: CSV<<
type,scope,file_pattern,frontmatter_format
agent,project,.github/agents/*.agent.yaml,COPILOT_CLI_AGENT_YAML_V1
agent,project,.github/agents/*.agent.md,COPILOT_CLI_AGENT_MD_V1
agent,personal,~/.copilot/agents/*.agent.yaml,COPILOT_CLI_AGENT_YAML_V1
agent,personal,~/.copilot/agents/*.agent.md,COPILOT_CLI_AGENT_MD_V1
skill,project,.github/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,project,.claude/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,project,.agents/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,personal,~/.copilot/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,personal,~/.claude/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
skill,personal,~/.agents/skills/<skill-id>/SKILL.md,COPILOT_CLI_SKILL_FRONTMATTER_V1
instructions,project,.github/copilot-instructions.md,
instructions,project,AGENTS.md,
instructions,personal,~/.copilot/copilot-instructions.md,
scoped-instructions,project,.github/instructions/*.instructions.md,COPILOT_CLI_INSTRUCTIONS_FRONTMATTER_V1
hooks,project,hooks.json,COPILOT_CLI_HOOKS_CONFIG_V1
hooks,project,hooks/hooks.json,COPILOT_CLI_HOOKS_CONFIG_V1
mcp-config,personal,~/.copilot/mcp-config.json,COPILOT_CLI_MCP_CONFIG_V1
permissions,personal,~/.copilot/permissions-config.json,COPILOT_CLI_PERMISSIONS_V1
config,personal,~/.copilot/config.json,COPILOT_CLI_CONFIG_V1
plugin-registry,personal,~/.copilot/installed-plugins/,
>>

SUBAGENT_AUTHORING_GUIDE: "guides/subagent-architecture-v1.0.0.guide.md"

SUBAGENT_ARCHITECTURE: JSON<<
{
  "coordinator_role": "Main copilot session (interactive REPL or non-interactive `copilot -p \"...\"` invocation)",
  "worker_role": "Custom .agent.yaml or .agent.md agent invoked via the task tool, /fleet slash command, or --agent flag",
  "depth_policy": "depth-1-only",
  "documented_limit": "Nested /fleet delegation is not documented. APS treats this as depth-1 for portability.",
  "invocation_surfaces": [
    {
      "name": "task tool",
      "kind": "built-in tool",
      "where": "Listed inside an agent `tools:` array; called programmatically by the model.",
      "context_isolation": "Runs in a separate context window per invocation."
    },
    {
      "name": "/fleet",
      "kind": "interactive slash command",
      "where": "Typed in the REPL after starting `copilot`.",
      "semantics": "Enables fleet mode for parallel subagent execution; persists for the rest of the session."
    },
    {
      "name": "--agent <agent>",
      "kind": "CLI flag",
      "where": "Passed to `copilot` at startup.",
      "semantics": "Selects the active agent for the session; the named agent must exist in `.github/agents/` or `~/.copilot/agents/` (or be a bundled agent like task/explore/code-review/research)."
    },
    {
      "name": "--autopilot",
      "kind": "CLI flag",
      "where": "Used with -p/--prompt for non-interactive execution.",
      "semantics": "Enables autopilot continuation mode; capped by --max-autopilot-continues."
    }
  ],
  "definition_paths": [".github/agents/*.agent.yaml", ".github/agents/*.agent.md", "~/.copilot/agents/*.agent.yaml", "~/.copilot/agents/*.agent.md"],
  "name_collision_rule": "When the same agent name exists in both project and personal scopes, the personal (~/.copilot/agents/) version wins.",
  "default_inheritance": {
    "model": "inherits the orchestrator session model unless the agent declares `model:`",
    "tools": "inherits the orchestrator allow/deny set unless restricted via the agent's `tools:` array or runtime --available-tools/--excluded-tools filters"
  },
  "controls": {
    "tool_filter": "--available-tools (whitelist) and --excluded-tools (blacklist) decide which tools the model can see",
    "permission_gate": "permissions-config.json + --allow-tool / --deny-tool control approval prompts (do NOT expose tools that the filter hides)",
    "hook_gate": "preToolUse hooks can deny a tool invocation by exiting non-zero or returning {decision: 'block'}"
  },
  "bundled_workers": [
    {"name": "task", "model": "claude-haiku-4.5", "purpose": "Execute development commands (tests, builds, lints, formatters); brief on success, verbose on failure."},
    {"name": "explore", "model": "claude-haiku-4.5", "purpose": "Fast codebase exploration via grep/glob/view/bash/lsp + read-only github-mcp-server + bluebird semantic search."},
    {"name": "code-review", "model": "claude-sonnet-4.5", "purpose": "High-signal code review of staged/unstaged or branch diffs; only surfaces real bugs."},
    {"name": "research", "model": "claude-sonnet-4.6", "purpose": "Exhaustive research using github MCP, web_search, web_fetch, and the task subagent."}
  ],
  "request_contract_rule": "Define the worker `tools:` array as the public capability surface and mirror it in the caller dispatch process args.",
  "response_contract_rule": "Workers return a typed result or bounded summary that the orchestrator captures before continuing.",
  "portability_rule": "Author Copilot CLI workers as leaf workers. Keep host-specific /fleet routing and --autopilot wiring in the caller dispatch layer."
}
>>

INSTRUCTION_FILE_PATHS: [".github/copilot-instructions.md", "~/.copilot/copilot-instructions.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"]
INSTRUCTION_OVERRIDE_ENV: "COPILOT_CUSTOM_INSTRUCTIONS_DIRS"
AGENT_FILE_PATHS: [".github/agents/*.agent.yaml", ".github/agents/*.agent.md", "~/.copilot/agents/*.agent.yaml", "~/.copilot/agents/*.agent.md"]
SKILL_FILE_PATHS: [".github/skills", ".claude/skills", ".agents/skills", "~/.copilot/skills", "~/.claude/skills", "~/.agents/skills"]
MCP_CONFIG_PATHS: ["~/.copilot/mcp-config.json"]
MCP_CONFIG_RUNTIME_FLAG: "--additional-mcp-config <json|@file>"
HOOK_CONFIG_PATHS: ["hooks.json", "hooks/hooks.json"]
PERMISSIONS_CONFIG_PATHS: ["~/.copilot/permissions-config.json"]
PLUGIN_INSTALL_DIR: "~/.copilot/installed-plugins/"
PLUGIN_RUNTIME_FLAG: "--plugin-dir <directory>"

DETECTION_MARKERS: [".github/copilot-instructions.md", ".github/agents", ".github/skills", ".github/instructions", "~/.copilot/config.json", "~/.copilot/copilot-instructions.md", "~/.copilot/agents", "hooks.json"]

CONFIG_HOME_ENV: "COPILOT_HOME"
CONFIG_HOME_DEFAULT: "~/.copilot"
CONFIG_DIR_FLAG: "--config-dir"

ENV_VARS: CSV<<
name,purpose,default
COPILOT_HOME,Override the directory where configuration and state files are stored,$HOME/.copilot
COPILOT_ALLOW_ALL,Allow all tools to run automatically without confirmation when set to "true",unset
COPILOT_AUTO_UPDATE,Set to "false" to disable automatic CLI updates (auto-disabled in CI environments),true
COPILOT_CUSTOM_INSTRUCTIONS_DIRS,Comma-separated additional directories to search for custom instructions files,unset
COPILOT_EDITOR,Command used to interactively edit a file (e.g., the plan); falls back to VISUAL then EDITOR,unset
COPILOT_GITHUB_TOKEN,Authentication token override; falls back to GH_TOKEN then GITHUB_TOKEN,unset
COPILOT_MODEL,Default agent model; overridden by --model flag and /model command,unset
GH_HOST,GitHub hostname for GHEC data residency (e.g., mycompany.ghe.com),github.com
USE_BUILTIN_RIPGREP,Set to "false" to use the system ripgrep binary instead of the bundled version,true
NO_COLOR,Disable color output when set to any value,unset
PLAIN_DIFF,Disable rich diff rendering when set to "true",unset
HTTP_PROXY,Proxy server for HTTP connections,unset
HTTPS_PROXY,Proxy server for HTTPS connections,unset
NO_PROXY,Comma-separated hosts that bypass the proxy,unset
>>

TOOL_NAMING_STYLE: "Two distinct grammars. Tool names (in agent `tools:` arrays) are bare snake_case ids plus `<server>/<tool>` slash notation for MCP tools. Permission patterns (in --allow-tool/--deny-tool and permissions-config.json) use `kind(arg?)` form."
TOOL_NAMING_QUALIFICATION: "Tool names: bare or `<server>/<tool>`. Permission patterns: `kind(arg?)`."

TOOL_BUILT_IN: ["bash", "read_bash", "stop_bash", "powershell", "read_powershell", "stop_powershell", "list_powershell", "view", "create", "edit", "grep", "glob", "lsp", "web_fetch", "web_search", "fetch_copilot_cli_documentation", "task", "read_agent", "list_agents", "skill", "report_intent", "sql", "ask_user"]

TOOL_BUILT_IN_BY_CATEGORY: JSON<<
{
  "shell_posix": ["bash", "read_bash", "stop_bash"],
  "shell_windows": ["powershell", "read_powershell", "stop_powershell", "list_powershell"],
  "filesystem": ["view", "create", "edit"],
  "search": ["grep", "glob"],
  "code_intelligence": ["lsp"],
  "web": ["web_fetch", "web_search", "fetch_copilot_cli_documentation"],
  "subagent": ["task", "read_agent", "list_agents"],
  "skills": ["skill"],
  "interaction": ["ask_user", "report_intent"],
  "data": ["sql"]
}
>>

TOOL_MCP_PATTERN_TOOLS_ARRAY: "<server>/<tool>"
TOOL_MCP_PATTERN_PERMISSIONS: "<server>(<tool>?)"
TOOL_PERMISSION_KINDS: ["shell(<command>:*?)", "write", "url(<domain-or-url>?)", "<mcp-server-name>(<tool-name>?)"]
TOOL_PERMISSION_PRECEDENCE: "deny overrides allow, including --allow-all-tools"
TOOL_FILTER_FLAGS: ["--available-tools", "--excluded-tools"]
TOOL_PERMISSION_FLAGS: ["--allow-tool", "--deny-tool", "--allow-all-tools"]
PATH_PERMISSION_FLAGS: ["--add-dir", "--allow-all-paths", "--disallow-temp-dir"]
URL_PERMISSION_FLAGS: ["--allow-url", "--deny-url", "--allow-all-urls"]
ALLOW_ALL_FLAGS: ["--allow-all", "--yolo"]

SLASH_COMMANDS: CSV<<
name,group,purpose
/init,agent_environment,Initialize Copilot instructions for this repository
/agent,agent_environment,Browse and select from available agents
/skills,agent_environment,Manage skills for enhanced capabilities
/mcp,agent_environment,Manage MCP server configuration
/plugin,agent_environment,Manage plugins and plugin marketplaces
/model,models_subagents,Select AI model to use
/fleet,models_subagents,Enable fleet mode for parallel subagent execution
/tasks,models_subagents,View and manage background tasks (subagents and shell sessions)
/ide,code,Connect to an IDE workspace
/diff,code,Review the changes made in the current directory
/review,code,Run code review agent to analyze changes
/lsp,code,Manage language server configuration
/terminal-setup,code,Configure terminal for multiline input support
/allow-all,permissions,Enable all permissions (tools, paths, URLs)
/add-dir,permissions,Add a directory to the allowed list for file access
/list-dirs,permissions,Display all allowed directories for file access
/cwd,permissions,Change working directory or show current directory
/reset-allowed-tools,permissions,Reset the list of allowed tools
/resume,session,Switch to a different session (optionally specify session ID)
/rename,session,Rename the current session
/context,session,Show context window token usage and visualization
/usage,session,Display session usage metrics and statistics
/session,session,Show session info and workspace summary
/compact,session,Summarize conversation history to reduce context window usage
/share,session,Share session or research report to markdown file or GitHub gist
/copy,session,Copy the last response to the clipboard
/help,help,Show help for interactive commands
/changelog,help,Display changelog for CLI versions
/feedback,help,Provide feedback about the CLI
/theme,help,View or configure terminal theme
/update,help,Update the CLI to the latest version
/experimental,help,Show or toggle experimental features
/clear,help,Clear the conversation history
/instructions,help,View and toggle custom instruction files
/streamer-mode,help,Toggle streamer mode (hides preview model names and quota details)
/exit,other,Exit the CLI
/quit,other,Exit the CLI
/login,other,Log in to Copilot
/logout,other,Log out of Copilot
/plan,other,Create an implementation plan before coding
/research,other,Run deep research investigation using GitHub search and web sources
/restart,other,Restart the CLI preserving the current session
/user,other,Manage GitHub user list
>>

SUBAGENT_INVOCATION_TOOLS: ["task"]
SUBAGENT_INVOCATION_COMMANDS: ["/fleet", "/tasks", "/agent"]
SUBAGENT_INVOCATION_FLAGS: ["--agent", "--autopilot", "--max-autopilot-continues"]

HOOK_EVENTS: ["preToolUse", "postToolUse", "userPromptSubmitted", "sessionStart", "sessionEnd", "errorOccurred", "agentStop"]
HOOK_DESIGN_LINEAGE: "Deliberately Claude-Code-compatible per SDK comment: 'Matches Claude Code terminology; extensible for future stop reasons.'"
HOOK_PLATFORMS: ["bash", "powershell"]
HOOK_DENY_RULE: "preToolUse hooks can deny a tool invocation by exiting with non-zero status or returning {decision: 'block'}."
HOOK_SDK_INTERFACE: "QueryHooks (programmatic embedding via @github/copilot SDK)"

BUILT_IN_MCP_SERVER: "github-mcp-server"
BUILT_IN_MCP_DISABLE_FLAG: "--disable-builtin-mcps"
BUILT_IN_MCP_TOOLSET_FLAGS: ["--add-github-mcp-tool", "--add-github-mcp-toolset", "--enable-all-github-mcp-tools"]

AGENT_MODELS: ["claude-sonnet-4.6", "claude-sonnet-4.5", "claude-haiku-4.5", "claude-opus-4.6", "claude-opus-4.6-fast", "claude-opus-4.5", "claude-sonnet-4", "gemini-3-pro-preview", "gpt-5.4", "gpt-5.3-codex", "gpt-5.2-codex", "gpt-5.2", "gpt-5.1-codex-max", "gpt-5.1-codex", "gpt-5.1", "gpt-5.1-codex-mini", "gpt-5-mini", "gpt-4.1"]
AGENT_MODEL_OVERRIDE_FLAG: "--model"
AGENT_MODEL_ENV: "COPILOT_MODEL"

INSTALLATION_METHODS: ["npm install -g @github/copilot", "brew install copilot-cli", "winget install GitHub.Copilot", "curl -fsSL https://gh.io/copilot-install | bash"]
PACKAGE_NAME: "@github/copilot"

AGENT_VERSIONING: JSON<<
{
  "templates": [
    {
      "path": "templates/.github/agents/aps-v{major}.{minor}.{patch}.agent.md",
      "current_path": "templates/.github/agents/aps-v1.2.2.agent.md",
      "frontmatter": {
        "name_pattern": "APS v{major}.{minor}.{patch} Agent",
        "description_pattern": "Generate APS v{major}.{minor}.{patch} .agent.md or .agent.yaml files for the Copilot CLI: detect artifact type from user intent, load APS+Copilot CLI adapter, extract intent, then generate+write+lint."
      },
      "format": "VSCode-format .agent.md (parsed by Copilot CLI in compatibility mode)"
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
  "shared_instruction_paths": ["AGENTS.md", "CLAUDE.md", "GEMINI.md"],
  "hook_compatibility": "Hook event names deliberately match Claude Code terminology per the SDK; a hooks.json authored for Copilot CLI uses the same event vocabulary as Claude Code's hook system."
}
>>

CONFIG_SETTINGS: CSV<<
key,type,default,purpose
allowed_urls,array,[],URLs/domains allowed without prompting
denied_urls,array,[],URLs/domains denied (override allows)
alt_screen,boolean,false,Use terminal alternate screen buffer
auto_update,boolean,true,Automatically download CLI updates
banner,enum,once,Animated banner frequency (always|once|never)
bash_env,boolean,false,Enable BASH_ENV support for bash shells
beep,boolean,true,Beep when user attention is required
compact_paste,boolean,true,Collapse large pasted content into compact tokens
copy_on_select,boolean,platform,Copy selected text to clipboard automatically
custom_agents.default_local_only,boolean,false,Default to local-only custom agents (skip remote org/enterprise)
experimental,boolean,false,Enable experimental features
include_coauthor,boolean,true,Add Co-authored-by trailer to git commits
companyAnnouncements,array,[],Banner messages displayed on startup
log_level,enum,default,Log level (none|error|warning|info|debug|all|default)
model,string,unset,Default AI model
mouse,boolean,true,Mouse support in alt screen mode
render_markdown,boolean,true,Render markdown in terminal
screen_reader,boolean,false,Screen reader optimizations
stream,boolean,true,Streaming mode
streamer_mode,boolean,false,Hide preview model names and quota details
theme,enum,auto,Color theme (auto|dark|light)
trusted_folders,array,[],Folders with read/execute permission granted
update_terminal_title,boolean,true,Update terminal tab title with current intent
ide.auto_connect,boolean,true,Automatically connect to IDE workspaces on startup
ide.open_diff_on_edit,boolean,true,Open file edit diffs in connected IDE for approval
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
<format id="COPILOT_CLI_AGENT_YAML_V1" name="Copilot CLI Native Agent YAML" purpose="YAML schema for native .agent.yaml files in .github/agents/ and ~/.copilot/agents/. This format is used by the Copilot CLI's bundled agents (task, explore, code-review, research) and is the canonical native schema.">
name: <AGENT_NAME>
displayName: <AGENT_DISPLAY_NAME>
description: >
  <AGENT_DESCRIPTION>
model: <MODEL>
tools:
  - "<TOOL_NAME>"
promptParts:
  includeAISafety: <INCLUDE_AI_SAFETY>
  includeToolInstructions: <INCLUDE_TOOL_INSTRUCTIONS>
  includeParallelToolCalling: <INCLUDE_PARALLEL_TOOL_CALLING>
  includeCustomAgentInstructions: <INCLUDE_CUSTOM_AGENT_INSTRUCTIONS>
  includeEnvironmentContext: <INCLUDE_ENVIRONMENT_CONTEXT>
prompt: |
  <AGENT_PROMPT_BODY>

WHERE:
- <AGENT_NAME> is String; lowercase-hyphenated agent identifier matching ^[a-z][a-z0-9-]*$.
- <AGENT_DISPLAY_NAME> is String; human-readable display name shown in the agent picker (e.g., "Task Agent").
- <AGENT_DESCRIPTION> is String; multi-line description (YAML block scalar) used by the picker and the model to decide when to invoke this agent.
- <MODEL> is String; one of AGENT_MODELS (bare model id like `claude-haiku-4.5`); omit to inherit the orchestrator session model.
- <TOOL_NAME> is String; either a bare name from TOOL_BUILT_IN (e.g., `bash`, `view`, `create`, `web_fetch`, `task`) or `<server>/<tool>` slash notation for MCP tools (e.g., `github-mcp-server/get_pull_request`); use `"*"` to include all available tools.
- <INCLUDE_AI_SAFETY> is Boolean; inject standard AI safety instructions into the prompt.
- <INCLUDE_TOOL_INSTRUCTIONS> is Boolean; inject standard tool usage instructions.
- <INCLUDE_PARALLEL_TOOL_CALLING> is Boolean; inject parallel tool calling guidance.
- <INCLUDE_CUSTOM_AGENT_INSTRUCTIONS> is Boolean; inject the user's custom instructions (AGENTS.md and friends).
- <INCLUDE_ENVIRONMENT_CONTEXT> is Boolean; inject environment context (cwd, OS, etc.).
- <AGENT_PROMPT_BODY> is Markdown; the agent's actual instructions, supports template variables like `{{cwd}}`.
</format>

<format id="COPILOT_CLI_AGENT_MD_V1" name="Copilot CLI VSCode-Format Agent Markdown" purpose="YAML frontmatter contract for .agent.md files in .github/agents/ and ~/.copilot/agents/. Parsed by Copilot CLI in VSCode-format compatibility mode (per changelog 'Improved parsing of VSCode-formatted custom agents with the .agent.md suffix').">
---
name: <AGENT_NAME>
description: "<AGENT_DESCRIPTION>"
model: <MODEL>
tools: <TOOLS_ARRAY>
---

<AGENT_PROMPT_BODY>

WHERE:
- <AGENT_NAME> is String; agent identifier; the markdown filename minus the `.agent.md` suffix is used when omitted.
- <AGENT_DESCRIPTION> is String; single-line double-quoted description shown when the agent is listed or invoked.
- <MODEL> is String; one of AGENT_MODELS (bare model id); omit to inherit the orchestrator session model.
- <TOOLS_ARRAY> is YAML array of tool names from TOOL_BUILT_IN (bare snake_case) or `<server>/<tool>` slash patterns for MCP tools; use `["*"]` for all tools; omit to inherit the orchestrator allow set.
- <AGENT_PROMPT_BODY> is Markdown; the agent's instructions (mirrors the `prompt:` block scalar in the native YAML format).
</format>

<format id="COPILOT_CLI_SKILL_FRONTMATTER_V1" name="Copilot CLI Skill Frontmatter" purpose="YAML frontmatter contract for SKILL.md files under any of the SKILL_FILE_PATHS locations.">
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
- <ALLOWED_TOOLS_ARRAY> is YAML array of permission patterns (kind(arg?) form); omit to inherit the session allow set.
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

<format id="COPILOT_CLI_HOOKS_CONFIG_V1" name="Copilot CLI Hooks Config" purpose="JSON structure for hooks.json (cwd) or hooks/hooks.json (subdirectory variant). Hook event names match Claude Code terminology per the SDK design lineage.">
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
- <HOOK_EVENT> is one of HOOK_EVENTS (preToolUse, postToolUse, userPromptSubmitted, sessionStart, sessionEnd, errorOccurred, agentStop).
- <MATCHER_PATTERN> is String; tool name or permission pattern to match (e.g., `bash`, `shell(git:*)`); omit for unconditional hooks.
- <BASH_COMMAND> is String; shell command to execute on POSIX systems.
- <POWERSHELL_COMMAND> is String; shell command to execute on Windows systems.
- <CWD_PATH> is String; optional working directory for the hook command.
- <TIMEOUT_SEC> is Integer; optional timeout in seconds before the hook is killed.
- <ENV_KEY> and <ENV_VALUE> are Strings; optional environment variables passed to the hook process.
- A `preToolUse` hook that exits non-zero (or returns `{decision: "block"}` from the SDK) denies the matching tool invocation.
- An `agentStop` hook with `{decision: "block", reason: "..."}` forces the agent to take another turn instead of stopping.
</format>

<format id="COPILOT_CLI_MCP_CONFIG_V1" name="Copilot CLI MCP Config" purpose="JSON structure for ~/.copilot/mcp-config.json. Per-session additions can be passed via --additional-mcp-config <json|@file>.">
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
- <SERVER_NAME> is String; unique server id used in `<server>/<tool>` (tool array) and `<server>(<tool>?)` (permissions) references.
- <SERVER_TYPE> is one of `local`, `stdio`, `http`, `sse`.
- <COMMAND> is String; executable for `local` or `stdio` servers; omit for `http`/`sse`.
- <ARG> is String; command-line argument for `local`/`stdio` servers.
- <URL> is String; endpoint URL for `http` or `sse` servers; omit for `local`/`stdio`.
- <HEADER_KEY>/<HEADER_VALUE> are Strings; optional HTTP headers for `http`/`sse` servers.
- <ENV_KEY>/<ENV_VALUE> are Strings; optional environment variables for `local`/`stdio` servers.
- <TOOL_NAME> is String; optional allowlist of tool names exposed by the server; omit to expose all advertised tools.
- The built-in `github-mcp-server` is enabled by default; disable it with `--disable-builtin-mcps` or scope its toolset with `--add-github-mcp-tool` / `--add-github-mcp-toolset`.
</format>

<format id="COPILOT_CLI_PERMISSIONS_V1" name="Copilot CLI Permissions Config" purpose="JSON structure for ~/.copilot/permissions-config.json. Patterns added at runtime via --allow-tool/--deny-tool are merged into this file.">
{
  "allow": ["<PERMISSION_PATTERN>"],
  "deny": ["<PERMISSION_PATTERN>"]
}

WHERE:
- <PERMISSION_PATTERN> is String; one of the kinds in TOOL_PERMISSION_KINDS:
  - `shell(<command>:*?)` exact-matches a shell command; the optional `:*` suffix matches command stems by prefix (e.g., `shell(git:*)` matches `git push` but not `gitea`).
  - `write` matches the `create` and `edit` tools (not shell redirections).
  - `url(<domain-or-url>?)` matches URL access via the `bash`, `powershell`, and `web_fetch` tools; protocol-aware.
  - `<mcp-server-name>(<tool-name>?)` matches a specific MCP tool, or all tools from that server if the tool name is omitted.
- Deny rules ALWAYS override allow rules, even `--allow-all-tools`.
</format>

<format id="COPILOT_CLI_CONFIG_V1" name="Copilot CLI Config" purpose="JSON structure for ~/.copilot/config.json. Many keys are persisted automatically when set via flags or slash commands.">
{
  "model": "<MODEL>",
  "theme": "<THEME>",
  "trusted_folders": ["<FOLDER_PATH>"],
  "allowed_urls": ["<URL_OR_DOMAIN>"],
  "denied_urls": ["<URL_OR_DOMAIN>"],
  "auto_update": <AUTO_UPDATE>,
  "experimental": <EXPERIMENTAL>,
  "include_coauthor": <INCLUDE_COAUTHOR>,
  "log_level": "<LOG_LEVEL>",
  "stream": <STREAM>,
  "streamer_mode": <STREAMER_MODE>,
  "render_markdown": <RENDER_MARKDOWN>,
  "screen_reader": <SCREEN_READER>,
  "alt_screen": <ALT_SCREEN>,
  "mouse": <MOUSE>,
  "compact_paste": <COMPACT_PASTE>,
  "copy_on_select": <COPY_ON_SELECT>,
  "bash_env": <BASH_ENV>,
  "banner": "<BANNER>",
  "beep": <BEEP>,
  "update_terminal_title": <UPDATE_TERMINAL_TITLE>,
  "companyAnnouncements": ["<ANNOUNCEMENT>"],
  "custom_agents": {
    "default_local_only": <DEFAULT_LOCAL_ONLY>
  },
  "ide": {
    "auto_connect": <IDE_AUTO_CONNECT>,
    "open_diff_on_edit": <IDE_OPEN_DIFF_ON_EDIT>
  }
}

WHERE:
- <MODEL> is String; default model id from AGENT_MODELS.
- <THEME> is one of `auto`, `dark`, `light`.
- <FOLDER_PATH> is String; absolute path to a folder marked as trusted (read/execute granted).
- <URL_OR_DOMAIN> is String; protocol-aware URL or domain pattern (e.g., `https://github.com`, `*.github.com`).
- <AUTO_UPDATE>, <EXPERIMENTAL>, <INCLUDE_COAUTHOR>, <STREAM>, <STREAMER_MODE>, <RENDER_MARKDOWN>, <SCREEN_READER>, <ALT_SCREEN>, <MOUSE>, <COMPACT_PASTE>, <COPY_ON_SELECT>, <BASH_ENV>, <BEEP>, <UPDATE_TERMINAL_TITLE>, <DEFAULT_LOCAL_ONLY>, <IDE_AUTO_CONNECT>, <IDE_OPEN_DIFF_ON_EDIT> are Boolean.
- <LOG_LEVEL> is one of `none`, `error`, `warning`, `info`, `debug`, `all`, `default`.
- <BANNER> is one of `always`, `once`, `never`.
- <ANNOUNCEMENT> is String; one of multiple banner messages randomly selected at startup.
</format>
</formats>
