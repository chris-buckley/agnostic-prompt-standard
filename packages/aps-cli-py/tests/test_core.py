from pathlib import Path

import pytest

from aps_cli.core import (
    DEFAULT_ADAPTER_ORDER,
    compute_install_families,
    compute_skill_destinations,
    detect_adapters,
    detect_platforms,
    find_repo_root,
    infer_platform_id,
    load_platforms,
    replace_dir_with_copy,
    resolve_payload_skill_dir,
    sort_platforms_for_ui,
)


def test_find_repo_root(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    assert find_repo_root(nested) == tmp_path


def test_find_repo_root_returns_none(tmp_path: Path):
    nested = tmp_path / "a"
    nested.mkdir()
    assert find_repo_root(nested) is None


def test_infer_platform_id_vscode(tmp_path: Path):
    (tmp_path / ".github" / "prompts").mkdir(parents=True)
    assert infer_platform_id(tmp_path) == "vscode-copilot"


def test_detect_platforms_finds_vscode_copilot(tmp_path: Path):
    """Test detection of vscode-copilot via .github/copilot-instructions.md marker."""
    # Create marker
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "copilot-instructions.md").touch()

    skill_dir = resolve_payload_skill_dir()
    detected = detect_platforms(tmp_path, skill_dir)

    assert "vscode-copilot" in detected


def test_detect_platforms_finds_claude_code(tmp_path: Path):
    """Test detection of claude-code via .claude directory marker."""
    # Create marker
    (tmp_path / ".claude").mkdir()

    skill_dir = resolve_payload_skill_dir()
    detected = detect_platforms(tmp_path, skill_dir)

    assert "claude-code" in detected


def test_detect_platforms_finds_claude_code_via_claude_md(tmp_path: Path):
    """Test detection of claude-code via CLAUDE.md file marker."""
    (tmp_path / "CLAUDE.md").write_text("# Claude")
    skill_dir = resolve_payload_skill_dir()
    detected = detect_platforms(tmp_path, skill_dir)
    assert "claude-code" in detected


def test_detect_platforms_finds_claude_code_via_mcp_json(tmp_path: Path):
    """Test detection of claude-code via .mcp.json file marker."""
    (tmp_path / ".mcp.json").write_text("{}")
    skill_dir = resolve_payload_skill_dir()
    detected = detect_platforms(tmp_path, skill_dir)
    assert "claude-code" in detected


def test_detect_platforms_finds_multiple(tmp_path: Path):
    """Test detection of multiple platforms."""
    # Create markers for both
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "copilot-instructions.md").touch()
    (tmp_path / ".claude").mkdir()

    skill_dir = resolve_payload_skill_dir()
    detected = detect_platforms(tmp_path, skill_dir)

    assert "vscode-copilot" in detected
    assert "claude-code" in detected


def test_detect_platforms_returns_empty_when_no_markers(tmp_path: Path):
    """Test that empty list is returned when no markers exist."""
    skill_dir = resolve_payload_skill_dir()
    detected = detect_platforms(tmp_path, skill_dir)

    assert detected == []


# OpenCode detection tests (only run if opencode platform exists)


def test_detect_platforms_finds_opencode_directory(tmp_path: Path):
    """Test detection of opencode via .opencode/ directory marker."""
    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)

    # Skip if opencode platform not available
    if not any(p.platform_id == "opencode" for p in platforms):
        pytest.skip("opencode platform not available in payload")

    (tmp_path / ".opencode").mkdir()
    detected = detect_platforms(tmp_path, skill_dir)
    assert "opencode" in detected


def test_detect_platforms_finds_opencode_jsonc_in_dir(tmp_path: Path):
    """Test detection of opencode via .opencode/opencode.jsonc marker."""
    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)

    if not any(p.platform_id == "opencode" for p in platforms):
        pytest.skip("opencode platform not available in payload")

    opencode_dir = tmp_path / ".opencode"
    opencode_dir.mkdir()
    (opencode_dir / "opencode.jsonc").write_text("{}")
    detected = detect_platforms(tmp_path, skill_dir)
    assert "opencode" in detected


def test_detect_platforms_finds_opencode_json_in_dir(tmp_path: Path):
    """Test detection of opencode via .opencode/opencode.json marker."""
    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)

    if not any(p.platform_id == "opencode" for p in platforms):
        pytest.skip("opencode platform not available in payload")

    opencode_dir = tmp_path / ".opencode"
    opencode_dir.mkdir()
    (opencode_dir / "opencode.json").write_text("{}")
    detected = detect_platforms(tmp_path, skill_dir)
    assert "opencode" in detected


def test_detect_platforms_finds_opencode_json_root(tmp_path: Path):
    """Test detection of opencode via opencode.json at root marker."""
    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)

    if not any(p.platform_id == "opencode" for p in platforms):
        pytest.skip("opencode platform not available in payload")

    (tmp_path / "opencode.json").write_text("{}")
    detected = detect_platforms(tmp_path, skill_dir)
    assert "opencode" in detected


