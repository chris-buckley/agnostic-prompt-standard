"""Tests that validate platform adapter file conventions."""

from __future__ import annotations

import re
from pathlib import Path

from aps_cli.parsers.adaptor import parse_adaptor_md

PLATFORMS_DIR = (
    Path(__file__).resolve().parents[3]
    / "skill"
    / "agnostic-prompt-standard"
    / "platforms"
)

FORMAT_ID_RE = re.compile(r'<format\b[^>]*\bid="([^"]+)"')


def _platform_dirs() -> list[Path]:
    return [
        p
        for p in PLATFORMS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    ]


def test_each_platform_has_adaptor_md():
    if not PLATFORMS_DIR.exists():
        return

    for platform in _platform_dirs():
        adaptor = platform / "adaptor.md"
        assert adaptor.exists(), f"Missing adaptor.md in {platform.name}"


def test_adaptor_has_required_constants():
    if not PLATFORMS_DIR.exists():
        return

    for platform in _platform_dirs():
        data = parse_adaptor_md(platform / "adaptor.md")
        assert isinstance(data.constants.get("PLATFORM_ID"), str)
        assert isinstance(data.constants.get("DISPLAY_NAME"), str)
        assert isinstance(data.constants.get("ADAPTER_VERSION"), str)


def test_adaptor_has_unique_format_ids():
    if not PLATFORMS_DIR.exists():
        return

    for platform in _platform_dirs():
        raw = (platform / "adaptor.md").read_text(encoding="utf-8")
        ids = FORMAT_ID_RE.findall(raw)
        assert len(ids) == len(set(ids)), f"Duplicate <format id> values in {platform.name}"


def test_agent_versioning_is_valid_json_when_present():
    if not PLATFORMS_DIR.exists():
        return

    for platform in _platform_dirs():
        data = parse_adaptor_md(platform / "adaptor.md")
        if "AGENT_VERSIONING" not in data.constants:
            continue

        av = data.constants["AGENT_VERSIONING"]
        assert isinstance(av, dict), f"AGENT_VERSIONING must be an object in {platform.name}"
        templates = av.get("templates")
        assert isinstance(templates, list), f"AGENT_VERSIONING.templates must be a list in {platform.name}"

def test_subagent_authoring_guide_is_present():
    if not PLATFORMS_DIR.exists():
        return

    for platform in _platform_dirs():
        data = parse_adaptor_md(platform / "adaptor.md")
        guide = data.constants.get("SUBAGENT_AUTHORING_GUIDE")
        assert isinstance(guide, str) and guide.strip(), f"Missing SUBAGENT_AUTHORING_GUIDE in {platform.name}"


def test_subagent_architecture_is_valid_json_object():
    if not PLATFORMS_DIR.exists():
        return

    for platform in _platform_dirs():
        data = parse_adaptor_md(platform / "adaptor.md")
        arch = data.constants.get("SUBAGENT_ARCHITECTURE")
        assert isinstance(arch, dict), f"SUBAGENT_ARCHITECTURE must be an object in {platform.name}"
