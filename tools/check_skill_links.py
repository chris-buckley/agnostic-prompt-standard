#!/usr/bin/env python3
"""Check that relative markdown links inside the APS skill resolve to existing files.

This catches broken internal links (a common footgun when moving/restructuring).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def is_external(link: str) -> bool:
    return link.startswith(("http://", "https://", "mailto:", "tel:"))


def normalize_target(link: str) -> str:
    # strip fragment (#...) and query (?...) if present
    target = link.split("#", 1)[0].split("?", 1)[0].strip()
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=None, help="Path to skill root")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else repo_root / "skill" / "agnostic-prompt-standard"

    missing: list[tuple[Path, str, Path]] = []

    for md in skill_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for raw in LINK_RE.findall(text):
            if not raw:
                continue
            raw = raw.strip()
            if raw.startswith("#"):
                continue
            if is_external(raw):
                continue
            target = normalize_target(raw)
            if "<" in target or ">" in target:
                continue
            if not target:
                continue
            # ignore absolute paths (rare) and protocol-relative
            if target.startswith("/") or target.startswith("//"):
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                missing.append((md, raw, resolved))

    if missing:
        print("Broken relative links detected:\n")
        for src, raw, resolved in missing:
            print(f"- {src.relative_to(skill_dir)} -> {raw} (resolved: {resolved})")
        return 1

    print("OK: no broken relative links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
