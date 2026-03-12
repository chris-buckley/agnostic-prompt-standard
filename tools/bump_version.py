#!/usr/bin/env python3
"""Atomically update version across all APS files.

Updates:
- skill/agnostic-prompt-standard/SKILL.md framework_revision
- packages/aps-cli-node/package.json version
- packages/aps-cli-node/package-lock.json top-level + root package version
- packages/aps-cli-py/pyproject.toml [project].version
- packages/aps-cli-py/src/aps_cli/__init__.py __version__
- Platform agent templates (frontmatter + file names) via adaptor.md

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
    """Return the repository root (parent of the tools/ directory)."""
    return Path(__file__).resolve().parents[1]


# --- Version readers ---


def read_skill_version(skill_md: Path) -> str:
    """Read framework_revision from SKILL.md frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    m = re.search(r'framework_revision:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', text)
    if not m:
        raise SystemExit(f"Could not find framework_revision in {skill_md}")
    return m.group(1)


def read_node_version(pkg_json: Path) -> str:
    """Read version from Node package.json."""
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    v = data.get("version")
    if not isinstance(v, str):
        raise SystemExit(f"No version in {pkg_json}")
    return v


def read_node_lock_version(lock_json: Path) -> str:
    """Read version from Node package-lock.json and validate the root package entry."""
    data = json.loads(lock_json.read_text(encoding="utf-8"))
    top_level_version = data.get("version")
    root_package_version = data.get("packages", {}).get("", {}).get("version")

    if not isinstance(top_level_version, str):
        raise SystemExit(f"No top-level version in {lock_json}")
    if root_package_version is not None and root_package_version != top_level_version:
        raise SystemExit(
            f"Version mismatch inside {lock_json}: top-level={top_level_version}, packages[''].version={root_package_version}"
        )

    return top_level_version


def read_pyproject_version(pyproject: Path) -> str:
    """Read [project].version from pyproject.toml."""
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'\[project\][\s\S]*?\nversion\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit(f"No [project].version in {pyproject}")
    return m.group(1)


def read_python_module_version(init_py: Path) -> str:
    """Read __version__ from Python __init__.py."""
    text = init_py.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit(f"No __version__ in {init_py}")
    return m.group(1)


# --- Version updaters ---


def update_skill_version(skill_md: Path, new_version: str) -> None:
    """Update framework_revision in SKILL.md frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    updated = re.sub(
        r'(framework_revision:\s*)"?[0-9]+\.[0-9]+\.[0-9]+"?',
        f'\\1"{new_version}"',
        text,
    )
    skill_md.write_text(updated, encoding="utf-8")


def update_node_version(pkg_json: Path, new_version: str) -> None:
    """Update version in Node package.json."""
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    data["version"] = new_version
    pkg_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_node_lock_version(lock_json: Path, new_version: str) -> None:
    """Update top-level and root package versions in Node package-lock.json."""
    data = json.loads(lock_json.read_text(encoding="utf-8"))
    data["version"] = new_version
    packages = data.setdefault("packages", {})
    root_package = packages.setdefault("", {})
    if not isinstance(root_package, dict):
        raise SystemExit(f"Invalid root package entry in {lock_json}")
    root_package["version"] = new_version
    lock_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_pyproject_version(pyproject: Path, new_version: str) -> None:
    """Update [project].version in pyproject.toml."""
    text = pyproject.read_text(encoding="utf-8")
    updated = re.sub(
        r'(\[project\][\s\S]*?\nversion\s*=\s*)"[^"]+"',
        f'\\1"{new_version}"',
        text,
    )
    pyproject.write_text(updated, encoding="utf-8")


def update_python_module_version(init_py: Path, new_version: str) -> None:
    """Update __version__ in Python __init__.py."""
    text = init_py.read_text(encoding="utf-8")
    updated = re.sub(
        r'(__version__\s*=\s*)"[^"]+"',
        f'\\1"{new_version}"',
        text,
    )
    init_py.write_text(updated, encoding="utf-8")


# --- Skill metadata (authors) ---


def read_skill_metadata(skill_md: Path) -> dict[str, str]:
    """Read author, co_authors, and repository from SKILL.md frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    result: dict[str, str] = {"author": "", "co_authors": "", "repository": ""}

    m = re.search(r'^\s*author:\s*"([^"]*)"', text, flags=re.MULTILINE)
    if m:
        result["author"] = m.group(1).strip()

    m = re.search(r'^\s*co_authors:\s*"([^"]*)"', text, flags=re.MULTILINE)
    if m:
        result["co_authors"] = m.group(1).strip()

    m = re.search(r'^\s*repository:\s*"([^"]*)"', text, flags=re.MULTILINE)
    if m:
        result["repository"] = m.group(1).strip()

    return result


