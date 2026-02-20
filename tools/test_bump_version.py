#!/usr/bin/env python3
"""Tests for bump_version.py platform agent versioning."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent))
from bump_version import (
    _parse_adaptor_json_block,
    build_authors_suffix,
    expand_version_pattern,
    find_existing_agent_file,
    load_platform_versioning_configs,
    read_skill_metadata,
    rename_agent_file,
    update_agent_frontmatter,
    update_platform_agents,
    SEMVER_RE,
)


class TestExpandVersionPattern(unittest.TestCase):
    """Tests for expand_version_pattern function."""

    def test_replaces_all_placeholders(self):
        pattern = "v{major}.{minor}.{patch}"
        result = expand_version_pattern(pattern, "1", "2", "3")
        self.assertEqual(result, "v1.2.3")

    def test_replaces_major_only(self):
        pattern = "version-{major}"
        result = expand_version_pattern(pattern, "2", "0", "0")
        self.assertEqual(result, "version-2")

    def test_handles_multiple_occurrences(self):
        pattern = "{major}.{minor}.{patch} ({major}.{minor})"
        result = expand_version_pattern(pattern, "1", "1", "7")
        self.assertEqual(result, "1.1.7 (1.1)")

    def test_no_placeholders_returns_unchanged(self):
        pattern = "static-text"
        result = expand_version_pattern(pattern, "1", "2", "3")
        self.assertEqual(result, "static-text")


class TestLoadPlatformVersioningConfigs(unittest.TestCase):
    """Tests for load_platform_versioning_configs function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.platforms_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_returns_empty_for_nonexistent_dir(self):
        result = load_platform_versioning_configs(Path("/nonexistent"))
        self.assertEqual(result, [])

    def test_skips_directories_starting_with_underscore(self):
        underscore_dir = self.platforms_dir / "_template"
        underscore_dir.mkdir()
        adaptor_content = '<instructions></instructions>\n<constants>\nPLATFORM_ID: "_template"\nDISPLAY_NAME: "Template"\n\nAGENT_VERSIONING: JSON<<\n{\n  "templates": []\n}\n>>\n</constants>\n<formats></formats>'
        (underscore_dir / "adaptor.md").write_text(adaptor_content)

        result = load_platform_versioning_configs(self.platforms_dir)
        self.assertEqual(result, [])

    def test_skips_adaptors_without_agent_versioning(self):
        platform_dir = self.platforms_dir / "test-platform"
        platform_dir.mkdir()
        adaptor_content = '<instructions></instructions>\n<constants>\nPLATFORM_ID: "test"\nDISPLAY_NAME: "Test"\n</constants>\n<formats></formats>'
        (platform_dir / "adaptor.md").write_text(adaptor_content)

        result = load_platform_versioning_configs(self.platforms_dir)
        self.assertEqual(result, [])

    def test_loads_adaptor_with_agent_versioning(self):
        platform_dir = self.platforms_dir / "test-platform"
        platform_dir.mkdir()
        adaptor_content = '<instructions></instructions>\n<constants>\nPLATFORM_ID: "test-platform"\nDISPLAY_NAME: "Test Platform"\n\nAGENT_VERSIONING: JSON<<\n{\n  "templates": []\n}\n>>\n</constants>\n<formats></formats>'
        (platform_dir / "adaptor.md").write_text(adaptor_content)

        result = load_platform_versioning_configs(self.platforms_dir)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "test-platform")
        self.assertEqual(result[0][2]["templates"], [])


