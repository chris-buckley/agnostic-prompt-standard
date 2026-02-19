"""Tests for the adaptor.md parser."""

from aps_cli.parsers.adaptor import (
    AdaptorData,
    FormatContract,
    get_string,
    get_string_array,
    parse_adaptor_md_string,
)

SAMPLE_ADAPTOR = """
<instructions>
Generate artifacts for Test Platform.
Tool names are PascalCase.
</instructions>

<constants>
PLATFORM_ID: "test-platform"
DISPLAY_NAME: "Test Platform"
ADAPTER_VERSION: "2.0.0"
LAST_UPDATED: "2026-02-19"
ENABLED: true
MAX_RETRIES: 3

INSTRUCTION_FILE_PATHS: ["./README.md", "./docs/*.md"]
DETECTION_MARKERS: [".test", "test.json"]

DESCRIPTION: TEXT<<
This is a multi-line
text block constant.
>>

CONFIG: JSON<<
{
  "key": "value",
  "nested": { "a": 1 }
}
>>

TOOLS: CSV<<
name,risk,description
Read,low,"Read files"
Write,medium,"Write files"
>>
</constants>

<formats>
<format id="TEST_FORMAT_V1" name="Test Format" purpose="A test format contract.">
## Title: <TITLE>

Content here.

WHERE:
- <TITLE> is String; the title.
</format>
</formats>
"""


def test_parses_instructions():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert "Generate artifacts for Test Platform" in data.instructions
    assert "PascalCase" in data.instructions


def test_parses_string_constants():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert data.constants["PLATFORM_ID"] == "test-platform"
    assert data.constants["DISPLAY_NAME"] == "Test Platform"
    assert data.constants["ADAPTER_VERSION"] == "2.0.0"


def test_parses_boolean_constants():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert data.constants["ENABLED"] is True


def test_parses_number_constants():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert data.constants["MAX_RETRIES"] == 3


def test_parses_inline_arrays():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert data.constants["INSTRUCTION_FILE_PATHS"] == ["./README.md", "./docs/*.md"]
    assert data.constants["DETECTION_MARKERS"] == [".test", "test.json"]


def test_parses_text_blocks():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    desc = data.constants["DESCRIPTION"]
    assert isinstance(desc, str)
    assert "multi-line" in desc
    assert "text block constant" in desc


def test_parses_json_blocks():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    config = data.constants["CONFIG"]
    assert isinstance(config, dict)
    assert config["key"] == "value"
    assert config["nested"] == {"a": 1}


def test_parses_csv_blocks():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    tools = data.constants["TOOLS"]
    assert isinstance(tools, list)
    assert len(tools) == 2
    assert tools[0]["name"] == "Read"
    assert tools[0]["risk"] == "low"
    assert tools[1]["name"] == "Write"


def test_parses_formats():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert "TEST_FORMAT_V1" in data.formats
    fmt = data.formats["TEST_FORMAT_V1"]
    assert fmt.name == "Test Format"
    assert fmt.purpose == "A test format contract."
    assert "WHERE:" in fmt.body


def test_get_string_helper():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert get_string(data.constants, "PLATFORM_ID") == "test-platform"
    assert get_string(data.constants, "MISSING", "default") == "default"


def test_get_string_array_helper():
    data = parse_adaptor_md_string(SAMPLE_ADAPTOR)
    assert get_string_array(data.constants, "DETECTION_MARKERS") == [".test", "test.json"]
    assert get_string_array(data.constants, "MISSING") == []


def test_handles_empty_input():
    data = parse_adaptor_md_string("")
    assert data.instructions == ""
    assert data.constants == {}
    assert data.formats == {}


def test_parses_real_claude_code_adaptor():
    """Verify parser handles the actual Claude Code adaptor.md structure."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    adaptor_path = repo_root / "skill" / "agnostic-prompt-standard" / "platforms" / "claude-code" / "adaptor.md"

    if not adaptor_path.exists():
        return  # Skip if not in repo context

    from aps_cli.parsers.adaptor import parse_adaptor_md

    data = parse_adaptor_md(adaptor_path)

    assert data.constants["PLATFORM_ID"] == "claude-code"
    assert data.constants["DISPLAY_NAME"] == "Claude Code CLI"
    assert isinstance(data.constants["DETECTION_MARKERS"], list)
    assert isinstance(data.constants["TOOLS"], list)
    assert len(data.constants["TOOLS"]) > 0
    assert "CC_AGENT_FRONTMATTER_V1" in data.formats
    assert "CC_RULES_FRONTMATTER_V1" in data.formats
