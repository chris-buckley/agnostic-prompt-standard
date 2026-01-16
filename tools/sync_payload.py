#!/usr/bin/env python3
"""Sync the APS skill directory into the Node + Python CLI package payloads.

Why this exists:
- `npx`/`pipx` installs the CLI package, so the CLI needs the APS files bundled.
- We keep APS as the single source of truth in `skill/agnostic-prompt-standard/`.

This script is intended to run in CI before building/publishing, and can be run locally.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SKILL_ID = "agnostic-prompt-standard"


def copy_skill(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=None, help="Repo root (defaults to this file's parent)")
    ap.add_argument("--node", action="store_true", help="Sync node payload")
    ap.add_argument("--python", action="store_true", help="Sync python payload")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    src = repo_root / "skill" / SKILL_ID
    if not src.is_dir():
        raise SystemExit(f"Skill dir not found: {src}")

    do_node = args.node or (not args.node and not args.python)
    do_py = args.python or (not args.node and not args.python)

    if do_node:
        dst_node = repo_root / "packages" / "aps-cli-node" / "payload" / SKILL_ID
        copy_skill(src, dst_node)
        print(f"Synced node payload -> {dst_node}")

    if do_py:
        dst_py = repo_root / "packages" / "aps-cli-py" / "src" / "aps_cli" / "payload" / SKILL_ID
        copy_skill(src, dst_py)
        print(f"Synced python payload -> {dst_py}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
