<instructions>
Generate artifacts for tool-agnostic APS usage or for runtimes that use external tools only.
Use this adapter when a host has no stable native tool registry, when tools come only from MCP or an equivalent external declaration file, or when you want one neutral tool layer across hosts.
Do not assume host-specific file names, frontmatter, or native tool naming.
Declare external tools in `predefinedTools.json` with canonical APS tool ids.
If a host exposes decorated runtime names, map them with `config.json` ALIAS entries instead of duplicating tool objects.
</instructions>

<constants>
PLATFORM_ID: "generic"
DISPLAY_NAME: "Generic / External Tools"
ADAPTER_VERSION: "1.0.0"
LAST_UPDATED: "2026-03-10"

INSTRUCTION_FILE_PATHS: []
DETECTION_MARKERS: []
MCP_CONFIG_PATHS: []
TOOL_SOURCES: ["native", "mcp", "mixed", "none"]
EXTERNAL_TOOL_DECLARATION_FILES: ["predefinedTools.json", "config.json"]

DOCS_MCP_URL: "https://modelcontextprotocol.io/specification/2025-06-18/schema"
</constants>

<formats>
</formats>