class TestFindExistingAgentFile(unittest.TestCase):
    """Tests for find_existing_agent_file function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.platform_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_finds_unversioned_file(self):
        templates_dir = self.platform_dir / "templates" / "agents"
        templates_dir.mkdir(parents=True)
        agent_file = templates_dir / "agent.md"
        agent_file.write_text("content")

        config = {"currentPath": "templates/agents/agent.md"}
        result = find_existing_agent_file(self.platform_dir, config)
        self.assertEqual(result, agent_file)

    def test_finds_versioned_file_when_unversioned_missing(self):
        templates_dir = self.platform_dir / "templates" / "agents"
        templates_dir.mkdir(parents=True)
        versioned_file = templates_dir / "agent-v1.0.0.md"
        versioned_file.write_text("content")

        config = {
            "currentPath": "templates/agents/agent.md",
            "path": "templates/agents/agent-v{major}.{minor}.{patch}.md"
        }
        result = find_existing_agent_file(self.platform_dir, config)
        self.assertEqual(result, versioned_file)

    def test_returns_none_when_no_file_found(self):
        config = {"currentPath": "templates/agents/agent.md"}
        result = find_existing_agent_file(self.platform_dir, config)
        self.assertIsNone(result)


class TestReadSkillMetadata(unittest.TestCase):
    """Tests for read_skill_metadata function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_reads_all_fields(self):
        skill_md = self.temp_path / "SKILL.md"
        skill_md.write_text(
            '---\nmetadata:\n'
            '  repository: "https://github.com/example/repo"\n'
            '  author: "Alice"\n'
            '  co_authors: "Bob; Carol"\n'
            '---\n'
        )
        result = read_skill_metadata(skill_md)
        self.assertEqual(result["author"], "Alice")
        self.assertEqual(result["co_authors"], "Bob; Carol")
        self.assertEqual(result["repository"], "https://github.com/example/repo")

    def test_returns_empty_for_missing_fields(self):
        skill_md = self.temp_path / "SKILL.md"
        skill_md.write_text('---\nmetadata:\n  spec_version: "1.0"\n---\n')
        result = read_skill_metadata(skill_md)
        self.assertEqual(result["author"], "")
        self.assertEqual(result["co_authors"], "")
        self.assertEqual(result["repository"], "")

    def test_handles_author_only(self):
        skill_md = self.temp_path / "SKILL.md"
        skill_md.write_text('---\nmetadata:\n  author: "Solo Dev"\n---\n')
        result = read_skill_metadata(skill_md)
        self.assertEqual(result["author"], "Solo Dev")
        self.assertEqual(result["co_authors"], "")

    def test_strips_whitespace(self):
        skill_md = self.temp_path / "SKILL.md"
        skill_md.write_text('---\nmetadata:\n  author: "  Spaced  "\n---\n')
        result = read_skill_metadata(skill_md)
        self.assertEqual(result["author"], "Spaced")


class TestBuildAuthorsSuffix(unittest.TestCase):
    """Tests for build_authors_suffix function."""

    def test_full_suffix(self):
        metadata = {
            "author": "Alice",
            "co_authors": "Bob; Carol",
            "repository": "https://github.com/example/repo",
        }
        result = build_authors_suffix(metadata)
        self.assertEqual(
            result,
            "Author: Alice. Co-authors: Bob, Carol. URL: https://github.com/example/repo",
        )

    def test_author_only(self):
        metadata = {"author": "Alice", "co_authors": "", "repository": ""}
        result = build_authors_suffix(metadata)
        self.assertEqual(result, "Author: Alice.")

    def test_no_co_authors(self):
        metadata = {
            "author": "Alice",
            "co_authors": "",
            "repository": "https://github.com/example/repo",
        }
        result = build_authors_suffix(metadata)
        self.assertEqual(result, "Author: Alice. URL: https://github.com/example/repo")

    def test_empty_metadata(self):
        metadata = {"author": "", "co_authors": "", "repository": ""}
        result = build_authors_suffix(metadata)
        self.assertEqual(result, "")

    def test_semicolons_become_commas(self):
        metadata = {"author": "A", "co_authors": "B; C; D", "repository": ""}
        result = build_authors_suffix(metadata)
        self.assertEqual(result, "Author: A. Co-authors: B, C, D.")

    def test_single_co_author(self):
        metadata = {"author": "A", "co_authors": "B", "repository": ""}
        result = build_authors_suffix(metadata)
        self.assertEqual(result, "Author: A. Co-authors: B.")


