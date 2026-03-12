#!/usr/bin/env python3
"""Tests for auto_bump_version.py."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from auto_bump_version import (  # noqa: E402
    bump_semver,
    filter_releasable_paths,
    is_releasable_path,
    is_zero_git_sha,
    normalize_tag_to_version,
)


class TestNormalizeTagToVersion(unittest.TestCase):
    def test_normalizes_v_prefixed_tags(self):
        self.assertEqual(normalize_tag_to_version("v1.2.3"), "1.2.3")

    def test_normalizes_refs_tags_prefix(self):
        self.assertEqual(normalize_tag_to_version("refs/tags/v1.2.3"), "1.2.3")

    def test_rejects_non_semver_tags(self):
        self.assertIsNone(normalize_tag_to_version("release-2025-01-01"))


class TestBumpSemver(unittest.TestCase):
    def test_bumps_patch(self):
        self.assertEqual(bump_semver("1.2.3", "patch"), "1.2.4")

    def test_bumps_minor(self):
        self.assertEqual(bump_semver("1.2.3", "minor"), "1.3.0")

    def test_bumps_major(self):
        self.assertEqual(bump_semver("1.2.3", "major"), "2.0.0")


class TestReleasablePaths(unittest.TestCase):
    def test_matches_default_releasable_prefixes(self):
        prefixes = ("skill/", "packages/", "tools/")
        self.assertTrue(is_releasable_path("skill/agnostic-prompt-standard/SKILL.md", prefixes))
        self.assertTrue(is_releasable_path("packages/aps-cli-node/src/cli.ts", prefixes))
        self.assertFalse(is_releasable_path("docs/adr/0001-example.md", prefixes))

    def test_filters_and_deduplicates_paths(self):
        paths = [
            "docs/adr/0001-example.md",
            "packages/aps-cli-node/src/cli.ts",
            "packages/aps-cli-node/src/cli.ts",
            "tools/bump_version.py",
        ]
        prefixes = ("skill/", "packages/", "tools/")
        self.assertEqual(
            filter_releasable_paths(paths, prefixes),
            ["packages/aps-cli-node/src/cli.ts", "tools/bump_version.py"],
        )


class TestZeroGitSha(unittest.TestCase):
    def test_recognizes_empty_or_none(self):
        self.assertTrue(is_zero_git_sha(None))
        self.assertTrue(is_zero_git_sha(""))

    def test_recognizes_all_zero_sha(self):
        self.assertTrue(is_zero_git_sha("0" * 40))

    def test_rejects_non_zero_sha(self):
        self.assertFalse(is_zero_git_sha("a" * 40))


if __name__ == "__main__":
    unittest.main()
