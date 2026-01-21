#!/usr/bin/env python3
"""Atomically update version across all APS files.

Updates:
- skill/agnostic-prompt-standard/SKILL.md framework_revision
- packages/aps-cli-node/package.json version
- packages/aps-cli-py/pyproject.toml [project].version
- packages/aps-cli-py/src/aps_cli/__init__.py __version__

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
