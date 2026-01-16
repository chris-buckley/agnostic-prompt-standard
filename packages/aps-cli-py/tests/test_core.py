from pathlib import Path

from aps_cli.core import find_repo_root, infer_platform_id


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
