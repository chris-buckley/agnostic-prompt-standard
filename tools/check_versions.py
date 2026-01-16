#!/usr/bin/env python3
"""Fail-fast version consistency checks.

We treat the APS skill's `framework_revision` as the canonical release version, and require:
- skill/agnostic-prompt-standard/SKILL.md framework_revision == X.Y.Z
- packages/aps-cli-node/package.json version == X.Y.Z
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
    m = re.search(r"framework_revision:\s*\"?([0-9]+\.[0-9]+\.[0-9]+)\"?", text)
    if not m:
        raise SystemExit(f"Could not find framework_revision in {skill_md}")
    v = m.group(1)
    if not SEMVER_RE.match(v):
        raise SystemExit(f"framework_revision is not semver: {v}")
    return v


def read_node_version(pkg_json: Path) -> str:
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    v = data.get("version")
    if not isinstance(v, str):
        raise SystemExit(f"No version in {pkg_json}")
    return v


def read_pyproject_version(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    # Very small parser: first 'version = "..."' after [project]
    m = re.search(r"\[project\][\s\S]*?\nversion\s*=\s*\"([^\"]+)\"", text)
    if not m:
        raise SystemExit(f"No [project].version in {pyproject}")
    return m.group(1)


def read_python_module_version(init_py: Path) -> str:
    text = init_py.read_text(encoding="utf-8")
    m = re.search(r"__version__\s*=\s*\"([^\"]+)\"", text)
    if not m:
        raise SystemExit(f"No __version__ in {init_py}")
    return m.group(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--tag", default=None, help="Tag name like v1.2.3 (optional)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else Path(__file__).resolve().parents[1]

    v_skill = read_skill_version(repo_root / "skill" / "agnostic-prompt-standard" / "SKILL.md")
    v_node = read_node_version(repo_root / "packages" / "aps-cli-node" / "package.json")
    v_py = read_pyproject_version(repo_root / "packages" / "aps-cli-py" / "pyproject.toml")
    v_py_mod = read_python_module_version(repo_root / "packages" / "aps-cli-py" / "src" / "aps_cli" / "__init__.py")

    versions = {
        "skill": v_skill,
        "node": v_node,
        "python": v_py,
        "python_module": v_py_mod,
    }

    uniq = sorted(set(versions.values()))
    if len(uniq) != 1:
        raise SystemExit(f"Version mismatch: {versions}")

    if args.tag:
        tag = args.tag
        if tag.startswith("refs/tags/"):
            tag = tag[len("refs/tags/") :]
        if tag.startswith("v"):
            tag_v = tag[1:]
        else:
            tag_v = tag
        if tag_v != v_skill:
            raise SystemExit(f"Tag/version mismatch: tag={args.tag} -> {tag_v}, expected={v_skill}")

    print(f"OK: version={v_skill}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
