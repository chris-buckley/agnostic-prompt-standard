from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Optional
from urllib.request import Request, urlopen

from .core import (
    default_personal_skill_path,
    default_project_skill_path,
    list_files_recursive,
    pick_workspace_root,
    replace_dir_with_copy,
)

APS_SKIP_SELF_UPDATE_ENV = "APS_SKIP_SELF_UPDATE"
PYPI_PACKAGE_NAME = "agnostic-prompt-aps"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"

PyRuntimeMode = Literal["dev-local", "ephemeral", "installed"]
SkillUpdateStatus = Literal["missing", "orphaned", "up-to-date", "update-available", "updated"]


@dataclass(frozen=True)
class SkillUpdateTarget:
    scope: str
    path: Path
    exists: bool
    installed_version: Optional[str]
    desired_version: str
    status: SkillUpdateStatus


@dataclass(frozen=True)
class PackageUpdateStatus:
    package_name: str
    current_version: str
    payload_version: str
    latest_version: Optional[str]
    update_available: bool
    runtime_mode: PyRuntimeMode
    registry_error: Optional[str]


def parse_semver(value: str) -> Optional[tuple[int, int, int]]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def compare_semver(a: str, b: str) -> int:
    parsed_a = parse_semver(a)
    parsed_b = parse_semver(b)
    if parsed_a is None or parsed_b is None:
        return (a > b) - (a < b)
    return (parsed_a > parsed_b) - (parsed_a < parsed_b)


def detect_python_runtime_mode(module_path: Path, executable: Optional[Path] = None) -> PyRuntimeMode:
    normalized_module = str(module_path.resolve()).replace("\\", "/")
    normalized_executable = str((executable or Path(sys.executable)).resolve()).replace("\\", "/")
    combined = f"{normalized_module} {normalized_executable}"

    if "/packages/aps-cli-py/" in normalized_module:
        return "dev-local"
    if "/.cache/pipx/" in combined or "/pipx/.cache/" in combined:
        return "ephemeral"
    return "installed"


def read_framework_revision_from_text(text: str) -> Optional[str]:
    match = re.search(r'framework_revision:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', text)
    return match.group(1) if match else None


