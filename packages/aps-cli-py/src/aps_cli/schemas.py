"""Pydantic v2 schemas for skill validation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError


class SkillFrontmatter(BaseModel):
    """Schema for SKILL.md frontmatter."""

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None


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
