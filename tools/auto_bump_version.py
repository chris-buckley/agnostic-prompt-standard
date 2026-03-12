#!/usr/bin/env python3
"""Automatically bump the APS release version when releasable changes exist.

This tool closes the gap where APS changes land on the default branch but no one
bumps the package version, which prevents npm/PyPI releases from being created.

Default behavior:
- Find the latest semver git tag (for example `v1.2.3`).
- Read the current canonical APS version from SKILL.md.
- If the current version is already newer than the latest tag, do nothing.
- If the current version matches the latest tag, inspect changed files.
- If releasable files changed, calculate the next semver and optionally apply it.

By default, the tool treats changes under these prefixes as releasable:
- skill/
- packages/
- tools/

Typical usage in CI:
    python tools/auto_bump_version.py --base-ref "$GITHUB_EVENT_BEFORE" --apply --commit --push
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional

from bump_version import SEMVER_RE, get_repo_root, read_skill_version

DEFAULT_RELEASABLE_PREFIXES = ("skill/", "packages/", "tools/")


def parse_semver(value: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid semver: {value}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def compare_semver(a: str, b: str) -> int:
    parsed_a = parse_semver(a)
    parsed_b = parse_semver(b)
    return (parsed_a > parsed_b) - (parsed_a < parsed_b)


def bump_semver(version: str, part: str = "patch") -> str:
    major, minor, patch = parse_semver(version)

    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported semver part: {part}")


def normalize_tag_to_version(tag: str) -> Optional[str]:
    cleaned = tag.strip()
    if cleaned.startswith("refs/tags/"):
        cleaned = cleaned[len("refs/tags/") :]
    if cleaned.startswith("v"):
        cleaned = cleaned[1:]
    return cleaned if SEMVER_RE.fullmatch(cleaned) else None


def is_zero_git_sha(value: Optional[str]) -> bool:
    if not value:
        return True
    stripped = value.strip()
    return bool(stripped) and set(stripped) == {"0"}


def is_releasable_path(path_str: str, prefixes: Iterable[str]) -> bool:
    return any(path_str.startswith(prefix) for prefix in prefixes)


def filter_releasable_paths(paths: Iterable[str], prefixes: Iterable[str]) -> list[str]:
    return sorted({path for path in paths if is_releasable_path(path, prefixes)})


def git_stdout(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def git_run(repo_root: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True)


def has_worktree_changes(repo_root: Path) -> bool:
    return bool(git_stdout(repo_root, ["status", "--porcelain"]))


def list_version_tags(repo_root: Path) -> list[str]:
    raw = git_stdout(repo_root, ["tag", "--list", "--sort=-version:refname"])
    return [line.strip() for line in raw.splitlines() if line.strip()]


def find_latest_version_tag(repo_root: Path) -> tuple[Optional[str], Optional[str]]:
    for tag in list_version_tags(repo_root):
        normalized = normalize_tag_to_version(tag)
        if normalized:
            return tag, normalized
    return None, None


def list_changed_paths(
    repo_root: Path,
    *,
    base_ref: Optional[str],
    latest_tag: Optional[str],
) -> list[str]:
    if base_ref and not is_zero_git_sha(base_ref):
        diff_ref = f"{base_ref}..HEAD"
        raw = git_stdout(repo_root, ["diff", "--name-only", diff_ref])
        return [line.strip() for line in raw.splitlines() if line.strip()]

    if latest_tag:
        raw = git_stdout(repo_root, ["diff", "--name-only", f"{latest_tag}..HEAD"])
        return [line.strip() for line in raw.splitlines() if line.strip()]

    return []


def run_bump_version(repo_root: Path, new_version: str) -> None:
    subprocess.run(
        [sys.executable, str(repo_root / "tools" / "bump_version.py"), new_version],
        cwd=repo_root,
        check=True,
    )


def sync_payloads(repo_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(repo_root / "tools" / "sync_payload.py")],
        cwd=repo_root,
        check=True,
    )


def commit_changes(repo_root: Path, new_version: str) -> None:
    git_run(repo_root, ["add", "-A"])
    if not has_worktree_changes(repo_root):
        return
    git_run(repo_root, ["commit", "-m", f"chore(release): bump APS version to {new_version}"])


def push_changes(repo_root: Path) -> None:
    git_run(repo_root, ["push"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Automatically bump APS version when releasable changes exist")
    parser.add_argument("--repo-root", default=None, help="Repository root (defaults to this file's parent)")
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Optional git ref/SHA to diff against instead of the latest version tag",
    )
    parser.add_argument(
        "--part",
        choices=("patch", "minor", "major"),
        default="patch",
        help="Semver part to bump when releasable changes are found",
    )
    parser.add_argument(
        "--path-prefix",
        action="append",
        dest="path_prefixes",
        default=None,
        help="Releasable path prefix. Repeat to override the defaults.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply the calculated version bump")
    parser.add_argument(
        "--no-sync-payload",
        action="store_true",
        help="Do not run tools/sync_payload.py after applying the bump",
    )
    parser.add_argument("--commit", action="store_true", help="Commit the version bump after applying it")
    parser.add_argument("--push", action="store_true", help="Push the bump commit after committing it")
    args = parser.parse_args()

    if args.push and not args.commit:
        parser.error("--push requires --commit")
    if args.commit and not args.apply:
        parser.error("--commit requires --apply")

    repo_root = (
        Path(args.repo_root).expanduser().resolve() if args.repo_root else get_repo_root()
    )
    prefixes = tuple(args.path_prefixes or DEFAULT_RELEASABLE_PREFIXES)

    if args.commit and has_worktree_changes(repo_root):
        raise SystemExit("Refusing to auto-commit with a dirty worktree. Commit or stash changes first.")

    current_version = read_skill_version(
        repo_root / "skill" / "agnostic-prompt-standard" / "SKILL.md"
    )
    latest_tag, latest_tag_version = find_latest_version_tag(repo_root)

    if not latest_tag or not latest_tag_version:
        print("No semver release tag found. Skip auto-bump.")
        return 0

    version_cmp = compare_semver(current_version, latest_tag_version)
    if version_cmp < 0:
        raise SystemExit(
            f"Current APS version {current_version} is behind latest tag {latest_tag_version}. Fix version metadata first."
        )
    if version_cmp > 0:
        print(
            f"Current APS version {current_version} is already newer than latest tag {latest_tag}. No auto-bump needed."
        )
        return 0

    changed_paths = list_changed_paths(
        repo_root,
        base_ref=args.base_ref,
        latest_tag=latest_tag,
    )
    releasable_paths = filter_releasable_paths(changed_paths, prefixes)

    if not releasable_paths:
        print("No releasable changes found. Skip auto-bump.")
        return 0

    next_version = bump_semver(current_version, args.part)
    print(f"Current version: {current_version}")
    print(f"Latest tag: {latest_tag}")
    print(f"Releasable changes ({len(releasable_paths)}):")
    for path_str in releasable_paths:
        print(f"  - {path_str}")
    print(f"Proposed next version: {next_version}")

    if not args.apply:
        return 0

    run_bump_version(repo_root, next_version)
    if not args.no_sync_payload:
        sync_payloads(repo_root)

    if args.commit:
        commit_changes(repo_root, next_version)
        if args.push:
            push_changes(repo_root)

    print(f"Applied APS version bump: {current_version} -> {next_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
