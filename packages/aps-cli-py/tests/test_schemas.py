"""Tests for Pydantic schema validation."""

from aps_cli.schemas import (
    parse_skill_frontmatter,
    safe_parse_skill_frontmatter,
)


class TestSkillFrontmatter:
    def test_valid_frontmatter(self):
        data = {
            "name": "Test Skill",
            "version": "1.0.0",
            "description": "A test skill",
        }
        frontmatter = parse_skill_frontmatter(data)
        assert frontmatter.name == "Test Skill"
        assert frontmatter.version == "1.0.0"

    def test_empty_frontmatter_is_valid(self):
        data = {}
        frontmatter = parse_skill_frontmatter(data)
        assert frontmatter.name is None
        assert frontmatter.version is None

    def test_extra_fields_are_allowed(self):
        data = {
            "name": "Test",
            "custom_field": "custom_value",
        }
        frontmatter = parse_skill_frontmatter(data)
        assert frontmatter.name == "Test"
        # Extra fields are accessible via model_extra
        assert "custom_field" in frontmatter.model_extra

    def test_safe_parse_returns_frontmatter(self):
        data = {"name": "Test"}
        frontmatter, error = safe_parse_skill_frontmatter(data)
        assert frontmatter is not None
        assert error is None
