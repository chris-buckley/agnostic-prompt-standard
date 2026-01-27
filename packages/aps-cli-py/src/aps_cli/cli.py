from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import questionary
import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .core import (
    AdapterDetection,
    Platform,
    compute_skill_destinations,
    copy_dir,
    copy_template_tree,
    default_personal_skill_path,
    default_project_skill_path,
    detect_adapters,
    ensure_dir,
    find_repo_root,
    format_detection_label,
    is_claude_platform,
    is_tty,
    list_files_recursive,
    load_platforms,
    pick_workspace_root,
    remove_dir,
    resolve_payload_skill_dir,
    sort_platforms_for_ui,
    SKILL_ID,
)

app = typer.Typer(add_completion=False)
console = Console()

InstallScope = Literal["repo", "personal"]


def _normalize_platform_args(platforms: Optional[list[str]]) -> Optional[list[str]]:
    """Normalize platform arguments, handling 'none' and comma-separated values."""
    if not platforms:
        return None

    # Flatten comma-separated values
    raw: list[str] = []
    for v in platforms:
        raw.extend(s.strip() for s in v.split(",") if s.strip())

    if any(v.lower() == "none" for v in raw):
        return []

    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for v in raw:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _fmt_path(p: Path) -> str:
    """Format path for display, replacing home with ~."""
    home = str(Path.home())
    s = str(p)
    if s.startswith(home):
        return "~" + s[len(home) :]
    return s


def _select_all_choice_label() -> str:
    return "Select all adapters"


def _platform_display_name(platform: Platform) -> str:
    """Get display name for platform in UI."""
    return f"{platform.display_name} ({platform.platform_id})"


def _detection_for(
    platform_id: str, detections: dict[str, AdapterDetection]
) -> Optional[AdapterDetection]:
    """Get detection result for a platform ID."""
    return detections.get(platform_id)


@dataclass
class PlannedTemplateFile:
    rel_path: str
    dst_path: Path
    exists: bool
    will_write: bool


@dataclass
class PlannedPlatformTemplates:
    platform_id: str
    templates_dir: Path
    template_root: Path
    files: list[PlannedTemplateFile]


@dataclass
class PlannedSkillInstall:
    dst: Path
    exists: bool


@dataclass
class InitPlan:
    scope: InstallScope
    workspace_root: Optional[Path]
    selected_platforms: list[str]
    payload_skill_dir: Path
    skills: list[PlannedSkillInstall]
    templates: list[PlannedPlatformTemplates]


async def _plan_platform_templates(
    payload_skill_dir: Path,
    scope: InstallScope,
    workspace_root: Optional[Path],
    selected_platforms: list[str],
    force: bool,
) -> list[PlannedPlatformTemplates]:
    """Plan template files to be copied for selected platforms."""
    template_root = Path.home() if scope == "personal" else workspace_root
    if not template_root:
        return []

    plans: list[PlannedPlatformTemplates] = []

    for platform_id in selected_platforms:
        templates_dir = payload_skill_dir / "platforms" / platform_id / "templates"
        if not templates_dir.is_dir():
            continue

        all_files = list_files_recursive(templates_dir)

        def filter_fn(rel_path: str) -> bool:
            # Skip .github/** for personal installs
            if scope == "personal" and rel_path.startswith(".github"):
                return False
            return True

        files: list[PlannedTemplateFile] = []
        for src in all_files:
            rel_path = str(src.relative_to(templates_dir)).replace("\\", "/")
            if not filter_fn(rel_path):
                continue

            dst_path = template_root / rel_path
            exists = dst_path.exists()
            files.append(
                PlannedTemplateFile(
                    rel_path=rel_path,
                    dst_path=dst_path,
                    exists=exists,
                    will_write=not exists or force,
                )
            )

        plans.append(
            PlannedPlatformTemplates(
                platform_id=platform_id,
                templates_dir=templates_dir,
                template_root=template_root,
                files=files,
            )
        )

    return plans


