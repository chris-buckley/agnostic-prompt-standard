from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from .schemas import safe_parse_platform_manifest, normalize_detection_marker

SKILL_ID = "agnostic-prompt-standard"

# Explicit ordering for known adapters in UI
DEFAULT_ADAPTER_ORDER: tuple[str, ...] = ("vscode-copilot", "claude-code", "opencode")

KnownAdapterId = Literal["vscode-copilot", "claude-code", "opencode"]


@dataclass(frozen=True)
class DetectionMarker:
    """A marker file or directory used to detect a platform."""

    kind: Literal["file", "dir"]
    label: str
    rel_path: str


@dataclass(frozen=True)
class Platform:
    """Information about a platform adapter."""

    platform_id: str
    display_name: str
    adapter_version: Optional[str]
    detection_markers: tuple[DetectionMarker, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AdapterDetection:
    """Result of detecting a platform adapter in a workspace."""

    platform_id: str
    detected: bool
    reasons: tuple[str, ...]


def is_tty() -> bool:
    """Check if running in interactive terminal."""
    try:
        return bool(os.isatty(0) and os.isatty(1))
    except Exception:
        return False


def find_repo_root(start_dir: Path) -> Optional[Path]:
    """Find git repository root by walking up from start directory."""
    cur = start_dir.resolve()
    while True:
        if (cur / ".git").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def pick_workspace_root(cli_root: Optional[str]) -> Optional[Path]:
    """Resolve workspace root from CLI option or auto-detect."""
    if cli_root:
        return Path(cli_root).expanduser().resolve()
    return find_repo_root(Path.cwd())


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


def is_claude_platform(platform_id: str) -> bool:
    """Check if platform uses Claude-specific paths."""
    return platform_id == "claude-code"


def compute_skill_destinations(
    scope: Literal["repo", "personal"],
    workspace_root: Optional[Path],
    selected_platforms: list[str],
) -> list[Path]:
    """Compute skill installation destinations based on selected platforms.

    Args:
        scope: Installation scope (repo or personal)
        workspace_root: Workspace root path (required for repo scope)
        selected_platforms: List of selected platform IDs

    Returns:
        List of unique destination paths
    """
    wants_claude = any(is_claude_platform(p) for p in selected_platforms)
    wants_non_claude = any(not is_claude_platform(p) for p in selected_platforms)

    # Default to non-Claude location if no adapters selected
    include_claude = wants_claude
    include_non_claude = wants_non_claude or len(selected_platforms) == 0

    if scope == "repo":
        if not workspace_root:
            raise ValueError("Repo install selected but no workspace root found.")
        dests: list[Path] = []
        if include_non_claude:
            dests.append(default_project_skill_path(workspace_root, claude=False))
        if include_claude:
            dests.append(default_project_skill_path(workspace_root, claude=True))
        return _unique_paths(dests)

    dests = []
    if include_non_claude:
        dests.append(default_personal_skill_path(claude=False))
    if include_claude:
        dests.append(default_personal_skill_path(claude=True))
    return _unique_paths(dests)


def _unique_paths(paths: list[Path]) -> list[Path]:
    """Remove duplicate paths while preserving order."""
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def infer_platform_id(workspace_root: Path) -> Optional[str]:
    """Infer platform ID based on workspace directory structure (legacy)."""
    gh = workspace_root / ".github"
    has_agents = (gh / "agents").exists()
    has_prompts = (gh / "prompts").exists()
    has_instructions = (gh / "copilot-instructions.md").exists() or (
        gh / "instructions"
    ).exists()
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

    raise FileNotFoundError(
        "APS payload not found. (Did you run tools/sync_payload.py before building?)"
    )


def load_platforms(skill_dir: Path) -> list[Platform]:
    """Load all platform adapters from the skill's platforms directory."""
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
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Validate with Pydantic
        manifest, error = safe_parse_platform_manifest(raw)
        if error:
            print(
                f"Warning: Invalid platform manifest at {manifest_path}: {error}",
                file=sys.stderr,
            )
            # Fall back to partial extraction
            platform_id = raw.get("platformId", entry.name)
            display_name = raw.get("displayName", entry.name)
            adapter_version = raw.get("adapterVersion")
            detection_markers: tuple[DetectionMarker, ...] = ()
        else:
            assert manifest is not None
            platform_id = manifest.platform_id
            display_name = manifest.display_name
            adapter_version = manifest.adapter_version
            # Get normalized detection markers from manifest
            detection_markers = tuple(
                DetectionMarker(
                    kind=m.kind,  # type: ignore[arg-type]
                    label=m.label,
                    rel_path=m.rel_path,
                )
                for m in manifest.detection_markers
            )

        out.append(
            Platform(
                platform_id=platform_id,
                display_name=display_name,
                adapter_version=adapter_version,
                detection_markers=detection_markers,
            )
        )

    return out


def sort_platforms_for_ui(platforms: list[Platform]) -> list[Platform]:
    """Sort platforms with known adapters first in defined order."""
    known_order = {pid: i for i, pid in enumerate(DEFAULT_ADAPTER_ORDER)}
    known = [p for p in platforms if p.platform_id in known_order]
    remaining = [p for p in platforms if p.platform_id not in known_order]

    known.sort(key=lambda p: known_order[p.platform_id])
    remaining.sort(key=lambda p: p.display_name.lower())

    return known + remaining


def _marker_exists(workspace_root: Path, marker: DetectionMarker) -> bool:
    """Check if a marker file or directory exists."""
    full = workspace_root / marker.rel_path
    if marker.kind == "dir":
        return full.is_dir()
    return full.exists()


def detect_adapters(
    workspace_root: Path, platforms: list[Platform]
) -> dict[str, AdapterDetection]:
    """Detect which platform adapters are present in a workspace.

    Args:
        workspace_root: Workspace root directory
        platforms: List of platforms with detection markers

    Returns:
        Dict mapping platform IDs to detection results
    """
    out: dict[str, AdapterDetection] = {}

    for platform in platforms:
        reasons: list[str] = []
        for marker in platform.detection_markers:
            if _marker_exists(workspace_root, marker):
                reasons.append(marker.label)

        out[platform.platform_id] = AdapterDetection(
            platform_id=platform.platform_id,
            detected=len(reasons) > 0,
            reasons=tuple(reasons),
        )

    return out


def format_detection_label(detection: AdapterDetection) -> str:
    """Format a detection result as a label suffix."""
    if not detection.detected:
        return ""
    return " (detected)"


def detect_platforms(workspace_root: Path, skill_dir: Path) -> list[str]:
    """Detect all platforms with markers present in workspace (legacy API).

    Args:
        workspace_root: Path to workspace root
        skill_dir: Path to skill directory with platform manifests

    Returns:
        List of detected platform IDs
    """
    platforms = load_platforms(skill_dir)
    detections = detect_adapters(workspace_root, platforms)
    return [pid for pid, det in detections.items() if det.detected]


def ensure_dir(p: Path) -> None:
    """Ensure a directory exists, creating it recursively if needed."""
    p.mkdir(parents=True, exist_ok=True)


def remove_dir(p: Path) -> None:
    """Remove a directory recursively."""
    shutil.rmtree(p, ignore_errors=True)


def copy_dir(src: Path, dst: Path) -> None:
    """Copy a directory recursively."""
    shutil.copytree(src, dst)


def list_files_recursive(root_dir: Path) -> list[Path]:
    """Recursively list all files in a directory."""
    results: list[Path] = []
    for item in root_dir.rglob("*"):
        if item.is_file():
            results.append(item)
    return results


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