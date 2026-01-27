"""Pydantic v2 schemas for manifest and skill validation."""

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class FileConventions(BaseModel):
    """File convention paths for a platform."""

    instructions: Optional[list[str]] = None
    agents: Optional[list[str]] = None
    prompts: Optional[list[str]] = None
    skills: Optional[list[str]] = None


class DetectionMarkerObject(BaseModel):
    """A marker file or directory used to detect a platform (object format)."""

    model_config = ConfigDict(populate_by_name=True)

    kind: str = Field(..., pattern="^(file|dir)$")
    label: str
    rel_path: str = Field(..., alias="relPath")


class DetectionMarker(BaseModel):
    """Normalized detection marker with all fields."""

    kind: str
    label: str
    rel_path: str


def normalize_detection_marker(
    input_marker: Union[str, dict, DetectionMarkerObject],
) -> DetectionMarker:
    """Convert a detection marker input (string or object) to normalized format.

    Args:
        input_marker: String path or marker object/dict

    Returns:
        Normalized DetectionMarker
    """
    if isinstance(input_marker, str):
        # String format: ".github/agents/" -> dir, ".github/copilot-instructions.md" -> file
        is_dir = input_marker.endswith("/")
        rel_path = input_marker.rstrip("/") if is_dir else input_marker
        return DetectionMarker(
            kind="dir" if is_dir else "file",
            label=input_marker,
            rel_path=rel_path,
        )
    elif isinstance(input_marker, DetectionMarkerObject):
        return DetectionMarker(
            kind=input_marker.kind,
            label=input_marker.label,
            rel_path=input_marker.rel_path,
        )
    elif isinstance(input_marker, dict):
        return DetectionMarker(
            kind=input_marker.get("kind", "file"),
            label=input_marker.get("label", ""),
            rel_path=input_marker.get("relPath", input_marker.get("rel_path", "")),
        )
    else:
        raise ValueError(f"Invalid detection marker type: {type(input_marker)}")


class PlatformManifest(BaseModel):
    """Schema for platform manifest.json files."""

    model_config = ConfigDict(populate_by_name=True)

    platform_id: str = Field(..., min_length=1, alias="platformId")
    display_name: str = Field(..., min_length=1, alias="displayName")
    adapter_version: Optional[str] = Field(None, alias="adapterVersion")
    description: Optional[str] = None
    skill_root: Optional[str] = Field(None, alias="skillRoot")
    file_conventions: Optional[FileConventions] = Field(None, alias="fileConventions")
    detection_markers_raw: Optional[list[Union[str, dict]]] = Field(
        None, alias="detectionMarkers"
    )

    @property
    def detection_markers(self) -> list[DetectionMarker]:
        """Get normalized detection markers."""
        if not self.detection_markers_raw:
            return []
        return [normalize_detection_marker(m) for m in self.detection_markers_raw]


class SkillFrontmatter(BaseModel):
    """Schema for SKILL.md frontmatter."""

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None


def parse_platform_manifest(data: dict) -> PlatformManifest:
    """Parse and validate a platform manifest.

    Args:
        data: Raw manifest data

    Returns:
        Validated PlatformManifest

    Raises:
        ValidationError: If validation fails
    """
    return PlatformManifest.model_validate(data)


def safe_parse_platform_manifest(
    data: dict,
) -> tuple[Optional[PlatformManifest], Optional[ValidationError]]:
    """Safely parse a platform manifest without raising.

    Args:
        data: Raw manifest data

    Returns:
        Tuple of (manifest, error) - one will be None
    """
    try:
        return parse_platform_manifest(data), None
    except ValidationError as e:
        return None, e


def parse_skill_frontmatter(data: dict) -> SkillFrontmatter:
    """Parse and validate skill frontmatter.

    Args:
        data: Raw frontmatter data

    Returns:
        Validated SkillFrontmatter

    Raises:
        ValidationError: If validation fails
    """
    return SkillFrontmatter.model_validate(data)


def safe_parse_skill_frontmatter(
    data: dict,
) -> tuple[Optional[SkillFrontmatter], Optional[ValidationError]]:
    """Safely parse skill frontmatter without raising.

    Args:
        data: Raw frontmatter data

    Returns:
        Tuple of (frontmatter, error) - one will be None
    """
    try:
        return parse_skill_frontmatter(data), None
    except ValidationError as e:
        return None, e