def build_authors_suffix(metadata: dict[str, str]) -> str:
    """Compose the authors/URL suffix for agent description frontmatter."""
    parts: list[str] = []

    author = metadata.get("author", "")
    if author:
        parts.append(f"Author: {author}.")

    co_authors = metadata.get("co_authors", "")
    if co_authors:
        names = ", ".join(name.strip() for name in co_authors.split(";") if name.strip())
        parts.append(f"Co-authors: {names}.")

    repository = metadata.get("repository", "")
    if repository:
        parts.append(f"URL: {repository}")

    return " ".join(parts)


# --- Adaptor.md parsing (minimal, for AGENT_VERSIONING) ---


def _parse_adaptor_json_block(text: str, key: str) -> dict[str, Any] | None:
    """Extract a JSON<< >> block constant from adaptor.md text."""
    pattern = rf'{re.escape(key)}:\s*JSON<<\r?\n(.*?)>>'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _update_adaptor_json_block(text: str, key: str, new_data: dict[str, Any]) -> str:
    """Replace a JSON<< >> block constant in adaptor.md text."""
    pattern = rf'({re.escape(key)}:\s*JSON<<\r?\n)(.*?)(>>)'
    replacement = rf'\g<1>{json.dumps(new_data, indent=2)}\n\g<3>'
    return re.sub(pattern, replacement, text, flags=re.DOTALL)


# --- Platform agent versioning ---


def load_platform_versioning_configs(
    platforms_dir: Path,
) -> list[tuple[str, Path, dict[str, Any]]]:
    """Load agent versioning config from adaptor.md."""
    results = []
    if not platforms_dir.exists():
        return results
    for platform_dir in platforms_dir.iterdir():
        if not platform_dir.is_dir() or platform_dir.name.startswith("_"):
            continue

        adaptor_path = platform_dir / "adaptor.md"
        if adaptor_path.exists():
            text = adaptor_path.read_text(encoding="utf-8")
            versioning = _parse_adaptor_json_block(text, "AGENT_VERSIONING")
            if versioning:
                results.append((platform_dir.name, platform_dir, versioning))
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
    # adaptor.md uses snake_case; manifest.json uses camelCase
    current_path_rel = template_config.get("current_path") or template_config.get("currentPath")
    path_pattern = template_config.get("path", "")

    if current_path_rel:
        current_path = platform_dir / current_path_rel
        if current_path.exists():
            return current_path

    if path_pattern:
        glob_pattern = path_pattern.replace("{major}", "*").replace("{minor}", "*").replace("{patch}", "*")
        matches = list(platform_dir.glob(glob_pattern))
        if matches:
            return max(matches, key=lambda p: p.stat().st_mtime)

    return None


def update_agent_frontmatter(
    file_path: Path,
    frontmatter_config: dict[str, Any],
    major: str,
    minor: str,
    patch: str,
    authors_suffix: str = "",
) -> bool:
    """Update frontmatter fields in an agent file.

    Handles both adaptor.md style (name_pattern/description_pattern)
    and manifest.json style (name.pattern/description.pattern).
    """
    if not file_path.exists():
        return False

    text = file_path.read_text(encoding="utf-8")
    updated = text

    # Normalize config: support both adaptor.md and manifest.json key styles
    normalized: dict[str, dict[str, str]] = {}
    for field_key, config in frontmatter_config.items():
        if isinstance(config, dict):
            if "pattern" in config:
                normalized[field_key] = config
            else:
                # Nested format: { name: { pattern: "..." } }
                for sub_key, sub_val in config.items():
                    if isinstance(sub_val, dict) and "pattern" in sub_val:
                        normalized[sub_key] = sub_val
        elif isinstance(config, str) and field_key.endswith("_pattern"):
            # adaptor.md style: name_pattern, description_pattern
            actual_field = field_key.replace("_pattern", "")
            normalized[actual_field] = {"pattern": config}

    for field_name, config in normalized.items():
        pattern = config.get("pattern", "")
        if not pattern:
            continue
        new_value = expand_version_pattern(pattern, major, minor, patch)

        if field_name == "description" and authors_suffix:
            new_value = f"{new_value} {authors_suffix}"

        # Match YAML frontmatter field with quoted value
        pattern_quoted = rf'^({field_name}:\s*)"[^"]*"'
        if re.search(pattern_quoted, updated, flags=re.MULTILINE):
            updated = re.sub(pattern_quoted, rf'\1"{new_value}"', updated, flags=re.MULTILINE)
        else:
            pattern_unquoted = rf'^({field_name}:\s*)(\S[^\n]*)$'
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


