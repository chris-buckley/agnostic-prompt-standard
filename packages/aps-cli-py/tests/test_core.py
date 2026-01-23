from pathlib import Path

from aps_cli.core import (
    detect_platforms,
    find_repo_root,
    infer_platform_id,
    resolve_payload_skill_dir,
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
