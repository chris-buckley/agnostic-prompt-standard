from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import questionary
import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .core import (
    SKILL_ID,
    copy_dir,
    copy_templates,
    default_personal_skill_path,
    default_project_skill_path,
    ensure_dir,
    find_repo_root,
    infer_platform_id,
    is_tty,
    load_platforms,
    remove_dir,
    resolve_payload_skill_dir,
)

app = typer.Typer(add_completion=False)
console = Console()


def _norm_platform(platform: Optional[str]) -> str:
    if not platform:
        return ""
    if platform.lower() == "none":
        return "none"
    return platform


@app.command()
def init(
    root: Optional[str] = typer.Option(
        None,
        "--root",
        help="Workspace root to install templates / project skill under (defaults to repo root or cwd)",
    ),
    repo: bool = typer.Option(False, "--repo", help="Force install as project skill (workspace/.github/skills or workspace/.claude/skills)"),
    personal: bool = typer.Option(False, "--personal", help="Force install as personal skill (~/.copilot/skills or ~/.claude/skills)"),
    platform: Optional[str] = typer.Option(None, "--platform", help='Platform adapter to apply (default: inferred; use "none" for skill only)'),
    templates: bool = typer.Option(False, "--templates", help="Also install platform templates (agents / AGENTS.md / .github/*), if available"),
    templates_root: Optional[str] = typer.Option(None, "--templates-root", help="Workspace root for templates when installing personal skill"),
    claude: bool = typer.Option(False, "--claude", help="Use Claude platform .claude/skills paths (instead of .github/skills + ~/.copilot/skills)"),
    yes: bool = typer.Option(False, "--yes", help="Non-interactive: accept inferred/default choices"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing skill/templates"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the plan only, do not write files"),
):
    """Install APS into a repo (.github/skills/...) or as a personal skill (~/.copilot/skills/...)."""

    if repo and personal:
        raise typer.BadParameter("Use at most one of --repo or --personal")

    payload_skill_dir = resolve_payload_skill_dir()

    repo_root = find_repo_root(Path.cwd())
    workspace_root = Path(root).expanduser().resolve() if root else (repo_root or Path.cwd().resolve())

    inferred_platform = infer_platform_id(workspace_root)
    platform_id = _norm_platform(platform) or (inferred_platform or "")

    install_scope = "repo" if repo else "personal" if personal else ("repo" if repo_root else "personal")

    # Defaults
    install_templates = templates or (platform_id not in ("", "none"))
    chosen_templates_root: Optional[Path] = None

    if not yes and is_tty():
        # Scope
        if not (repo or personal):
            install_scope = questionary.select(
                "Where should APS be installed?",
                choices=[
                    questionary.Choice(
                        title=f"Project skill in this repo ({repo_root})" if repo_root else "Project skill (choose workspace)",
                        value="repo",
                    ),
                    questionary.Choice(
                        title=f"Personal skill ({default_personal_skill_path(claude=claude)})",
                        value="personal",
                    ),
                ],
                default="repo" if repo_root else "personal",
            ).ask()
            assert isinstance(install_scope, str)

        # Workspace root (only necessary for repo scope or for applying templates)
        if install_scope == "repo" and (not root and not repo_root):
            root_answer = questionary.text("Workspace root path:", default=str(workspace_root)).ask()
            workspace_root = Path(str(root_answer)).expanduser().resolve()

        # Platform selection
        if not platform:
            platforms = load_platforms(payload_skill_dir)
            choices = [questionary.Choice(title="None (skill only)", value="none")]
            if inferred_platform:
                choices.insert(0, questionary.Choice(title=f"Auto-detected: {inferred_platform}", value=inferred_platform))
            for p in platforms:
                if p.platform_id == inferred_platform:
                    continue
                choices.append(questionary.Choice(title=f"{p.display_name} ({p.platform_id})", value=p.platform_id))

            platform_id = questionary.select("Select a platform adapter to apply:", choices=choices, default=inferred_platform or "none").ask()
            assert isinstance(platform_id, str)

        install_templates = False
        if platform_id != "none":
            install_templates = questionary.confirm("Apply platform templates to the workspace?", default=True).ask()

        force = questionary.confirm("Overwrite existing files if they exist?", default=force).ask()
        dry_run = questionary.confirm("Dry run (print plan only)?", default=dry_run).ask()

    # Determine where templates should be applied.
    if install_templates and platform_id not in ("", "none"):
        if install_scope == "repo":
            chosen_templates_root = workspace_root
        else:
            if templates_root:
                chosen_templates_root = Path(templates_root).expanduser().resolve()
            elif repo_root:
                chosen_templates_root = repo_root
            else:
                chosen_templates_root = Path.cwd().resolve()

    # Compute destinations
    skill_dest = (
        default_project_skill_path(workspace_root, claude=claude)
        if install_scope == "repo"
        else default_personal_skill_path(claude=claude)
    )

    templates_src = (
        payload_skill_dir / "platforms" / platform_id / "templates"
        if platform_id not in ("", "none")
        else None
    )

    plan = {
        "install_scope": install_scope,
        "workspace_root": str(workspace_root),
        "templates_root": str(chosen_templates_root) if chosen_templates_root else None,
        "platform_id": platform_id or None,
        "claude": bool(claude),
        "skill_source": str(payload_skill_dir),
        "skill_dest": str(skill_dest),
        "install_templates": bool(
            install_templates
            and chosen_templates_root is not None
            and templates_src is not None
            and templates_src.is_dir()
        ),
        "templates_source": str(templates_src) if templates_src else None,
        "force": bool(force),
    }

    if dry_run:
        console.print_json(json.dumps({"plan": plan}, indent=2))
        raise typer.Exit(code=0)

    # Install skill
    if skill_dest.exists():
        if not force:
            raise typer.BadParameter(f"Destination already exists: {skill_dest}. Re-run with --force.")
        remove_dir(skill_dest)

    ensure_dir(skill_dest.parent)
    copy_dir(payload_skill_dir, skill_dest)

    templates_summary = None
    if plan["install_templates"] and chosen_templates_root and templates_src and templates_src.is_dir():
        templates_summary = copy_templates(templates_src, chosen_templates_root, force=force)

    console.print("[green]APS installed.[/green]")
    console.print(f"  Skill: {skill_dest}")
    if templates_summary:
        console.print(f"  Templates copied: {len(templates_summary['copied'])}")
        if templates_summary["skipped"]:
            console.print(f"  Templates skipped (existing): {len(templates_summary['skipped'])}")


