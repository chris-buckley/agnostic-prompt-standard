from pathlib import Path

from aps_cli.core import (
    DEFAULT_ADAPTER_ORDER,
    compute_skill_destinations,
    detect_adapters,
    detect_platforms,
    find_repo_root,
    infer_platform_id,
    load_platforms,
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
    assert DEFAULT_ADAPTER_ORDER == ("vscode-copilot", "claude-code", "opencode")


def test_sort_platforms_for_ui():
    """Test that platforms are sorted with known adapters first."""
    from aps_cli.core import Platform

    platforms = [
        Platform("zzz-platform", "ZZZ Platform", None, ()),
        Platform("opencode", "OpenCode", None, ()),
        Platform("vscode-copilot", "VS Code Copilot", None, ()),
        Platform("aaa-platform", "AAA Platform", None, ()),
        Platform("claude-code", "Claude Code", None, ()),
    ]

    sorted_platforms = sort_platforms_for_ui(platforms)
    sorted_ids = [p.platform_id for p in sorted_platforms]

    # Known adapters should come first in order
    assert sorted_ids[:3] == ["vscode-copilot", "claude-code", "opencode"]
    # Remaining should be alphabetically sorted by display name
    assert sorted_ids[3:] == ["aaa-platform", "zzz-platform"]