from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Optional

try:
    import questionary
except ModuleNotFoundError:
    class _UnavailablePrompt:
        def ask(self):
            raise RuntimeError(
                "questionary is required for interactive APS prompts. Install APS with its optional dependencies or use explicit flags / --yes."
            )


    class _QuestionaryChoice:
        def __init__(self, title: str, value):
            self.title = title
            self.value = value


    class _QuestionaryFallback:
        Choice = _QuestionaryChoice

        @staticmethod
        def select(*args, **kwargs):
            return _UnavailablePrompt()

        @staticmethod
        def checkbox(*args, **kwargs):
            return _UnavailablePrompt()

        @staticmethod
        def text(*args, **kwargs):
            return _UnavailablePrompt()

        @staticmethod
        def confirm(*args, **kwargs):
            return _UnavailablePrompt()


    questionary = _QuestionaryFallback()

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .update import (
    APS_SKIP_SELF_UPDATE_ENV,
    PackageUpdateStatus,
    SkillUpdateTarget,
    TemplateUpdateTarget,
    apply_skill_updates,
    collect_skill_targets,
    collect_template_targets,
    apply_template_updates,
    compare_semver,
    detect_python_runtime_mode,
    fetch_latest_cli_version,
    maybe_self_update,
    read_skill_version,
)
from .core import (
    AdapterDetection,
    Platform,
    clean_old_platform_templates,
    compute_install_families,
    compute_skill_destinations,
    copy_template_tree,
    default_personal_skill_path,
    default_project_skill_path,
    detect_adapters,
    find_repo_root,
    format_detection_label,
    is_tty,
    list_files_recursive,
    load_platforms,
    pick_workspace_root,
    replace_dir_with_copy,
    resolve_payload_skill_dir,
    sort_platforms_for_ui,
)

app = typer.Typer(add_completion=False)
console = Console()


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Print CLI version",
        is_eager=True,
    ),
) -> None:
    """Root command for the APS CLI."""

    if version:
        typer.echo(__version__)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help(), err=True)
        raise typer.Exit(code=2)


InstallScope = Literal["repo", "personal"]
ToolIntent = Literal["native", "mcp", "mixed", "agnostic"]


def _normalize_platform_args(platforms: Optional[list[str]]) -> Optional[list[str]]:
    if not platforms:
        return None

    raw: list[str] = []
    for value in platforms:
        raw.extend(item.strip() for item in value.split(",") if item.strip())

    if any(value.lower() == "none" for value in raw):
        return []

    seen: set[str] = set()
    out: list[str] = []
    for value in raw:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _fmt_path(p: Path) -> str:
    home = str(Path.home())
    s = str(p)
    if s.startswith(home):
        return "~" + s[len(home) :]
    return s


def _select_all_choice_label() -> str:
    return "Select all adapters"


def _platform_display_name(platform: Platform) -> str:
    return f"{platform.display_name} ({platform.platform_id})"


def _detection_for(
    platform_id: str, detections: dict[str, AdapterDetection]
) -> Optional[AdapterDetection]:
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
    tool_intent: Optional[ToolIntent]
    selected_platforms: list[str]
    payload_skill_dir: Path
    skills: list[PlannedSkillInstall]
    templates: list[PlannedPlatformTemplates]


def _default_tool_intent(detections: dict[str, AdapterDetection]) -> ToolIntent:
    return "native" if any(d.detected for d in detections.values()) else "agnostic"


def _default_selected_platforms_for_tool_intent(
    available_platform_ids: list[str],
    detections: dict[str, AdapterDetection],
    tool_intent: ToolIntent,
) -> list[str]:
    detected_concrete = [
        platform_id
        for platform_id in available_platform_ids
        if platform_id != "generic"
        and bool(detections.get(platform_id) and detections[platform_id].detected)
    ]
    include_generic = "generic" in available_platform_ids

    if tool_intent == "native":
        return detected_concrete
    if tool_intent == "agnostic":
        return ["generic"] if include_generic else []
    return list(
        dict.fromkeys(detected_concrete + (["generic"] if include_generic else []))
    )


def _format_tool_intent(tool_intent: ToolIntent) -> str:
    labels = {
        "native": "native host tools",
        "mcp": "external MCP tools",
        "mixed": "mixed native + MCP tools",
        "agnostic": "tool-agnostic / no fixed tool surface",
    }
    return labels[tool_intent]


def _normalize_declared_path(path_str: str) -> str:
    return path_str[2:] if path_str.startswith("./") else path_str


