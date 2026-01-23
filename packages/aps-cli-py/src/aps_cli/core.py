from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

SKILL_ID = "agnostic-prompt-standard"


@dataclass(frozen=True)
class Platform:
    platform_id: str
    display_name: str
    adapter_version: Optional[str]
    detection_markers: tuple[str, ...] = field(default_factory=tuple)


def is_tty() -> bool:
    try:
        return bool(os.isatty(0) and os.isatty(1))
    except Exception:
        return False


def find_repo_root(start_dir: Path) -> Optional[Path]:
    cur = start_dir.resolve()
    while True:
        if (cur / ".git").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def default_project_skill_path(repo_root: Path, *, claude: bool = False) -> Path:
    """Return the project-skill path for the detected agent ecosystem.

    - Default: `.github/skills/<skill-id>/` (Copilot Agent Skills)
    - Claude:  `.claude/skills/<skill-id>/` (Claude platform)
    """
    base = repo_root / (".claude" if claude else ".github") / "skills"
    return base / SKILL_ID


def default_personal_skill_path(*, claude: bool = False) -> Path:
    """Return the per-user skill path.

    - Default: `~/.copilot/skills/<skill-id>/`
    - Claude:  `~/.claude/skills/<skill-id>/`
    """
    base = Path.home() / (".claude" if claude else ".copilot") / "skills"
    return base / SKILL_ID


def infer_platform_id(workspace_root: Path) -> Optional[str]:
    gh = workspace_root / ".github"
    has_agents = (gh / "agents").exists()
    has_prompts = (gh / "prompts").exists()
    has_instructions = (gh / "copilot-instructions.md").exists() or (
        gh / "instructions"
    ).exists()
    if has_agents or has_prompts or has_instructions:
        return "vscode-copilot"
    return None


def detect_platforms(workspace_root: Path, skill_dir: Path) -> list[str]:
    """Detect all platforms with markers present in workspace.

    Args:
        workspace_root: Path to workspace root
        skill_dir: Path to skill directory with platform manifests

    Returns:
        List of detected platform IDs
    """
    platforms = load_platforms(skill_dir)
    detected: list[str] = []

    for platform in platforms:
        for marker in platform.detection_markers:
            marker_path = workspace_root / marker
            if marker_path.exists():
                detected.append(platform.platform_id)
                break  # One marker match is sufficient

    return detected


def resolve_payload_skill_dir() -> Path:
    """Locate the bundled APS skill directory.

    Priority:
    1) Installed package payload: aps_cli/payload/agnostic-prompt-standard
    2) Repo checkout: ../../../../skill/agnostic-prompt-standard (relative to this file)
    """
    here = Path(__file__).resolve().parent
    packaged = here / "payload" / SKILL_ID
    if packaged.is_dir():
        return packaged

    # repo fallback
    repo_root = Path(__file__).resolve().parents[4]
    dev = repo_root / "skill" / SKILL_ID
    if dev.is_dir():
        return dev

    raise FileNotFoundError(
        "APS payload not found. (Did you run tools/sync_payload.py before building?)"
    )


def load_platforms(skill_dir: Path) -> list[Platform]:
    platforms_dir = skill_dir / "platforms"
    out: list[Platform] = []
    for entry in platforms_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("_"):
            continue
        manifest_path = entry / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        platform_id = manifest.get("platformId", entry.name)
        display_name = manifest.get("displayName", entry.name)
        adapter_version = manifest.get("adapterVersion")
        detection_markers = tuple(manifest.get("detectionMarkers", []))
        out.append(
            Platform(
                platform_id=platform_id,
                display_name=display_name,
                adapter_version=adapter_version,
                detection_markers=detection_markers,
            )
        )
    out.sort(key=lambda p: p.display_name.lower())
    return out


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def remove_dir(p: Path) -> None:
    shutil.rmtree(p, ignore_errors=True)


def copy_dir(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)


def copy_template_tree(
    src_dir: Path,
    dst_root: Path,
    *,
    force: bool = False,
    filter_fn: Optional[Callable[[str], bool]] = None,
) -> list[str]:
    """Copy template files individually with optional filtering.

    Args:
        src_dir: Source templates directory
        dst_root: Destination root directory
        force: Overwrite existing files
        filter_fn: Callback (rel_path: str) -> bool; return False to skip

    Returns:
        List of relative paths that were copied
    """
    copied: list[str] = []
    for src_file in src_dir.rglob("*"):
        if not src_file.is_file():
            continue
        rel_path = src_file.relative_to(src_dir)
        rel_str = str(rel_path).replace("\\", "/")
        if filter_fn and not filter_fn(rel_str):
            continue
        dst_file = dst_root / rel_path
        if dst_file.exists() and not force:
            continue
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        copied.append(rel_str)
    return copied