class TestUpdateAgentFrontmatter(unittest.TestCase):
    """Tests for update_agent_frontmatter function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_updates_quoted_name_field(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text('---\nname: "Old Name"\ndescription: "Old desc"\n---\nContent')

        config = {"name": {"pattern": "New v{major}.{minor}.{patch} Name"}}
        result = update_agent_frontmatter(agent_file, config, "1", "2", "3")

        self.assertTrue(result)
        content = agent_file.read_text()
        self.assertIn('name: "New v1.2.3 Name"', content)

    def test_updates_unquoted_name_field(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text('---\nname: old-name\ndescription: "Old desc"\n---\nContent')

        config = {"name": {"pattern": "new-name-v{major}-{minor}-{patch}"}}
        result = update_agent_frontmatter(agent_file, config, "1", "1", "7")

        self.assertTrue(result)
        content = agent_file.read_text()
        self.assertIn('name: new-name-v1-1-7', content)

    def test_updates_multiple_fields(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text('---\nname: "Old"\ndescription: "Old desc"\n---\nContent')

        config = {
            "name": {"pattern": "APS v{major}.{minor}.{patch}"},
            "description": {"pattern": "Generate APS v{major}.{minor}.{patch} files"}
        }
        result = update_agent_frontmatter(agent_file, config, "2", "0", "0")

        self.assertTrue(result)
        content = agent_file.read_text()
        self.assertIn('name: "APS v2.0.0"', content)
        self.assertIn('description: "Generate APS v2.0.0 files"', content)

    def test_returns_false_when_file_not_found(self):
        config = {"name": {"pattern": "test"}}
        result = update_agent_frontmatter(self.temp_path / "missing.md", config, "1", "0", "0")
        self.assertFalse(result)

    def test_returns_false_when_no_changes_needed(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text('---\nname: "APS v1.0.0"\n---\nContent')

        config = {"name": {"pattern": "APS v{major}.{minor}.{patch}"}}
        result = update_agent_frontmatter(agent_file, config, "1", "0", "0")

        # Should return False since content didn't change
        self.assertFalse(result)

    def test_appends_authors_suffix_to_description(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text(
            '---\nname: "Old"\n'
            'description: "Generate APS v1.0.0 files. Author: Alice. Co-authors: Bob. URL: https://example.com"\n'
            '---\nContent'
        )

        config = {
            "name": {"pattern": "APS v{major}.{minor}.{patch}"},
            "description": {"pattern": "Generate APS v{major}.{minor}.{patch} files."},
        }
        suffix = "Author: Alice. Co-authors: Bob. URL: https://example.com"
        result = update_agent_frontmatter(agent_file, config, "2", "0", "0", authors_suffix=suffix)

        self.assertTrue(result)
        content = agent_file.read_text()
        self.assertIn('name: "APS v2.0.0"', content)
        self.assertIn(
            'description: "Generate APS v2.0.0 files. Author: Alice. Co-authors: Bob. URL: https://example.com"',
            content,
        )

    def test_description_without_suffix_when_empty(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text('---\ndescription: "Old desc"\n---\nContent')

        config = {"description": {"pattern": "Generate APS v{major}.{minor}.{patch} files."}}
        result = update_agent_frontmatter(agent_file, config, "1", "2", "3", authors_suffix="")

        self.assertTrue(result)
        content = agent_file.read_text()
        self.assertIn('description: "Generate APS v1.2.3 files."', content)
        # No trailing space or suffix
        self.assertNotIn("Author:", content)

    def test_suffix_only_applied_to_description_not_name(self):
        agent_file = self.temp_path / "agent.md"
        agent_file.write_text('---\nname: "Old"\ndescription: "Old desc"\n---\nContent')

        config = {
            "name": {"pattern": "APS v{major}.{minor}.{patch}"},
            "description": {"pattern": "Generate v{major}.{minor}.{patch}."},
        }
        suffix = "Author: Alice."
        result = update_agent_frontmatter(agent_file, config, "3", "0", "0", authors_suffix=suffix)

        self.assertTrue(result)
        content = agent_file.read_text()
        # Suffix should NOT appear in name
        self.assertIn('name: "APS v3.0.0"', content)
        self.assertNotIn('name: "APS v3.0.0 Author:', content)
        # Suffix SHOULD appear in description
        self.assertIn('description: "Generate v3.0.0. Author: Alice."', content)


class TestRenameAgentFile(unittest.TestCase):
    """Tests for rename_agent_file function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.platform_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_renames_file_with_version(self):
        templates_dir = self.platform_dir / "templates"
        templates_dir.mkdir()
        source = templates_dir / "agent.md"
        source.write_text("content")

        config = {"path": "templates/agent-v{major}.{minor}.{patch}.md"}
        result = rename_agent_file(self.platform_dir, config, source, "1", "1", "7")

        expected = templates_dir / "agent-v1.1.7.md"
        self.assertEqual(result, expected)
        self.assertTrue(expected.exists())
        self.assertFalse(source.exists())

    def test_creates_parent_directories(self):
        source_dir = self.platform_dir / "old"
        source_dir.mkdir()
        source = source_dir / "agent.md"
        source.write_text("content")

        config = {"path": "new/nested/agent-v{major}.{minor}.{patch}.md"}
        result = rename_agent_file(self.platform_dir, config, source, "2", "0", "0")

        expected = self.platform_dir / "new" / "nested" / "agent-v2.0.0.md"
        self.assertEqual(result, expected)
        self.assertTrue(expected.exists())

    def test_returns_source_when_already_at_target(self):
        templates_dir = self.platform_dir / "templates"
        templates_dir.mkdir()
        source = templates_dir / "agent-v1.0.0.md"
        source.write_text("content")

        config = {"path": "templates/agent-v{major}.{minor}.{patch}.md"}
        result = rename_agent_file(self.platform_dir, config, source, "1", "0", "0")

        self.assertEqual(result, source)
        self.assertTrue(source.exists())

    def test_returns_none_when_no_path_config(self):
        source = self.platform_dir / "agent.md"
        source.write_text("content")

        result = rename_agent_file(self.platform_dir, {}, source, "1", "0", "0")
        self.assertIsNone(result)