def _render_plan(plan: InitPlan, force: bool) -> str:
    """Render plan as human-readable text."""
    lines: list[str] = []

    lines.append("Selected adapters:")
    if not plan.selected_platforms:
        lines.append("  (none)")
    else:
        for p in plan.selected_platforms:
            lines.append(f"  - {p}")
    lines.append("")

    lines.append("Skill install destinations:")
    for s in plan.skills:
        status = (
            "overwrite" if s.exists and force else "overwrite (needs confirmation)" if s.exists else "create"
        )
        lines.append(f"  - {_fmt_path(s.dst)}  [{status}]")
    lines.append("")

    if not plan.templates:
        lines.append("Platform templates: (none)")
        return "\n".join(lines)

    lines.append("Platform templates:")
    for t in plan.templates:
        will_write = sum(1 for f in t.files if f.will_write)
        skipped = len(t.files) - will_write
        skip_msg = f", {skipped} skipped (exists)" if skipped > 0 else ""
        lines.append(f"  - {t.platform_id}: {will_write} file(s) to write{skip_msg}")

        preview = [f for f in t.files if f.will_write][:30]
        for f in preview:
            lines.append(f"      {f.rel_path}")
        if will_write > 30:
            lines.append("      ...")

    return "\n".join(lines)


@app.command()
def init(
    root: Optional[str] = typer.Option(
        None,
        "--root",
        help="Workspace root to install project skill under (defaults to repo root or cwd)",
    ),
    repo: bool = typer.Option(
        False,
        "--repo",
        help="Force install as project skill (workspace/.github/skills or workspace/.claude/skills)",
    ),
    personal: bool = typer.Option(
        False,
        "--personal",
        help="Force install as personal skill (~/.copilot/skills or ~/.claude/skills)",
    ),
    platform: Optional[list[str]] = typer.Option(
        None,
        "--platform",
        help='Platform adapter(s) to apply (e.g. vscode-copilot, claude-code). Use "none" to skip.',
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Non-interactive: accept inferred/default choices"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the plan only, do not write files"
    ),
):
    """Install APS into a repo (.github/skills/...) or as a personal skill (~/.copilot/skills/...)."""

    if repo and personal:
        raise typer.BadParameter("Use at most one of --repo or --personal")

    payload_skill_dir = resolve_payload_skill_dir()
    repo_root = find_repo_root(Path.cwd())
    guessed_workspace_root = pick_workspace_root(root)

    platforms = load_platforms(payload_skill_dir)
    platforms = sort_platforms_for_ui(platforms)
    platforms_by_id = {p.platform_id: p for p in platforms}
    available_platform_ids = [p.platform_id for p in platforms]

    detections = (
        detect_adapters(guessed_workspace_root, platforms)
        if guessed_workspace_root
        else {}
    )

    cli_platforms = _normalize_platform_args(platform)

    # Determine platform selection
    selected_platforms: list[str] = []

    if cli_platforms is not None:
        selected_platforms = cli_platforms
    elif not yes and is_tty():
        choices = [
            questionary.Choice(title=_select_all_choice_label(), value="__all__")
        ]
        for platform_id in available_platform_ids:
            det = _detection_for(platform_id, detections)
            label = format_detection_label(det) if det else ""
            p = platforms_by_id[platform_id]
            checked = bool(det and det.detected)
            choices.append(
                questionary.Choice(
                    title=f"{_platform_display_name(p)}{label}",
                    value=platform_id,
                    checked=checked,
                )
            )

        picked = questionary.checkbox(
            "Select platform adapters to apply (press <space> to select, <a> to toggle all):",
            choices=choices,
        ).ask()

        if picked is None:
            raise typer.Abort()

        has_all = "__all__" in picked
        picked_platforms = [p for p in picked if p != "__all__"]

        if has_all and not picked_platforms:
            selected_platforms = list(available_platform_ids)
        else:
            selected_platforms = picked_platforms
    else:
        # Non-interactive defaults
        if yes and detections:
            selected_platforms = [
                pid for pid, det in detections.items() if det.detected
            ]
        else:
            selected_platforms = []

    # Determine scope
    install_scope: InstallScope = (
        "personal" if personal else "repo" if repo else ("repo" if repo_root else "personal")
    )
    workspace_root = guessed_workspace_root

    if not yes and is_tty():
        if not (repo or personal):
            # Compute likely destinations for display
            personal_bases: set[str] = set()
            wants_claude = any(is_claude_platform(p) for p in selected_platforms)
            wants_non_claude = (
                any(not is_claude_platform(p) for p in selected_platforms)
                or not selected_platforms
            )
            if wants_non_claude:
                base = str(default_personal_skill_path(claude=False)).replace(
                    SKILL_ID, ""
                )
                personal_bases.add(_fmt_path(Path(base)))
            if wants_claude:
                base = str(default_personal_skill_path(claude=True)).replace(
                    SKILL_ID, ""
                )
                personal_bases.add(_fmt_path(Path(base)))

            scope_answer = questionary.select(
                "Where should APS be installed?",
                choices=[
                    questionary.Choice(
                        title=(
                            f"Project skill in this repo ({_fmt_path(repo_root)})"
                            if repo_root
                            else "Project skill (choose a workspace folder)"
                        ),
                        value="repo",
                    ),
                    questionary.Choice(
                        title=f"Personal skill for your user ({', '.join(sorted(personal_bases))})",
                        value="personal",
                    ),
                ],
                default="repo" if repo_root else "personal",
            ).ask()
            assert scope_answer in ("repo", "personal")
            install_scope = scope_answer

        if install_scope == "repo" and not workspace_root:
            root_answer = questionary.text(
                "Workspace root path (the folder that contains .github/):",
                default=str(Path.cwd()),
            ).ask()
            workspace_root = Path(root_answer).expanduser().resolve()

    if install_scope == "repo" and not workspace_root:
        raise typer.BadParameter(
            "Repo install selected but no workspace root found. Run in a git repo or pass --root <path>."
        )

    # Compute destinations
    skill_dests = compute_skill_destinations(
        install_scope, workspace_root, selected_platforms
    )
    skills = [
        PlannedSkillInstall(dst=dst, exists=dst.exists()) for dst in skill_dests
    ]

    # Plan templates
    import asyncio

    templates = asyncio.get_event_loop().run_until_complete(
        _plan_platform_templates(
            payload_skill_dir, install_scope, workspace_root, selected_platforms, force
        )
    )

    plan = InitPlan(
        scope=install_scope,
        workspace_root=workspace_root,
        selected_platforms=selected_platforms,
        payload_skill_dir=payload_skill_dir,
        skills=skills,
        templates=templates,
    )

    if dry_run:
        console.print("Dry run — planned actions:\n")
        console.print(_render_plan(plan, force))
        return

    if not yes and is_tty():
        console.print(_render_plan(plan, force))
        console.print()

        if any(s.exists for s in skills) and not force:
            console.print(
                "Note: One or more skill destinations already exist. Confirming will overwrite them."
            )

        ok = questionary.confirm("Proceed with these changes?", default=False).ask()
        if not ok:
            console.print("Cancelled.")
            return
    else:
        # Non-interactive: refuse to overwrite without --force
        conflicts = [s for s in skills if s.exists]
        if conflicts and not force:
            first = conflicts[0]
            raise typer.BadParameter(
                f"Destination exists: {first.dst} (use --force to overwrite)"
            )

    # Execute skill copies
    for s in skills:
        if s.exists:
            if force or (is_tty() and not yes):
                remove_dir(s.dst)

        ensure_dir(s.dst.parent)
        copy_dir(payload_skill_dir, s.dst)
        console.print(f"Installed APS skill -> {s.dst}")

    # Copy templates
    for t in templates:

        def filter_fn(rel_path: str) -> bool:
            if install_scope == "personal" and rel_path.startswith(".github"):
                return False
            return True

        copied = copy_template_tree(
            t.templates_dir,
            t.template_root,
            force=force,
            filter_fn=filter_fn,
        )

        if copied:
            console.print(
                f"Installed {len(copied)} template file(s) for {t.platform_id}:"
            )
            for f in copied:
                console.print(f"  - {f}")

    console.print("\nNext steps:")
    console.print("- Ensure your IDE has Agent Skills enabled as needed.")
    for d in skill_dests:
        console.print(f"- Skill location: {d}")