def test_detect_platforms_finds_opencode_jsonc_root(tmp_path: Path):
    """Test detection of opencode via opencode.jsonc at root marker."""
    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)

    if not any(p.platform_id == "opencode" for p in platforms):
        pytest.skip("opencode platform not available in payload")

    (tmp_path / "opencode.jsonc").write_text("{}")
    detected = detect_platforms(tmp_path, skill_dir)
    assert "opencode" in detected


def test_detect_platforms_finds_opencode_json_dotted_root(tmp_path: Path):
    """Test detection of opencode via .opencode.json at root marker."""
    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)

    if not any(p.platform_id == "opencode" for p in platforms):
        pytest.skip("opencode platform not available in payload")

    (tmp_path / ".opencode.json").write_text('{"ok":true}')
    detected = detect_platforms(tmp_path, skill_dir)
    assert "opencode" in detected


def test_detect_adapters_returns_detection_objects(tmp_path: Path):
    """Test that detect_adapters returns AdapterDetection objects."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "copilot-instructions.md").touch()

    skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(skill_dir)
    detections = detect_adapters(tmp_path, platforms)

    assert "vscode-copilot" in detections
    assert detections["vscode-copilot"].detected is True
    assert len(detections["vscode-copilot"].reasons) > 0


def test_compute_skill_destinations_single_non_claude(tmp_path: Path):
    """Test destinations for non-Claude platform."""
    dests = compute_skill_destinations("repo", tmp_path, ["vscode-copilot"])
    assert len(dests) == 1
    assert ".github" in str(dests[0])


def test_compute_skill_destinations_single_claude(tmp_path: Path):
    """Test destinations for Claude platform."""
    dests = compute_skill_destinations("repo", tmp_path, ["claude-code"])
    assert len(dests) == 1
    assert ".claude" in str(dests[0])


def test_compute_skill_destinations_multiple_platforms(tmp_path: Path):
    """Test destinations for both Claude and non-Claude platforms."""
    dests = compute_skill_destinations("repo", tmp_path, ["vscode-copilot", "claude-code"])
    assert len(dests) == 2
    paths_str = [str(d) for d in dests]
    assert any(".github" in p for p in paths_str)
    assert any(".claude" in p for p in paths_str)


def test_compute_skill_destinations_empty_defaults_to_non_claude(tmp_path: Path):
    """Test that empty platform list defaults to non-Claude location."""
    dests = compute_skill_destinations("repo", tmp_path, [])
    assert len(dests) == 1
    assert ".github" in str(dests[0])


def test_default_adapter_order():
    """Test that DEFAULT_ADAPTER_ORDER contains known adapters."""
    assert DEFAULT_ADAPTER_ORDER == ("vscode-copilot", "claude-code", "opencode", "generic")


def test_sort_platforms_for_ui():
    """Test that platforms are sorted with known adapters first."""
    from aps_cli.core import Platform

    platforms = [
        Platform("zzz-platform", "ZZZ Platform", None, ()),
        Platform("opencode", "OpenCode", None, ()),
        Platform("vscode-copilot", "VS Code Copilot", None, ()),
        Platform("aaa-platform", "AAA Platform", None, ()),
        Platform("claude-code", "Claude Code", None, ()),
        Platform("generic", "Generic / External Tools", None, ()),
    ]

    sorted_platforms = sort_platforms_for_ui(platforms)
    sorted_ids = [p.platform_id for p in sorted_platforms]

    # Known adapters should come first in order
    assert sorted_ids[:4] == ["vscode-copilot", "claude-code", "opencode", "generic"]
    # Remaining should be alphabetically sorted by display name
    assert sorted_ids[4:] == ["aaa-platform", "zzz-platform"]

def test_compute_install_families_generic_only_defaults_to_non_claude():
    """Generic adapter alone should keep the historical non-Claude fallback."""
    assert compute_install_families(["generic"]) == (False, True)


def test_compute_install_families_generic_plus_claude_keeps_claude_only():
    """Generic adapter must not force a non-Claude install family."""
    assert compute_install_families(["generic", "claude-code"]) == (True, False)


def test_replace_dir_with_copy_swaps_directory_contents_without_stale_files(tmp_path: Path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"

    (src / "nested").mkdir(parents=True)
    (src / "SKILL.md").write_text('framework_revision: "1.2.0"\n', encoding="utf-8")
    (src / "nested" / "new.txt").write_text("new\n", encoding="utf-8")

    (dest / "nested").mkdir(parents=True)
    (dest / "old.txt").write_text("old\n", encoding="utf-8")
    (dest / "nested" / "stale.txt").write_text("stale\n", encoding="utf-8")

    replaced_existing, leftover_backup = replace_dir_with_copy(src, dest)

    assert replaced_existing is True
    assert leftover_backup is None
    assert (dest / "SKILL.md").read_text(encoding="utf-8") == 'framework_revision: "1.2.0"\n'
    assert (dest / "nested" / "new.txt").read_text(encoding="utf-8") == "new\n"
    assert not (dest / "old.txt").exists()
    assert not (dest / "nested" / "stale.txt").exists()
