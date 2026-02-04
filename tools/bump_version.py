#!/usr/bin/env python3
"""Atomically update version across all APS files.

Updates:
- skill/agnostic-prompt-standard/SKILL.md framework_revision
- packages/aps-cli-node/package.json version
- packages/aps-cli-py/pyproject.toml [project].version
- packages/aps-cli-py/src/aps_cli/__init__.py __version__
- Platform agent templates (frontmatter + file names)

Usage:
    python tools/bump_version.py 1.2.3       # Update all files to 1.2.3
    python tools/bump_version.py --check     # Verify all versions match
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_skill_version(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    m = re.search(r'framework_revision:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', text)
    if not m:
        raise SystemExit(f"Could not find framework_revision in {skill_md}")
    return m.group(1)


def read_node_version(pkg_json: Path) -> str:
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    v = data.get("version")
    if not isinstance(v, str):
        raise SystemExit(f"No version in {pkg_json}")
    return v


def read_pyproject_version(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'\[project\][\s\S]*?\nversion\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit(f"No [project].version in {pyproject}")
    return m.group(1)


def read_python_module_version(init_py: Path) -> str:
    text = init_py.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit(f"No __version__ in {init_py}")
    return m.group(1)


def update_skill_version(skill_md: Path, new_version: str) -> None:
    text = skill_md.read_text(encoding="utf-8")
    updated = re.sub(
        r'(framework_revision:\s*)"?[0-9]+\.[0-9]+\.[0-9]+"?',
        f'\\1"{new_version}"',
        text,
    )
    skill_md.write_text(updated, encoding="utf-8")


def update_node_version(pkg_json: Path, new_version: str) -> None:
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    data["version"] = new_version
    pkg_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_pyproject_version(pyproject: Path, new_version: str) -> None:
    text = pyproject.read_text(encoding="utf-8")
    updated = re.sub(
        r'(\[project\][\s\S]*?\nversion\s*=\s*)"[^"]+"',
        f'\\1"{new_version}"',
        text,
    )
    pyproject.write_text(updated, encoding="utf-8")


def update_python_module_version(init_py: Path, new_version: str) -> None:
    text = init_py.read_text(encoding="utf-8")
    updated = re.sub(
        r'(__version__\s*=\s*)"[^"]+"',
        f'\\1"{new_version}"',
        text,
    )
    init_py.write_text(updated, encoding="utf-8")


# --- Platform agent versioning ---


def load_platform_manifests(platforms_dir: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    """Load all platform manifests that have agentVersioning config."""
    results = []
    if not platforms_dir.exists():
        return results
    for platform_dir in platforms_dir.iterdir():
        if not platform_dir.is_dir() or platform_dir.name.startswith("_"):
            continue
        manifest_path = platform_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "agentVersioning" in manifest:
                results.append((platform_dir.name, platform_dir, manifest))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def expand_version_pattern(pattern: str, major: str, minor: str, patch: str) -> str:
    """Expand {major}, {minor}, {patch} placeholders in a pattern."""
    return (
        pattern.replace("{major}", major)
        .replace("{minor}", minor)
        .replace("{patch}", patch)
    )


def find_existing_agent_file(platform_dir: Path, template_config: dict[str, Any]) -> Path | None:
    """Find the current agent file, whether unversioned or previously versioned."""
    current_path_rel = template_config.get("currentPath")
    path_pattern = template_config.get("path", "")

    # Try unversioned path first
    if current_path_rel:
        current_path = platform_dir / current_path_rel
        if current_path.exists():
            return current_path

    # Try to find existing versioned file
    if path_pattern:
        glob_pattern = path_pattern.replace("{major}", "*").replace("{minor}", "*").replace("{patch}", "*")
        matches = list(platform_dir.glob(glob_pattern))
        if matches:
            # Return the most recently modified one
            return max(matches, key=lambda p: p.stat().st_mtime)

    return None


def update_agent_frontmatter(
    file_path: Path, frontmatter_config: dict[str, Any], major: str, minor: str, patch: str
) -> bool:
    """Update frontmatter fields in an agent file based on platform config."""
    if not file_path.exists():
        return False

    text = file_path.read_text(encoding="utf-8")
    updated = text

    for field, config in frontmatter_config.items():
        if "pattern" not in config:
            continue
        new_value = expand_version_pattern(config["pattern"], major, minor, patch)

        # Match YAML frontmatter field with quoted value
        pattern_quoted = rf'^({field}:\s*)"[^"]*"'
        if re.search(pattern_quoted, updated, flags=re.MULTILINE):
            updated = re.sub(pattern_quoted, rf'\1"{new_value}"', updated, flags=re.MULTILINE)
        else:
            # Try unquoted value (for fields like name in Claude Code)
            pattern_unquoted = rf'^({field}:\s*)(\S[^\n]*)$'
            updated = re.sub(pattern_unquoted, rf'\1{new_value}', updated, flags=re.MULTILINE)

    if updated != text:
        file_path.write_text(updated, encoding="utf-8")
        return True
    return False


def rename_agent_file(
    platform_dir: Path, template_config: dict[str, Any], source_path: Path, major: str, minor: str, patch: str
) -> Path | None:
    """Rename agent file to include version if configured."""
    new_path_rel = template_config.get("path")
    if not new_path_rel:
        return None

    new_path_pattern = expand_version_pattern(new_path_rel, major, minor, patch)
    new_path = platform_dir / new_path_pattern

    if source_path != new_path:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(new_path)
        return new_path
    return source_path


def update_platform_agents(platforms_dir: Path, new_version: str) -> list[str]:
    """Update all platform agent templates with new version."""
    match = SEMVER_RE.match(new_version)
    if not match:
        return []

    major, minor, patch = match.groups()
    updated_files = []

    for platform_id, platform_dir, manifest in load_platform_manifests(platforms_dir):
        versioning = manifest.get("agentVersioning", {})
        templates = versioning.get("templates", [])

        for template in templates:
            frontmatter_config = template.get("frontmatter", {})

            # Find the source file
            source_path = find_existing_agent_file(platform_dir, template)
            if not source_path:
                print(f"  Warning: No agent file found for {platform_id}", file=sys.stderr)
                continue

            # Update frontmatter
            frontmatter_updated = update_agent_frontmatter(
                source_path, frontmatter_config, major, minor, patch
            )

            # Rename file if path pattern includes version
            new_path = rename_agent_file(platform_dir, template, source_path, major, minor, patch)

            if new_path:
                updated_files.append(str(new_path))
            elif frontmatter_updated:
                updated_files.append(str(source_path))

    return updated_files


def main() -> int:
    ap = argparse.ArgumentParser(description="Update or check APS version")
    ap.add_argument("version", nargs="?", help="New version (e.g., 1.2.3)")
    ap.add_argument("--check", action="store_true", help="Check that all versions match")
    args = ap.parse_args()

    repo_root = get_repo_root()
    skill_md = repo_root / "skill" / "agnostic-prompt-standard" / "SKILL.md"
    pkg_json = repo_root / "packages" / "aps-cli-node" / "package.json"
    pyproject = repo_root / "packages" / "aps-cli-py" / "pyproject.toml"
    init_py = repo_root / "packages" / "aps-cli-py" / "src" / "aps_cli" / "__init__.py"
    platforms_dir = repo_root / "skill" / "agnostic-prompt-standard" / "platforms"

    # Read current versions
    versions = {
        "skill": read_skill_version(skill_md),
        "node": read_node_version(pkg_json),
        "python": read_pyproject_version(pyproject),
        "python_module": read_python_module_version(init_py),
    }

    if args.check:
        uniq = sorted(set(versions.values()))
        if len(uniq) != 1:
            print(f"Version mismatch: {versions}", file=sys.stderr)
            return 1
        print(f"OK: version={uniq[0]}")
        return 0

    if not args.version:
        ap.print_help()
        return 1

    new_version = args.version
    if not SEMVER_RE.match(new_version):
        print(f"Invalid semver: {new_version}", file=sys.stderr)
        return 1

    print(f"Current versions: {versions}")
    print(f"Updating to: {new_version}")

    update_skill_version(skill_md, new_version)
    update_node_version(pkg_json, new_version)
    update_pyproject_version(pyproject, new_version)
    update_python_module_version(init_py, new_version)

    print("Done. Updated:")
    print(f"  - {skill_md}")
    print(f"  - {pkg_json}")
    print(f"  - {pyproject}")
    print(f"  - {init_py}")

    # Update platform agent templates
    agent_updates = update_platform_agents(platforms_dir, new_version)
    if agent_updates:
        print("\nPlatform agent templates updated:")
        for f in agent_updates:
            print(f"  - {f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
