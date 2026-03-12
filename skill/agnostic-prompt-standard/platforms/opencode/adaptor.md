<instructions>
Generate artifacts for the OpenCode agent runtime using the constants in this adapter.
OpenCode uses AGENTS.md and JSONC configuration files.
Configuration supports JSON with comments (JSONC).
MCP servers are declared in the top-level mcp object of the OpenCode config file.
</instructions>

<constants>
PLATFORM_ID: "opencode"
DISPLAY_NAME: "OpenCode"
ADAPTER_VERSION: "2.0.0"
LAST_UPDATED: "2026-02-19"

INSTRUCTION_FILE_PATHS: ["AGENTS.md", ".opencode/instructions.md"]
CONFIG_FILE_PATHS: [".opencode/opencode.jsonc", ".opencode/opencode.json", "opencode.json", "opencode.jsonc", ".opencode.json"]
MCP_CONFIG_PATHS: [".opencode/opencode.jsonc", ".opencode/opencode.json", "opencode.json", "opencode.jsonc", ".opencode.json"]

DETECTION_MARKERS: [".opencode", ".opencode/opencode.jsonc", ".opencode/opencode.json", "opencode.json", "opencode.jsonc", ".opencode.json"]

DOCS_OFFICIAL_URL: "https://opencode.ai/docs"
DOCS_CONFIG_URL: "https://opencode.ai/docs/config"
DOCS_MCP_URL: "https://opencode.ai/docs/mcp-servers/"
</constants>

<formats>
</formats>