def _declared_path_scope(path_str: str) -> Literal["workspace", "user", "absolute"]:
    if path_str == "~" or path_str.startswith("~/") or path_str.startswith("~\\"):
        return "user"
    if Path(path_str).is_absolute():
        return "absolute"
    return "workspace"


def _build_mcp_validation(
    workspace_root: Optional[Path], platforms: list[Platform]
) -> dict:
    checks: list[dict] = []

    for platform in platforms:
        for declared in dict.fromkeys(platform.mcp_config_paths):
            normalized = _normalize_declared_path(declared)
            scope = _declared_path_scope(normalized)

            if scope == "workspace" and workspace_root is None:
                checks.append(
                    {
                        "platform_id": platform.platform_id,
                        "path": declared,
                        "resolved_path": None,
                        "scope": scope,
                        "exists": None,
                        "status": "skipped",
                        "reason": "workspace root not detected",
                    }
                )
                continue

            if scope == "workspace":
                resolved_path = str((workspace_root or Path(".")) / normalized)
            elif scope == "user":
                resolved_path = str(Path(normalized).expanduser())
            else:
                resolved_path = normalized

            exists = Path(resolved_path).exists()
            checks.append(
                {
                    "platform_id": platform.platform_id,
                    "path": declared,
                    "resolved_path": resolved_path,
                    "scope": scope,
                    "exists": exists,
                    "status": "present" if exists else "missing",
                }
            )

    return {"enabled": True, "checks": checks}


def _plan_platform_templates(
    payload_skill_dir: Path,
    scope: InstallScope,
    workspace_root: Optional[Path],
    selected_platforms: list[str],
    force: bool,
) -> list[PlannedPlatformTemplates]:
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
    lines: list[str] = []

    if plan.tool_intent is not None:
        lines.append(f"Tool source intent: {_format_tool_intent(plan.tool_intent)}")
        lines.append("")

    lines.append("Selected adapters:")
    if not plan.selected_platforms:
        lines.append("  (none)")
    else:
        for platform_id in plan.selected_platforms:
            lines.append(f"  - {platform_id}")
    lines.append("")

    lines.append("Skill install destinations:")
    for skill in plan.skills:
        status = (
            "overwrite"
            if skill.exists and force
            else "overwrite (needs confirmation)"
            if skill.exists
            else "create"
        )
        lines.append(f"  - {_fmt_path(skill.dst)}  [{status}]")
    lines.append("")

    if not plan.templates:
        lines.append("Platform templates: (none)")
        return "\n".join(lines)

    lines.append("Platform templates:")
    for template in plan.templates:
        will_write = sum(1 for file in template.files if file.will_write)
        skipped = len(template.files) - will_write
        skip_msg = f", {skipped} skipped (exists)" if skipped > 0 else ""
        lines.append(
            f"  - {template.platform_id}: {will_write} file(s) to write{skip_msg}"
        )

        preview = [file for file in template.files if file.will_write][:30]
        for file in preview:
            lines.append(f"      {file.rel_path}")
        if will_write > 30:
            lines.append("      ...")

    return "\n".join(lines)