def read_skill_version(skill_dir: Path) -> Optional[str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    return read_framework_revision_from_text(skill_md.read_text(encoding="utf-8"))


def _extract_version_candidates(text: str) -> list[str]:
    out: set[str] = set()
    for pattern in (
        re.compile(r'framework_revision:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?'),
        re.compile(r"aps-v([0-9]+\.[0-9]+\.[0-9]+)(?:\.agent)?\.md\b"),
    ):
        for match in pattern.finditer(text):
            version = match.group(1)
            if version:
                out.add(version)
    return list(out)


def _pick_highest_version(versions: list[str]) -> Optional[str]:
    highest: Optional[str] = None
    for version in versions:
        if highest is None or compare_semver(version, highest) > 0:
            highest = version
    return highest


def infer_installed_skill_version(skill_dir: Path) -> Optional[str]:
    skill_md_version = read_skill_version(skill_dir)
    if skill_md_version:
        return skill_md_version

    platforms_dir = skill_dir / "platforms"
    if not platforms_dir.is_dir():
        return None

    versions: set[str] = set()

    try:
        files = list_files_recursive(platforms_dir)
    except Exception:
        return None

    for file_path in files:
        versions.update(_extract_version_candidates(str(file_path)))

        if file_path.name != "adaptor.md":
            continue

        try:
            versions.update(_extract_version_candidates(file_path.read_text(encoding="utf-8")))
        except Exception:
            # Ignore unreadable adaptor files while inferring a best-effort version.
            pass

    return _pick_highest_version(list(versions))


def fetch_latest_cli_version(
    urlopen_func: Callable[..., object] = urlopen,
) -> str:
    request = Request(PYPI_JSON_URL, headers={"Accept": "application/json"})
    response = urlopen_func(request, timeout=10)
    with response as handle:  # type: ignore[attr-defined]
        data = json.load(handle)

    latest = data.get("info", {}).get("version")
    if not isinstance(latest, str) or parse_semver(latest) is None:
        raise ValueError("PyPI JSON API response did not include a valid info.version")
    return latest


def collect_skill_targets(
    *,
    root: Optional[str],
    repo: bool,
    personal: bool,
    desired_version: str,
) -> list[SkillUpdateTarget]:
    workspace_root = pick_workspace_root(root)
    if repo and workspace_root is None:
        raise ValueError(
            "Repo update selected but no workspace root found. Run in a git repo or pass --root <path>."
        )

    explicit_scope = repo or personal
    candidates: list[tuple[str, Path]] = []

    if repo or (not explicit_scope and workspace_root is not None):
        if workspace_root is not None:
            candidates.append(("repo", default_project_skill_path(workspace_root, claude=False)))
            candidates.append(("repo (claude)", default_project_skill_path(workspace_root, claude=True)))

    if personal or not explicit_scope:
        candidates.append(("personal", default_personal_skill_path(claude=False)))
        candidates.append(("personal (claude)", default_personal_skill_path(claude=True)))

    seen: set[Path] = set()
    targets: list[SkillUpdateTarget] = []

    for scope, target_path in candidates:
        if target_path in seen:
            continue
        seen.add(target_path)

        exists = target_path.exists()
        if not explicit_scope and not exists:
            continue

        has_entrypoint = exists and (target_path / "SKILL.md").exists()
        installed_version = infer_installed_skill_version(target_path) if exists else None

        if not exists:
            status: SkillUpdateStatus = "missing"
        elif not has_entrypoint:
            status = "orphaned"
        elif installed_version == desired_version:
            status = "up-to-date"
        else:
            status = "update-available"

        targets.append(
            SkillUpdateTarget(
                scope=scope,
                path=target_path,
                exists=exists,
                installed_version=installed_version,
                desired_version=desired_version,
                status=status,
            )
        )

    return targets


def apply_skill_updates(
    targets: list[SkillUpdateTarget], payload_skill_dir: Path, *, force: bool
) -> list[SkillUpdateTarget]:
    updated_targets: list[SkillUpdateTarget] = []

    for target in targets:
        if not target.exists:
            updated_targets.append(target)
            continue

        if target.status == "up-to-date" and not force:
            updated_targets.append(target)
            continue

        replace_dir_with_copy(payload_skill_dir, target.path)
        updated_targets.append(
            SkillUpdateTarget(
                scope=target.scope,
                path=target.path,
                exists=True,
                installed_version=target.desired_version,
                desired_version=target.desired_version,
                status="updated",
            )
        )

    return updated_targets


def build_forwarded_args(
    *,
    root: Optional[str],
    repo: bool,
    personal: bool,
    check: bool,
    json_out: bool,
    dry_run: bool,
    yes: bool,
    force: bool,
) -> list[str]:
    args = ["update"]
    if root:
        args.extend(["--root", root])
    if repo:
        args.append("--repo")
    if personal:
        args.append("--personal")
    if check:
        args.append("--check")
    if json_out:
        args.append("--json")
    if dry_run:
        args.append("--dry-run")
    if yes:
        args.append("--yes")
    if force:
        args.append("--force")
    return args


def run_and_exit(command: list[str]) -> None:
    env = dict(os.environ)
    env[APS_SKIP_SELF_UPDATE_ENV] = "1"
    result = subprocess.run(command, env=env, check=False)
    raise SystemExit(result.returncode)


def try_command(command: list[str]) -> bool:
    result = subprocess.run(command, check=False)
    return result.returncode == 0


def maybe_self_update(
    *,
    runtime_mode: PyRuntimeMode,
    latest_version: str,
    root: Optional[str],
    repo: bool,
    personal: bool,
    check: bool,
    json_out: bool,
    dry_run: bool,
    yes: bool,
    force: bool,
) -> None:
    forwarded_args = build_forwarded_args(
        root=root,
        repo=repo,
        personal=personal,
        check=check,
        json_out=json_out,
        dry_run=dry_run,
        yes=yes,
        force=force,
    )

    if runtime_mode == "dev-local":
        return

    if runtime_mode == "ephemeral" and shutil.which("pipx"):
        run_and_exit(["pipx", "run", "--no-cache", PYPI_PACKAGE_NAME, *forwarded_args])

    if shutil.which("pipx") and try_command(["pipx", "upgrade", "--install", PYPI_PACKAGE_NAME]):
        run_and_exit([sys.executable, "-m", "aps_cli", *forwarded_args])

    if try_command([sys.executable, "-m", "pip", "install", "--upgrade", f"{PYPI_PACKAGE_NAME}=={latest_version}"]):
        run_and_exit([sys.executable, "-m", "aps_cli", *forwarded_args])

    if shutil.which("pipx"):
        run_and_exit(["pipx", "run", "--no-cache", PYPI_PACKAGE_NAME, *forwarded_args])

    raise RuntimeError("Unable to self-update APS CLI with pipx or pip")