@app.command()
def doctor(json_out: bool = typer.Option(False, "--json", help="Machine-readable output")):
    """Check whether APS is installed and infer platform settings."""
    repo_root = find_repo_root(Path.cwd())
    workspace_root = repo_root or Path.cwd().resolve()

    # Check both Copilot and Claude locations.
    project_skill = default_project_skill_path(workspace_root, claude=False)
    project_skill_claude = default_project_skill_path(workspace_root, claude=True)
    personal_skill = default_personal_skill_path(claude=False)
    personal_skill_claude = default_personal_skill_path(claude=True)

    out = {
        "cwd": str(Path.cwd()),
        "repo_root": str(repo_root) if repo_root else None,
        "inferred_platform": infer_platform_id(workspace_root),
        "project_skill": {"path": str(project_skill), "installed": (project_skill / "SKILL.md").exists()},
        "project_skill_claude": {"path": str(project_skill_claude), "installed": (project_skill_claude / "SKILL.md").exists()},
        "personal_skill": {"path": str(personal_skill), "installed": (personal_skill / "SKILL.md").exists()},
        "personal_skill_claude": {"path": str(personal_skill_claude), "installed": (personal_skill_claude / "SKILL.md").exists()},
    }

    if json_out:
        console.print_json(json.dumps(out, indent=2))
        raise typer.Exit(code=0)

    console.print("[bold]APS doctor[/bold]")
    console.print(f"  cwd: {out['cwd']}")
    console.print(f"  repo_root: {out['repo_root'] or '(none)'}")
    console.print(f"  inferred_platform: {out['inferred_platform'] or '(none)'}")
    console.print(f"  project skill: {'OK' if out['project_skill']['installed'] else 'missing'} — {out['project_skill']['path']}")
    console.print(f"  project skill (claude): {'OK' if out['project_skill_claude']['installed'] else 'missing'} — {out['project_skill_claude']['path']}")
    console.print(f"  personal skill: {'OK' if out['personal_skill']['installed'] else 'missing'} — {out['personal_skill']['path']}")
    console.print(f"  personal skill (claude): {'OK' if out['personal_skill_claude']['installed'] else 'missing'} — {out['personal_skill_claude']['path']}")


@app.command()
def platforms():
    """List available platform adapters bundled with this APS release."""
    payload_skill_dir = resolve_payload_skill_dir()
    platforms = load_platforms(payload_skill_dir)

    table = Table(title="APS Platform Adapters")
    table.add_column("platform_id")
    table.add_column("display_name")
    table.add_column("templates")
    table.add_column("adapter_version")

    for p in platforms:
        table.add_row(p.platform_id, p.display_name, "yes" if p.has_templates else "no", p.adapter_version or "")

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