def _render_empty_platform_warning() -> str:
    return (
        "Note: No platform adapters selected. Only the APS skill will be installed.\n"
        "      Templates will not be copied. Use --platform <id> to include platform templates."
    )


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
        help='Platform adapter(s) to apply (e.g. vscode-copilot, claude-code). Use "none" to skip platform templates.',
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

    payload_skill_dir = resolve_payload_skill_dir()
    repo_root = find_repo_root(Path.cwd())
    guessed_workspace_root = pick_workspace_root(root)

    platforms = sort_platforms_for_ui(load_platforms(payload_skill_dir))
    platforms_by_id = {platform.platform_id: platform for platform in platforms}
    available_platform_ids = [platform.platform_id for platform in platforms]

    detections = (
        detect_adapters(guessed_workspace_root, platforms)
        if guessed_workspace_root
        else {}
    )

    cli_platforms = _normalize_platform_args(platform)

    tool_intent: Optional[ToolIntent] = None
    selected_platforms: list[str] = []

    if cli_platforms is not None:
        selected_platforms = cli_platforms
    elif not yes and is_tty():
        tool_intent_answer = questionary.select(
            "Which tool surface best matches this workspace?",
            choices=[
                questionary.Choice(title="Native host tools only", value="native"),
                questionary.Choice(title="External tools only (MCP / declarations)", value="mcp"),
                questionary.Choice(title="Mixed native + external tools", value="mixed"),
                questionary.Choice(title="Tool-agnostic / no fixed tool surface", value="agnostic"),
            ],
            default=_default_tool_intent(detections),
        ).ask()
        assert tool_intent_answer in ("native", "mcp", "mixed", "agnostic")
        tool_intent = tool_intent_answer

        default_selected = set(
            _default_selected_platforms_for_tool_intent(
                available_platform_ids, detections, tool_intent
            )
        )

        choices = [
            questionary.Choice(title=_select_all_choice_label(), value="__all__")
        ]
        for platform_id in available_platform_ids:
            det = _detection_for(platform_id, detections)
            label = format_detection_label(det) if det else ""
            platform_info = platforms_by_id[platform_id]
            choices.append(
                questionary.Choice(
                    title=f"{_platform_display_name(platform_info)}{label}",
                    value=platform_id,
                    checked=platform_id in default_selected,
                )
            )

        picked = questionary.checkbox(
            "Select platform adapters to apply (press <space> to select, <a> to toggle all):",
            choices=choices,
        ).ask()

        if picked is None:
            raise typer.Abort()

        has_all = "__all__" in picked
        picked_platforms = [platform_id for platform_id in picked if platform_id != "__all__"]

        if has_all and not picked_platforms:
            selected_platforms = list(available_platform_ids)
        else:
            selected_platforms = picked_platforms
    else:
        if yes and detections:
            selected_platforms = [
                platform_id
                for platform_id, detection in detections.items()
                if detection.detected
            ]
        else:
            selected_platforms = []

    install_scope: InstallScope = (
        "personal" if personal else "repo" if repo else ("repo" if repo_root else "personal")
    )
    workspace_root = guessed_workspace_root

    if not yes and is_tty():
        if not (repo or personal):
            include_claude, include_non_claude = compute_install_families(selected_platforms)
            project_paths: list[str] = []
            personal_paths: list[str] = []
            if include_non_claude:
                if repo_root:
                    project_paths.append(
                        _fmt_path(default_project_skill_path(repo_root, claude=False))
                    )
                personal_paths.append(
                    _fmt_path(default_personal_skill_path(claude=False))
                )
            if include_claude:
                if repo_root:
                    project_paths.append(
                        _fmt_path(default_project_skill_path(repo_root, claude=True))
                    )
                personal_paths.append(
                    _fmt_path(default_personal_skill_path(claude=True))
                )

            project_display = ", ".join(dict.fromkeys(project_paths))
            personal_display = ", ".join(dict.fromkeys(personal_paths))

            scope_answer = questionary.select(
                "Where should APS be installed?",
                choices=[
                    questionary.Choice(
                        title=(
                            f"Local (project)    {project_display}"
                            if repo_root
                            else "Local (project)    choose a workspace folder"
                        ),
                        value="repo",
                    ),
                    questionary.Choice(
                        title=f"Global (personal)  {personal_display}",
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

    skill_dests = compute_skill_destinations(
        install_scope, workspace_root, selected_platforms
    )
    skills = [PlannedSkillInstall(dst=dst, exists=dst.exists()) for dst in skill_dests]

    templates = _plan_platform_templates(
        payload_skill_dir, install_scope, workspace_root, selected_platforms, force
    )

    plan = InitPlan(
        scope=install_scope,
        workspace_root=workspace_root,
        tool_intent=tool_intent,
        selected_platforms=selected_platforms,
        payload_skill_dir=payload_skill_dir,
        skills=skills,
        templates=templates,
    )

    if dry_run:
        console.print("Dry run — planned actions:\n")
        console.print(_render_plan(plan, force), markup=False)
        if not plan.selected_platforms:
            console.print()
            console.print(_render_empty_platform_warning())
        return

    if not yes and is_tty():
        console.print(_render_plan(plan, force), markup=False)
        console.print()

        if not plan.selected_platforms:
            console.print(_render_empty_platform_warning())
            console.print()

        if any(skill.exists for skill in skills) and not force:
            console.print(
                "Note: One or more skill destinations already exist. Confirming will overwrite them."
            )

        ok = questionary.confirm("Proceed with these changes?", default=False).ask()
        if not ok:
            console.print("Cancelled.")
            return
    else:
        conflicts = [skill for skill in skills if skill.exists]
        if conflicts and not force:
            first = conflicts[0]
            raise typer.BadParameter(
                f"Destination exists: {first.dst} (use --force to overwrite)"
            )

    for skill in skills:
        replace_dir_with_copy(payload_skill_dir, skill.dst)
        console.print(f"Installed APS skill -> {skill.dst}")

    for template in templates:
        def filter_fn(rel_path: str) -> bool:
            if install_scope == "personal" and rel_path.startswith(".github"):
                return False
            return True

        removed = clean_old_platform_templates(template.template_root, template.platform_id, payload_skill_dir)
        if removed:
            console.print(f"Cleaned up {len(removed)} old template file(s) for {template.platform_id}")

        copied = copy_template_tree(
            template.templates_dir,
            template.template_root,
            force=force,
            filter_fn=filter_fn,
        )

        if copied:
            console.print(
                f"Installed {len(copied)} template file(s) for {template.platform_id}:"
            )
            for rel_path in copied:
                console.print(f"  - {rel_path}")

    console.print("\nNext steps:")
    console.print("- Ensure your IDE has Agent Skills enabled as needed.")
    for dest in skill_dests:
        console.print(f"- Skill location: {dest}")


def _render_update_report(
    package_status: PackageUpdateStatus,
    targets: list[SkillUpdateTarget],
    template_targets: list[TemplateUpdateTarget],
    *,
    check: bool,
    dry_run: bool,
    yes: bool,
) -> None:
    console.print("APS Update")
    console.print("----------")
    console.print(f"CLI package: {package_status.package_name}")
    console.print(f"Current CLI version: {package_status.current_version}")
    console.print(f"Bundled skill version: {package_status.payload_version}")

    if package_status.latest_version:
        latest_summary = (
            f"{package_status.latest_version} (newer release available)"
            if package_status.update_available
            else f"{package_status.latest_version} (already current)"
        )
        console.print(f"Latest registry version: {latest_summary}")
    else:
        console.print(
            f"Latest registry version: unavailable ({package_status.registry_error or 'unknown error'})"
        )

    console.print(f"Runtime mode: {package_status.runtime_mode}")

    if (
        package_status.update_available
        and os.environ.get(APS_SKIP_SELF_UPDATE_ENV) != "1"
        and not yes
        and not check
        and not dry_run
    ):
        console.print("")
        console.print("Note: The running CLI is older than the latest published release.")
        console.print(
            "      Re-run with pipx run --no-cache agnostic-prompt-aps update to refresh from the newest payload immediately."
        )

    console.print("")
    console.print("Skill installations:" if (check or dry_run) else "Skill installation results:")

    if not targets and not template_targets:
        console.print("- (none found)")
    elif targets:
        for target in targets:
            version_info = (
                f"{target.installed_version} -> {target.desired_version}"
                if target.installed_version
                else f"target {target.desired_version}"
            )
            console.print(
                f"- {target.scope}: {_fmt_path(target.path)} [{target.status}] ({version_info})",
                markup=False,
            )

    if template_targets:
        console.print("")
        console.print("Platform template updates:" if (check or dry_run) else "Platform template results:")
        for target in template_targets:
            summary = (
                f"({len(target.removed)} old removed, {len(target.copied)} new written)"
                if target.status == "updated"
                else f"({target.status})"
            )
            console.print(
                f"- {target.scope} templates ({target.platform_id}): {_fmt_path(target.template_root)} {summary}",
                markup=False,
            )


@app.command()
def doctor(
    root: Optional[str] = typer.Option(
        None,
        "--root",
        help="Workspace root path (defaults to git repo root if found)",
    ),
    json_out: bool = typer.Option(False, "--json", help="Output JSON format"),
    validate_mcp: bool = typer.Option(
        False, "--validate-mcp", help="Validate declared MCP config paths"
    ),
):
    """Check APS installation status + basic platform detection."""
    workspace_root = pick_workspace_root(root)

    payload_skill_dir = resolve_payload_skill_dir()
    platforms = sort_platforms_for_ui(load_platforms(payload_skill_dir))
    detected_adapters = (
        detect_adapters(workspace_root, platforms) if workspace_root else None
    )
    mcp_validation = _build_mcp_validation(workspace_root, platforms) if validate_mcp else None

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

    adapters_out = None
    if detected_adapters:
        adapters_out = {
            platform_id: {
                "platformId": detection.platform_id,
                "detected": detection.detected,
                "reasons": list(detection.reasons),
            }
            for platform_id, detection in detected_adapters.items()
        }

    result = {
        "workspace_root": str(workspace_root) if workspace_root else None,
        "detected_adapters": adapters_out,
        "installations": installations,
        "mcp_validation": mcp_validation,
    }

    if json_out:
        typer.echo(json.dumps(result, indent=2))
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

    if mcp_validation:
        console.print("")
        console.print("MCP config paths:")
        if not mcp_validation["checks"]:
            console.print("- (none declared)")
        else:
            for check in mcp_validation["checks"]:
                mark = (
                    "✓"
                    if check["status"] == "present"
                    else "✗"
                    if check["status"] == "missing"
                    else "•"
                )
                resolved = check["resolved_path"] or check["path"]
                detail = f" ({check['reason']})" if check.get("reason") else ""
                console.print(
                    f"- {check['platform_id']} [{check['scope']}]: {resolved} {mark}{detail}",
                    markup=False,
                )

    console.print("")
    console.print("Installed skills:")
    for inst in installations:
        status = "✓" if inst["installed"] else "✗"
        console.print(f"- {inst['scope']}: {inst['path']} {status}")


@app.command()
def update(
    root: Optional[str] = typer.Option(
        None,
        "--root",
        help="Workspace root path (defaults to git repo root if found)",
    ),
    repo: bool = typer.Option(
        False, "--repo", help="Update repo-scoped APS skill installation(s) only"
    ),
    personal: bool = typer.Option(
        False, "--personal", help="Update personal APS skill installation(s) only"
    ),
    check: bool = typer.Option(
        False, "--check", help="Check for available updates without writing files"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output JSON format"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print planned actions without writing"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Non-interactive; accept self-update prompt automatically"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Refresh installed skill directories even when versions already match"
    ),
):
    """Check for APS updates and refresh installed APS skills."""

    payload_skill_dir = resolve_payload_skill_dir()
    payload_version = read_skill_version(payload_skill_dir) or __version__
    runtime_mode = detect_python_runtime_mode(Path(__file__), Path(sys.executable))

    latest_version: Optional[str] = None
    registry_error: Optional[str] = None

    try:
        latest_version = fetch_latest_cli_version()
    except Exception as exc:
        registry_error = str(exc)

    package_status = PackageUpdateStatus(
        package_name="agnostic-prompt-aps",
        current_version=__version__,
        payload_version=payload_version,
        latest_version=latest_version,
        update_available=bool(
            latest_version and compare_semver(latest_version, __version__) > 0
        ),
        runtime_mode=runtime_mode,
        registry_error=registry_error,
    )

    if (
        package_status.update_available
        and not check
        and not dry_run
        and not json_out
        and os.environ.get(APS_SKIP_SELF_UPDATE_ENV) != "1"
        and runtime_mode != "dev-local"
    ):
        should_self_update = yes

        if not should_self_update and is_tty():
            should_self_update = bool(
                questionary.confirm(
                    f"A newer APS CLI release is available ({__version__} -> {latest_version}). Update the CLI package now before refreshing installed skills?",
                    default=True,
                ).ask()
            )

        if should_self_update and latest_version:
            maybe_self_update(
                runtime_mode=runtime_mode,
                latest_version=latest_version,
                root=root,
                repo=repo,
                personal=personal,
                check=check,
                json_out=json_out,
                dry_run=dry_run,
                yes=yes,
                force=force,
            )
            return

    planned_targets = collect_skill_targets(
        root=root,
        repo=repo,
        personal=personal,
        desired_version=payload_version,
    )

    planned_template_targets = collect_template_targets(
        root=root,
        repo=repo,
        personal=personal,
        payload_skill_dir=payload_skill_dir,
    )

    targets = (
        planned_targets
        if check or dry_run
        else apply_skill_updates(planned_targets, payload_skill_dir, force=force)
    )

    template_targets = (
        planned_template_targets
        if check or dry_run
        else apply_template_updates(planned_template_targets, payload_skill_dir, force=force)
    )

    if json_out:
        import dataclasses
        class PathEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Path):
                    return str(obj)
                return super().default(obj)

        typer.echo(
            json.dumps(
                {
                    "package": dataclasses.asdict(package_status),
                    "installations": [dataclasses.asdict(target) for target in targets],
                    "templates": [dataclasses.asdict(t) for t in template_targets],
                    "mode": "check" if check else "dry-run" if dry_run else "apply",
                },
                indent=2,
                cls=PathEncoder
            )
        )
        return

    _render_update_report(
        package_status,
        targets,
        template_targets,
        check=check,
        dry_run=dry_run,
        yes=yes,
    )

    if not targets and not template_targets and not check and not dry_run:
        console.print("")
        console.print("Nothing to update. Run `aps init` first to install APS.")


@app.command()
def platforms():
    """List available platform adapters bundled with this APS release."""
    payload_skill_dir = resolve_payload_skill_dir()
    plats = sort_platforms_for_ui(load_platforms(payload_skill_dir))

    table = Table(title="APS Platform Adapters")
    table.add_column("platform_id")
    table.add_column("display_name")
    table.add_column("adapter_version")

    for platform in plats:
        table.add_row(platform.platform_id, platform.display_name, platform.adapter_version or "")

    console.print(table)


@app.command()
def version():
    """Print CLI version."""
    typer.echo(__version__)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
