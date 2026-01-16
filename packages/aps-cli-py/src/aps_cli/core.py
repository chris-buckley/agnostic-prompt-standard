from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

SKILL_ID = "agnostic-prompt-standard"


@dataclass(frozen=True)
class Platform:
    platform_id: str
    display_name: str
    adapter_version: Optional[str]
    has_templates: bool


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
    has_instructions = (gh / "copilot-instructions.md").exists() or (gh / "instructions").exists()
    if has_agents or has_prompts or has_instructions:
        return "vscode-copilot"
    return None


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

    raise FileNotFoundError("APS payload not found. (Did you run tools/sync_payload.py before building?)")


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
        has_templates = (entry / "templates").is_dir()
        out.append(
            Platform(
                platform_id=platform_id,
                display_name=display_name,
                adapter_version=adapter_version,
                has_templates=has_templates,
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


def copy_templates(templates_dir: Path, workspace_root: Path, force: bool) -> dict[str, list[str]]:
    """Merge-copy templates_dir into workspace_root.

    Returns {"copied": [...], "skipped": [...]}
    """
    copied: list[str] = []
    skipped: list[str] = []

    for root, dirs, files in os.walk(templates_dir):
        root_path = Path(root)
        rel_root = root_path.relative_to(templates_dir)
        for d in dirs:
            ensure_dir(workspace_root / rel_root / d)
        for f in files:
            src = root_path / f
            rel = (rel_root / f)
            dst = workspace_root / rel
            ensure_dir(dst.parent)
            if dst.exists() and not force:
                skipped.append(str(rel))
                continue
            shutil.copy2(src, dst)
            copied.append(str(rel))

    return {"copied": copied, "skipped": skipped}
