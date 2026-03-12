#!/usr/bin/env python3
"""Fail-fast version consistency checks.

We treat the APS skill's `framework_revision` as the canonical release version, and require:
- skill/agnostic-prompt-standard/SKILL.md framework_revision == X.Y.Z
- packages/aps-cli-node/package.json version == X.Y.Z
- packages/aps-cli-node/package-lock.json top-level + root package version == X.Y.Z
- packages/aps-cli-py/pyproject.toml [project].version == X.Y.Z
- packages/aps-cli-py/src/aps_cli/__init__.py __version__ == X.Y.Z

Optionally validate tag name (e.g. vX.Y.Z).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def read_skill_version(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(r"framework_revision:\s*\"?([0-9]+\.[0-9]+\.[0-9]+)\"?", text)
    if not match:
        raise SystemExit(f"Could not find framework_revision in {skill_md}")
    version = match.group(1)
    if not SEMVER_RE.match(version):
        raise SystemExit(f"framework_revision is not semver: {version}")
    return version


def read_node_version(pkg_json: Path) -> str:
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    version = data.get("version")
    if not isinstance(version, str):
        raise SystemExit(f"No version in {pkg_json}")
    return version


def read_node_lock_version(lock_json: Path) -> str:
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
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r"\[project\][\s\S]*?\nversion\s*=\s*\"([^\"]+)\"", text)
    if not match:
        raise SystemExit(f"No [project].version in {pyproject}")
    return match.group(1)


def read_python_module_version(init_py: Path) -> str:
    text = init_py.read_text(encoding="utf-8")
    match = re.search(r"__version__\s*=\s*\"([^\"]+)\"", text)
    if not match:
        raise SystemExit(f"No __version__ in {init_py}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--tag", default=None, help="Tag name like v1.2.3 (optional)")
    args = parser.parse_args()

    repo_root = (
        Path(args.repo_root).expanduser().resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[1]
    )

    versions = {
        "skill": read_skill_version(repo_root / "skill" / "agnostic-prompt-standard" / "SKILL.md"),
        "node": read_node_version(repo_root / "packages" / "aps-cli-node" / "package.json"),
        "node_lock": read_node_lock_version(repo_root / "packages" / "aps-cli-node" / "package-lock.json"),
        "python": read_pyproject_version(repo_root / "packages" / "aps-cli-py" / "pyproject.toml"),
        "python_module": read_python_module_version(
            repo_root / "packages" / "aps-cli-py" / "src" / "aps_cli" / "__init__.py"
        ),
    }

    unique_versions = sorted(set(versions.values()))
    if len(unique_versions) != 1:
        raise SystemExit(f"Version mismatch: {versions}")

    canonical_version = unique_versions[0]

    if args.tag:
        tag_value = args.tag
        if tag_value.startswith("refs/tags/"):
            tag_value = tag_value[len("refs/tags/") :]
        normalized_tag = tag_value[1:] if tag_value.startswith("v") else tag_value
        if normalized_tag != canonical_version:
            raise SystemExit(
                f"Tag/version mismatch: tag={args.tag} -> {normalized_tag}, expected={canonical_version}"
            )

    print(f"OK: version={canonical_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
