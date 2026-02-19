"""Parse adaptor.md files into structured data.

Handles <instructions>, <constants>, and <formats> sections including
TEXT, JSON, CSV, and YAML block constant types.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

ConstantValue = Union[str, int, float, bool, list, dict]

SECTION_RE = re.compile(
    r"<(instructions|constants|formats)>(.*?)</\1>", re.DOTALL
)
FORMAT_TAG_RE = re.compile(
    r'<format\s+id="([^"]+)"'
    r'(?:\s+name="([^"]*)")?'
    r'(?:\s+purpose="([^"]*)")?\s*>'
    r"(.*?)</format>",
    re.DOTALL,
)


@dataclass(frozen=True)
class FormatContract:
    """A parsed format block from adaptor.md."""

    id: str
    name: str
    purpose: str
    body: str


@dataclass
class AdaptorData:
    """Complete parsed adaptor.md content."""

    instructions: str = ""
    constants: dict[str, ConstantValue] = field(default_factory=dict)
    formats: dict[str, FormatContract] = field(default_factory=dict)


def _split_csv_row(line: str) -> list[str]:
    """Split a CSV row respecting quoted fields."""
    reader = csv.reader(io.StringIO(line))
    for row in reader:
        return list(row)
    return []


def _parse_csv_block(body: str) -> list[dict[str, str]]:
    """Parse CSV block into list of dicts keyed by header."""
    lines = [l for l in body.strip().splitlines() if l.strip()]
    if not lines:
        return []

    headers = _split_csv_row(lines[0])
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        cells = _split_csv_row(line)
        row = {headers[j]: (cells[j] if j < len(cells) else "") for j in range(len(headers))}
        rows.append(row)
    return rows


def _parse_constants(raw: str) -> dict[str, ConstantValue]:
    """Parse the constants section text."""
    constants: dict[str, ConstantValue] = {}
    lines = raw.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        trimmed = line.strip()

        if not trimmed or trimmed.startswith("//") or trimmed.startswith("#"):
            i += 1
            continue

        colon_idx = trimmed.find(":")
        if colon_idx == -1:
            i += 1
            continue

        key = trimmed[:colon_idx].strip()
        rest = trimmed[colon_idx + 1 :].strip()

        # Block constants
        block_match = re.match(r"^(JSON|TEXT|CSV|YAML)<<$", rest)
        if block_match:
            block_type = block_match.group(1)
            body_lines: list[str] = []
            i += 1
            while i < len(lines):
                if lines[i].strip() == ">>":
                    i += 1
                    break
                body_lines.append(lines[i])
                i += 1
            body = "\n".join(body_lines)

            if block_type == "JSON":
                try:
                    constants[key] = json.loads(body)
                except json.JSONDecodeError:
                    constants[key] = body
            elif block_type == "CSV":
                constants[key] = _parse_csv_block(body)
            else:
                constants[key] = body
            continue

        # Inline array
        if rest.startswith("["):
            try:
                constants[key] = json.loads(rest)
            except json.JSONDecodeError:
                constants[key] = rest
            i += 1
            continue

        # Quoted string
        if (rest.startswith('"') and rest.endswith('"')) or (
            rest.startswith("'") and rest.endswith("'")
        ):
            constants[key] = rest[1:-1]
            i += 1
            continue

        # Boolean
        if rest == "true":
            constants[key] = True
            i += 1
            continue
        if rest == "false":
            constants[key] = False
            i += 1
            continue

        # Number
        try:
            if "." in rest:
                constants[key] = float(rest)
            else:
                constants[key] = int(rest)
            i += 1
            continue
        except ValueError:
            pass

        # Bare string
        constants[key] = rest
        i += 1

    return constants


def _parse_formats(raw: str) -> dict[str, FormatContract]:
    """Parse the formats section text."""
    formats: dict[str, FormatContract] = {}
    for m in FORMAT_TAG_RE.finditer(raw):
        fid = m.group(1)
        formats[fid] = FormatContract(
            id=fid,
            name=m.group(2) or "",
            purpose=m.group(3) or "",
            body=(m.group(4) or "").strip(),
        )
    return formats


def parse_adaptor_md(file_path: Path) -> AdaptorData:
    """Parse an adaptor.md file into structured data.

    Args:
        file_path: Path to the adaptor.md file.

    Returns:
        Parsed AdaptorData.
    """
    raw = file_path.read_text(encoding="utf-8")
    return parse_adaptor_md_string(raw)


def parse_adaptor_md_string(raw: str) -> AdaptorData:
    """Parse adaptor.md content string into structured data.

    Args:
        raw: Raw adaptor.md content.

    Returns:
        Parsed AdaptorData.
    """
    data = AdaptorData()

    for m in SECTION_RE.finditer(raw):
        section = m.group(1)
        content = m.group(2) or ""

        if section == "instructions":
            data.instructions = content.strip()
        elif section == "constants":
            data.constants = _parse_constants(content)
        elif section == "formats":
            data.formats = _parse_formats(content)

    return data


def get_string(constants: dict[str, Any], key: str, fallback: str = "") -> str:
    """Extract a string constant or return a default."""
    v = constants.get(key)
    return v if isinstance(v, str) else fallback


def get_string_array(constants: dict[str, Any], key: str) -> list[str]:
    """Extract a string array constant or return empty list."""
    v = constants.get(key)
    if isinstance(v, list):
        return [item for item in v if isinstance(item, str)]
    return []
