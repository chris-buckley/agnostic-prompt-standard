"""Tests that every platform adapter has a valid adaptor.md."""

from pathlib import Path

from aps_cli.parsers.adaptor import get_string, parse_adaptor_md

PLATFORMS_DIR = (
    Path(__file__).resolve().parents[3]
    / "skill"
    / "agnostic-prompt-standard"
    / "platforms"
)


def test_every_platform_has_adaptor_md():
    """Every non-underscore platform directory must have an adaptor.md file."""
    for entry in sorted(PLATFORMS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        adaptor_path = entry / "adaptor.md"
        assert adaptor_path.exists(), f"{entry.name}/ is missing adaptor.md"


def test_every_adaptor_has_required_constants():
    """Every adaptor.md must define PLATFORM_ID and DISPLAY_NAME constants."""
    for entry in sorted(PLATFORMS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        adaptor_path = entry / "adaptor.md"
        if not adaptor_path.exists():
            continue
        data = parse_adaptor_md(adaptor_path)
        pid = get_string(data.constants, "PLATFORM_ID")
        name = get_string(data.constants, "DISPLAY_NAME")
        assert pid, f"{entry.name}/adaptor.md is missing PLATFORM_ID constant"
        assert name, f"{entry.name}/adaptor.md is missing DISPLAY_NAME constant"
