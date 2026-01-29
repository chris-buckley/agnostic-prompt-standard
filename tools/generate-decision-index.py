#!/usr/bin/env python3
"""Generate the ADR decision index from individual ADR files.

Extracts all **Decision:** statements from ADR files and generates
a definition-list-style index in 0000-decision-index.md.

Usage:
    python tools/generate_decision_index.py                    # Auto-detect ADR dir
    python tools/generate_decision_index.py --adr-dir ./docs/adr
    python tools/generate_decision_index.py --dry-run          # Preview without writing
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Decision:
    """A single decision extracted from an ADR."""

    adr_number: str
    section_number: int
    section_title: str
    decision_text: str
    filename: str

    @property
    def anchor(self) -> str:
        """Generate the markdown anchor for linking to this section."""
        # GitHub/most renderers: lowercase, spaces to hyphens, strip special chars
        slug = self.section_title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug.strip())
        return f"{self.section_number}-{slug}"


# Patterns for extraction
ADR_FILENAME_RE = re.compile(r"^(\d{4})-(.+)\.md$")
SECTION_HEADING_RE = re.compile(r"^###\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
DECISION_RE = re.compile(r"\*\*Decision:\*\*\s*(.+?)(?:\n\n|\n\*\*|\Z)", re.DOTALL)


def extract_adr_number(filename: str) -> str | None:
    """Extract the ADR number from a filename like '0003-foo-bar.md'."""
    m = ADR_FILENAME_RE.match(filename)
    return m.group(1) if m else None


def extract_decisions(adr_path: Path) -> list[Decision]:
    """Extract all decisions from a single ADR file."""
    adr_number = extract_adr_number(adr_path.name)
    if not adr_number:
        return []

    text = adr_path.read_text(encoding="utf-8")
    decisions: list[Decision] = []

    # Find all section headings
    sections = list(SECTION_HEADING_RE.finditer(text))

    for i, section_match in enumerate(sections):
        section_num = int(section_match.group(1))
        section_title = section_match.group(2).strip()

        # Get the content between this section and the next (or end of file)
        start = section_match.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        section_content = text[start:end]

        # Look for **Decision:** in this section
        decision_match = DECISION_RE.search(section_content)
        if decision_match:
            decision_text = decision_match.group(1).strip()
            # Clean up: remove newlines, collapse whitespace
            decision_text = re.sub(r"\s+", " ", decision_text)

            decisions.append(
                Decision(
                    adr_number=adr_number,
                    section_number=section_num,
                    section_title=section_title,
                    decision_text=decision_text,
                    filename=adr_path.name,
                )
            )

    return decisions


def generate_index(decisions: list[Decision]) -> str:
    """Generate the markdown content for the decision index."""
    lines = [
        "# ADR Decision Index",
        "",
        "This index is auto-generated from individual ADR files.",
        "Run `python tools/generate_decision_index.py` to regenerate.",
        "",
        "---",
        "",
    ]

    for i, d in enumerate(decisions, start=1):
        decision_id = f"D{i:03d}"
        source_link = f"[ADR-{d.adr_number} §{d.section_number}]({d.filename}#{d.anchor})"

        lines.append(f"**{decision_id}** — {d.section_title}  ")
        lines.append(f": {d.decision_text}  ")
        lines.append(f": *Source:* {source_link}")
        lines.append("")

    return "\n".join(lines)


def find_adr_dir() -> Path | None:
    """Try to auto-detect the ADR directory."""
    candidates = [
        Path(__file__).resolve().parents[1] / "docs" / "adr",
        Path.cwd() / "docs" / "adr",
        Path.cwd() / "adr",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate ADR decision index")
    ap.add_argument("--adr-dir", type=Path, help="Path to ADR directory")
    ap.add_argument("--dry-run", action="store_true", help="Print output without writing")
    ap.add_argument("--output", type=Path, help="Output file (default: 0000-decision-index.md in ADR dir)")
    args = ap.parse_args()

    # Determine ADR directory
    adr_dir = args.adr_dir or find_adr_dir()
    if not adr_dir or not adr_dir.is_dir():
        print("Error: Could not find ADR directory. Use --adr-dir to specify.")
        return 1

    print(f"Scanning ADR directory: {adr_dir}")

    # Find all ADR files (excluding the index itself)
    adr_files = sorted(
        f for f in adr_dir.glob("*.md") if ADR_FILENAME_RE.match(f.name) and "decision-index" not in f.name
    )

    if not adr_files:
        print("No ADR files found.")
        return 1

    print(f"Found {len(adr_files)} ADR file(s)")

    # Extract decisions from all files
    all_decisions: list[Decision] = []
    for adr_file in adr_files:
        decisions = extract_decisions(adr_file)
        if decisions:
            print(f"  {adr_file.name}: {len(decisions)} decision(s)")
            all_decisions.extend(decisions)

    if not all_decisions:
        print("No decisions found in ADR files.")
        print("Hint: Ensure decisions use the format: **Decision:** <text>")
        return 1

    print(f"\nTotal decisions: {len(all_decisions)}")

    # Generate index content
    index_content = generate_index(all_decisions)

    if args.dry_run:
        print("\n--- Generated Index (dry run) ---\n")
        print(index_content)
        return 0

    # Write the index file
    output_path = args.output or adr_dir / "0000-decision-index.md"
    output_path.write_text(index_content, encoding="utf-8")
    print(f"\nWrote decision index to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())