@app.command()
def doctor(
    root: Optional[str] = typer.Option(
        None,
        "--root",
        help="Workspace root path (defaults to git repo root if found)",
    ),
    json_out: bool = typer.Option(False, "--json", help="Output JSON format"),
):
    """Check APS installation status + basic platform detection."""
    workspace_root = pick_workspace_root(root)

    payload_skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(payload_skill_dir)
    detected_adapters = (
        detect_adapters(workspace_root, platforms) if workspace_root else None
    )

    # Build installations list matching Node structure
    installations: list[dict] = []

    if workspace_root:
        repo_skill = default_project_skill_path(workspace_root, claude=False)
        repo_skill_claude = default_project_skill_path(workspace_root, claude=True)
        installations.append(
            {
                "scope": "repo",
                "path": str(repo_skill),
                "installed": (repo_skill / "SKILL.md").exists(),
            }
        )
        installations.append(
            {
                "scope": "repo (claude)",
                "path": str(repo_skill_claude),
                "installed": (repo_skill_claude / "SKILL.md").exists(),
            }
        )

    personal_skill = default_personal_skill_path(claude=False)
    personal_skill_claude = default_personal_skill_path(claude=True)
    installations.append(
        {
            "scope": "personal",
            "path": str(personal_skill),
            "installed": (personal_skill / "SKILL.md").exists(),
        }
    )
    installations.append(
        {
            "scope": "personal (claude)",
            "path": str(personal_skill_claude),
            "installed": (personal_skill_claude / "SKILL.md").exists(),
        }
    )

    # Format detected_adapters for JSON output
    adapters_out = None
    if detected_adapters:
        adapters_out = {
            pid: {
                "platformId": det.platform_id,
                "detected": det.detected,
                "reasons": list(det.reasons),
            }
            for pid, det in detected_adapters.items()
        }

    result = {
        "workspace_root": str(workspace_root) if workspace_root else None,
        "detected_adapters": adapters_out,
        "installations": installations,
    }

    if json_out:
        console.print_json(json.dumps(result, indent=2))
        return

    console.print("APS Doctor")
    console.print("----------")
    console.print(f"Workspace root: {workspace_root or '(not detected)'}")

    if detected_adapters:
        detected = [d for d in detected_adapters.values() if d.detected]
        if detected:
            console.print(
                f"Detected adapters: {', '.join(d.platform_id for d in detected)}"
            )
        else:
            console.print("Detected adapters: (none)")
    console.print("")

    console.print("Installed skills:")
    for inst in installations:
        status = "✓" if inst["installed"] else "✗"
        console.print(f"- {inst['scope']}: {inst['path']} {status}")


@app.command()
def platforms():
    """List available platform adapters bundled with this APS release."""
    payload_skill_dir = resolve_payload_skill_dir()
    plats = load_platforms(payload_skill_dir)
    plats = sort_platforms_for_ui(plats)

    table = Table(title="APS Platform Adapters")
    table.add_column("platform_id")
    table.add_column("display_name")
    table.add_column("adapter_version")

    for p in plats:
        table.add_row(p.platform_id, p.display_name, p.adapter_version or "")

    console.print(table)


@app.command()
def version():
    """Print CLI version."""
    console.print(__version__)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()