class TestUpdatePlatformAgents(unittest.TestCase):
    """End-to-end tests for update_platform_agents function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.platforms_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_adaptor_md(self, platform_dir, templates_json):
        """Helper to create an adaptor.md file with AGENT_VERSIONING block."""
        adaptor_content = (
            "<instructions></instructions>\n"
            "<constants>\n"
            'PLATFORM_ID: "' + platform_dir.name + '"\n'
            'DISPLAY_NAME: "' + platform_dir.name + '"\n'
            "\n"
            "AGENT_VERSIONING: JSON<<\n"
            + json.dumps({"templates": templates_json}, indent=2) + "\n"
            ">>\n"
            "</constants>\n"
            "<formats></formats>"
        )
        (platform_dir / "adaptor.md").write_text(adaptor_content)

    def test_updates_vscode_style_agent(self):
        # Create VS Code style platform
        platform_dir = self.platforms_dir / "vscode-copilot"
        templates_dir = platform_dir / "templates" / ".github" / "agents"
        templates_dir.mkdir(parents=True)

        agent_file = templates_dir / "aps-prompt-protocol.agent.md"
        agent_file.write_text(
            '---\nname: "APS v1.0.0 Agent"\ndescription: "Generate APS v1.0.0 files"\n---\nContent'
        )

        self._make_adaptor_md(platform_dir, [{
            "path": "templates/.github/agents/aps-v{major}.{minor}.{patch}.agent.md",
            "current_path": "templates/.github/agents/aps-prompt-protocol.agent.md",
            "frontmatter": {
                "name_pattern": "APS v{major}.{minor}.{patch} Agent",
                "description_pattern": "Generate APS v{major}.{minor}.{patch} files"
            }
        }])

        result = update_platform_agents(self.platforms_dir, "1.1.7")

        self.assertEqual(len(result), 1)
        new_file = templates_dir / "aps-v1.1.7.agent.md"
        self.assertTrue(new_file.exists())
        content = new_file.read_text()
        self.assertIn('name: "APS v1.1.7 Agent"', content)
        self.assertIn('description: "Generate APS v1.1.7 files"', content)

    def test_updates_claude_style_agent(self):
        # Create Claude Code style platform
        platform_dir = self.platforms_dir / "claude-code"
        templates_dir = platform_dir / "templates" / ".claude" / "agents"
        templates_dir.mkdir(parents=True)

        agent_file = templates_dir / "aps-agent-protocol.md"
        agent_file.write_text(
            '---\nname: aps-agent-protocol\ndescription: "Generate APS v1.0.0 files"\n---\nContent'
        )

        self._make_adaptor_md(platform_dir, [{
            "path": "templates/.claude/agents/aps-v{major}.{minor}.{patch}.md",
            "current_path": "templates/.claude/agents/aps-agent-protocol.md",
            "frontmatter": {
                "name_pattern": "aps-v{major}-{minor}-{patch}",
                "description_pattern": "Generate APS v{major}.{minor}.{patch} files"
            }
        }])

        result = update_platform_agents(self.platforms_dir, "1.1.7")

        self.assertEqual(len(result), 1)
        new_file = templates_dir / "aps-v1.1.7.md"
        self.assertTrue(new_file.exists())
        content = new_file.read_text()
        self.assertIn('name: aps-v1-1-7', content)

    def test_returns_empty_for_invalid_version(self):
        result = update_platform_agents(self.platforms_dir, "invalid")
        self.assertEqual(result, [])

    def test_handles_already_versioned_file(self):
        platform_dir = self.platforms_dir / "test-platform"
        templates_dir = platform_dir / "templates"
        templates_dir.mkdir(parents=True)

        # File already versioned from previous bump
        agent_file = templates_dir / "agent-v1.0.0.md"
        agent_file.write_text('---\nname: "v1.0.0"\n---\nContent')

        self._make_adaptor_md(platform_dir, [{
            "path": "templates/agent-v{major}.{minor}.{patch}.md",
            "current_path": "templates/agent.md",
            "frontmatter": {"name_pattern": "v{major}.{minor}.{patch}"}
        }])

        result = update_platform_agents(self.platforms_dir, "2.0.0")

        new_file = templates_dir / "agent-v2.0.0.md"
        self.assertTrue(new_file.exists())
        self.assertFalse(agent_file.exists())  # Old file should be gone

    def test_updates_adaptor_current_path_after_rename(self):
        """Verify current_path in adaptor.md is updated after file rename."""
        platform_dir = self.platforms_dir / "test-platform"
        templates_dir = platform_dir / "templates"
        templates_dir.mkdir(parents=True)

        # Stale current_path pointing to old version
        agent_file = templates_dir / "agent-v1.0.0.md"
        agent_file.write_text('---\nname: "v1.0.0"\n---\nContent')

        self._make_adaptor_md(platform_dir, [{
            "path": "templates/agent-v{major}.{minor}.{patch}.md",
            "current_path": "templates/agent-v0.9.0.md",
            "frontmatter": {"name_pattern": "v{major}.{minor}.{patch}"}
        }])

        update_platform_agents(self.platforms_dir, "2.0.0")

        # Verify adaptor.md was rewritten with updated current_path
        adaptor_text = (platform_dir / "adaptor.md").read_text(encoding="utf-8")
        versioning = _parse_adaptor_json_block(adaptor_text, "AGENT_VERSIONING")
        self.assertIsNotNone(versioning)
        current_path = versioning["templates"][0]["current_path"]
        self.assertEqual(current_path, "templates/agent-v2.0.0.md")

    def test_appends_authors_suffix_to_description(self):
        """End-to-end: authors suffix is appended to description during bump."""
        platform_dir = self.platforms_dir / "test-platform"
        templates_dir = platform_dir / "templates"
        templates_dir.mkdir(parents=True)

        agent_file = templates_dir / "agent-v1.0.0.md"
        agent_file.write_text(
            '---\n'
            'name: "v1.0.0"\n'
            'description: "Generate v1.0.0 files. Author: Alice. URL: https://example.com"\n'
            '---\nContent'
        )

        self._make_adaptor_md(platform_dir, [{
            "path": "templates/agent-v{major}.{minor}.{patch}.md",
            "current_path": "templates/agent.md",
            "frontmatter": {
                "name_pattern": "v{major}.{minor}.{patch}",
                "description_pattern": "Generate v{major}.{minor}.{patch} files."
            }
        }])

        suffix = "Author: Alice. URL: https://example.com"
        result = update_platform_agents(self.platforms_dir, "2.0.0", authors_suffix=suffix)

        new_file = templates_dir / "agent-v2.0.0.md"
        self.assertTrue(new_file.exists())
        content = new_file.read_text()
        self.assertIn(
            'description: "Generate v2.0.0 files. Author: Alice. URL: https://example.com"',
            content,
        )


class TestSemverRegex(unittest.TestCase):
    """Tests for SEMVER_RE regex pattern."""

    def test_valid_versions(self):
        valid = ["0.0.0", "1.0.0", "1.2.3", "10.20.30", "1.1.7"]
        for v in valid:
            with self.subTest(version=v):
                self.assertIsNotNone(SEMVER_RE.match(v))

    def test_invalid_versions(self):
        invalid = ["1.0", "1", "v1.0.0", "1.0.0-beta", "01.0.0", "1.2.3.4"]
        for v in invalid:
            with self.subTest(version=v):
                self.assertIsNone(SEMVER_RE.match(v))


if __name__ == "__main__":
    unittest.main()
