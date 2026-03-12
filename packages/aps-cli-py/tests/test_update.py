from __future__ import annotations

import io
import json
from pathlib import Path

from aps_cli.update import (
    collect_skill_targets,
    compare_semver,
    detect_python_runtime_mode,
    fetch_latest_cli_version,
    infer_installed_skill_version,
    read_framework_revision_from_text,
)


class _FakeResponse:
    def __init__(self, payload: dict):
        self._stream = io.StringIO(json.dumps(payload))

    def __enter__(self):
        return self._stream

    def __exit__(self, exc_type, exc, tb):
        self._stream.close()
        return False


def test_compare_semver_orders_versions():
    assert compare_semver("1.2.0", "1.1.9") == 1
    assert compare_semver("1.1.9", "1.2.0") == -1
    assert compare_semver("1.2.0", "1.2.0") == 0


def test_detect_python_runtime_mode_classifies_dev_local():
    mode = detect_python_runtime_mode(
        Path("/repo/agnostic-prompt-standard/packages/aps-cli-py/src/aps_cli/update.py"),
        Path("/usr/bin/python3"),
    )
    assert mode == "dev-local"


def test_detect_python_runtime_mode_classifies_pipx_cache_as_ephemeral():
    mode = detect_python_runtime_mode(
        Path("/home/user/.cache/pipx/venvs/agnostic-prompt-aps/lib/python3.12/site-packages/aps_cli/update.py"),
        Path("/home/user/.cache/pipx/venvs/agnostic-prompt-aps/bin/python"),
    )
    assert mode == "ephemeral"


def test_detect_python_runtime_mode_defaults_to_installed():
    mode = detect_python_runtime_mode(
        Path("/usr/lib/python3.12/site-packages/aps_cli/update.py"),
        Path("/usr/bin/python3"),
    )
    assert mode == "installed"


def test_fetch_latest_cli_version_reads_pypi_info_version():
    latest = fetch_latest_cli_version(
        lambda *args, **kwargs: _FakeResponse({"info": {"version": "1.2.3"}})
    )
    assert latest == "1.2.3"


def test_fetch_latest_cli_version_rejects_invalid_version():
    try:
        fetch_latest_cli_version(
            lambda *args, **kwargs: _FakeResponse({"info": {"version": "latest"}})
        )
    except ValueError as exc:
        assert "valid info.version" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid info.version")


def test_read_framework_revision_from_text_extracts_version():
    text = 'metadata:\n  framework_revision: "1.2.3"\n'
    assert read_framework_revision_from_text(text) == "1.2.3"


def test_collect_skill_targets_only_returns_existing_targets_by_default(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "workspace"
    repo_skill = repo_root / ".github" / "skills" / "agnostic-prompt-standard"
    repo_skill.mkdir(parents=True)
    (repo_skill / "SKILL.md").write_text('framework_revision: "1.2.3"', encoding="utf-8")

    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    targets = collect_skill_targets(
        root=str(repo_root),
        repo=False,
        personal=False,
        desired_version="1.2.4",
    )

    assert len(targets) == 1
    assert targets[0].scope == "repo"
    assert targets[0].status == "update-available"


def test_collect_skill_targets_reports_missing_when_scope_is_explicit(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    targets = collect_skill_targets(
        root=str(repo_root),
        repo=True,
        personal=False,
        desired_version="1.2.4",
    )

    assert len(targets) == 2
    assert all(target.status == "missing" for target in targets)


def test_infer_installed_skill_version_uses_versioned_adapter_artifacts_when_skill_md_is_missing(tmp_path: Path):
    skill_dir = tmp_path / "skill"
    adaptor_dir = skill_dir / "platforms" / "claude-code"
    template_dir = skill_dir / "platforms" / "vscode-copilot" / "templates" / ".github" / "agents"

    adaptor_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    (adaptor_dir / "adaptor.md").write_text(
        'current_path: "templates/.claude/agents/aps-v1.1.16.md"\n',
        encoding="utf-8",
    )
    (template_dir / "aps-v1.1.16.agent.md").write_text("# agent\n", encoding="utf-8")

    assert infer_installed_skill_version(skill_dir) == "1.1.16"


def test_collect_skill_targets_marks_orphaned_installs_when_directory_exists_without_skill_md(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "workspace"
    repo_skill = repo_root / ".github" / "skills" / "agnostic-prompt-standard"
    template_dir = repo_skill / "platforms" / "vscode-copilot" / "templates" / ".github" / "agents"
    template_dir.mkdir(parents=True)
    (template_dir / "aps-v1.1.16.agent.md").write_text("# agent\n", encoding="utf-8")

    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    targets = collect_skill_targets(
        root=str(repo_root),
        repo=False,
        personal=False,
        desired_version="1.2.0",
    )

    assert len(targets) == 1
    assert targets[0].scope == "repo"
    assert targets[0].status == "orphaned"
    assert targets[0].installed_version == "1.1.16"
