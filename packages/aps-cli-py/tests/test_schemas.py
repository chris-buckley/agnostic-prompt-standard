"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from aps_cli.schemas import (
    PlatformManifest,
    SkillFrontmatter,
    parse_platform_manifest,
    parse_skill_frontmatter,
    safe_parse_platform_manifest,
    safe_parse_skill_frontmatter,
    normalize_detection_marker,
)


class TestPlatformManifest:
    def test_valid_minimal_manifest(self):
        data = {
            "platformId": "test-platform",
            "displayName": "Test Platform",
        }
        manifest = parse_platform_manifest(data)
        assert manifest.platform_id == "test-platform"
        assert manifest.display_name == "Test Platform"
        assert manifest.adapter_version is None

    def test_valid_full_manifest(self):
        data = {
            "platformId": "test-platform",
            "displayName": "Test Platform",
            "adapterVersion": "1.0.0",
            "description": "A test platform",
            "detectionMarkers": [
                {"kind": "file", "label": ".test", "relPath": ".test"},
                {"kind": "dir", "label": ".test/", "relPath": ".test"},
            ],
        }
        manifest = parse_platform_manifest(data)
        assert manifest.platform_id == "test-platform"
        assert manifest.adapter_version == "1.0.0"
        assert manifest.detection_markers_raw is not None
        assert len(manifest.detection_markers_raw) == 2
        # Check normalized markers
        markers = manifest.detection_markers
        assert len(markers) == 2
        assert markers[0].kind == "file"
        assert markers[0].rel_path == ".test"

    def test_valid_manifest_with_string_markers(self):
        """Test that string markers are accepted and normalized."""
        data = {
            "platformId": "test-platform",
            "displayName": "Test Platform",
            "detectionMarkers": [
                ".github/copilot-instructions.md",
                ".github/agents/",
            ],
        }
        manifest = parse_platform_manifest(data)
        markers = manifest.detection_markers
        assert len(markers) == 2
        assert markers[0].kind == "file"
        assert markers[0].rel_path == ".github/copilot-instructions.md"
        assert markers[1].kind == "dir"
        assert markers[1].rel_path == ".github/agents"

    def test_missing_platform_id_raises(self):
        data = {"displayName": "Test Platform"}
        with pytest.raises(ValidationError):
            parse_platform_manifest(data)

    def test_missing_display_name_raises(self):
        data = {"platformId": "test-platform"}
        with pytest.raises(ValidationError):
            parse_platform_manifest(data)

    def test_empty_platform_id_raises(self):
        data = {"platformId": "", "displayName": "Test Platform"}
        with pytest.raises(ValidationError):
            parse_platform_manifest(data)

    def test_invalid_marker_handled_gracefully(self):
        """Test that invalid marker objects are rejected (match Node strictness)."""
        data = {
            "platformId": "test-platform",
            "displayName": "Test Platform",
            "detectionMarkers": [
                {"kind": "invalid", "label": ".test", "relPath": ".test"},
            ],
        }
        # Use safe parse to avoid throwing in callers.
        manifest, error = safe_parse_platform_manifest(data)
        assert manifest is None
        assert error is not None

    def test_safe_parse_returns_none_on_error(self):
        data = {"displayName": "Test Platform"}
        manifest, error = safe_parse_platform_manifest(data)
        assert manifest is None
        assert error is not None

    def test_safe_parse_returns_manifest_on_success(self):
        data = {"platformId": "test", "displayName": "Test"}
        manifest, error = safe_parse_platform_manifest(data)
        assert manifest is not None
        assert error is None
        assert manifest.platform_id == "test"


class TestNormalizeDetectionMarker:
    def test_normalize_string_file(self):
        marker = normalize_detection_marker(".github/copilot-instructions.md")
        assert marker.kind == "file"
        assert marker.label == ".github/copilot-instructions.md"
        assert marker.rel_path == ".github/copilot-instructions.md"

    def test_normalize_string_dir(self):
        marker = normalize_detection_marker(".github/agents/")
        assert marker.kind == "dir"
        assert marker.label == ".github/agents/"
        assert marker.rel_path == ".github/agents"

    def test_normalize_dict(self):
        marker = normalize_detection_marker({
            "kind": "file",
            "label": "CLAUDE.md",
            "relPath": "CLAUDE.md",
        })
        assert marker.kind == "file"
        assert marker.label == "CLAUDE.md"
        assert marker.rel_path == "CLAUDE.md"


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