def _update_adaptor_versioning_current_path(
    platform_dir: Path, new_rel: str, template_path_pattern: str
) -> None:
    """Update the current_path for a specific template in the AGENT_VERSIONING block."""
    adaptor_path = platform_dir / "adaptor.md"
    if not adaptor_path.exists():
        return
    text = adaptor_path.read_text(encoding="utf-8")
    versioning = _parse_adaptor_json_block(text, "AGENT_VERSIONING")
    if not versioning:
        return
    for tmpl in versioning.get("templates", []):
        if tmpl.get("path") == template_path_pattern:
            tmpl["current_path"] = new_rel
            break
    updated = _update_adaptor_json_block(text, "AGENT_VERSIONING", versioning)
    adaptor_path.write_text(updated, encoding="utf-8")


def update_platform_agents(
    platforms_dir: Path, new_version: str, authors_suffix: str = ""
) -> list[str]:
    """Update all platform agent templates with new version."""
    match = SEMVER_RE.match(new_version)
    if not match:
        return []

    major, minor, patch = match.groups()
    updated_files = []

    for platform_id, platform_dir, versioning in load_platform_versioning_configs(platforms_dir):
        templates = versioning.get("templates", [])

        for template in templates:
            # Normalize frontmatter config from both adaptor.md and manifest.json styles
            frontmatter_config = template.get("frontmatter", {})

            source_path = find_existing_agent_file(platform_dir, template)
            if not source_path:
                print(f"  Warning: No agent file found for {platform_id}", file=sys.stderr)
                continue

            frontmatter_updated = update_agent_frontmatter(
                source_path, frontmatter_config, major, minor, patch, authors_suffix
            )

            new_path = rename_agent_file(platform_dir, template, source_path, major, minor, patch)

            # Update current_path in adaptor.md
            if new_path and new_path != source_path:
                new_rel = str(new_path.relative_to(platform_dir)).replace("\\", "/")

                adaptor_path = platform_dir / "adaptor.md"
                if adaptor_path.exists():
                    _update_adaptor_versioning_current_path(
                        platform_dir, new_rel, template["path"]
                    )

            if new_path:
                updated_files.append(str(new_path))
            elif frontmatter_updated:
                updated_files.append(str(source_path))

    return updated_files


def main() -> int:
    """CLI entrypoint: update or check APS version across all sources."""
    ap = argparse.ArgumentParser(description="Update or check APS version")
    ap.add_argument("version", nargs="?", help="New version (e.g., 1.2.3)")
    ap.add_argument("--check", action="store_true", help="Check that all versions match")
    args = ap.parse_args()

    repo_root = get_repo_root()
    skill_md = repo_root / "skill" / "agnostic-prompt-standard" / "SKILL.md"
    pkg_json = repo_root / "packages" / "aps-cli-node" / "package.json"
    lock_json = repo_root / "packages" / "aps-cli-node" / "package-lock.json"
    pyproject = repo_root / "packages" / "aps-cli-py" / "pyproject.toml"
    init_py = repo_root / "packages" / "aps-cli-py" / "src" / "aps_cli" / "__init__.py"
    platforms_dir = repo_root / "skill" / "agnostic-prompt-standard" / "platforms"

    versions = {
        "skill": read_skill_version(skill_md),
        "node": read_node_version(pkg_json),
        "node_lock": read_node_lock_version(lock_json),
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
    update_node_lock_version(lock_json, new_version)
    update_pyproject_version(pyproject, new_version)
    update_python_module_version(init_py, new_version)

    print("Done. Updated:")
    print(f"  - {skill_md}")
    print(f"  - {pkg_json}")
    print(f"  - {lock_json}")
    print(f"  - {pyproject}")
    print(f"  - {init_py}")

    metadata = read_skill_metadata(skill_md)
    authors_suffix = build_authors_suffix(metadata)

    agent_updates = update_platform_agents(platforms_dir, new_version, authors_suffix)
    if agent_updates:
        print("\nPlatform agent templates updated:")
        for f in agent_updates:
            print(f"  - {f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
