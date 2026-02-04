"""Tests for CLI functions."""

from aps_cli.cli import _render_empty_platform_warning


def test_render_empty_platform_warning_returns_warning_message():
    """Warning message includes expected content."""
    warning = _render_empty_platform_warning()
    assert "No platform adapters selected" in warning
    assert "Only the APS skill will be installed" in warning
    assert "Templates will not be copied" in warning


def test_render_empty_platform_warning_mentions_platform_flag():
    """Warning message mentions --platform flag."""
    warning = _render_empty_platform_warning()
    assert "--platform" in warning
