#!/usr/bin/env python3
"""
Universal extractor for APS "formats" by id.

Supports two related but distinct things:

1) Contract extraction:
   Find a `<format id="..."> ... </format>` definition in a directory of files.

2) Rendered output extraction:
   Find a fenced markdown block ```format:<ID> ... ``` by id.

Designed for automation:
- Standard library only (no dependencies)
- Deterministic output
- Works on macOS/Linux/Windows

Examples
--------
# 1) Extract a contract from a repo/skill directory:
python tools/extract_format.py contract --id CODE_MAP_V1 --root skill/agnostic-prompt-standard --mode raw

# 2) Extract a rendered block from a model response file:
python tools/extract_format.py block --id TABLE_API_COVERAGE_V1 --file response.md --mode body

# 3) Pipe a response in via stdin:
cat response.md | python tools/extract_format.py block --id HELLO_V1
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# -------------------------
# Shared helpers / patterns
# -------------------------

ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
OPEN_FORMAT_RE = re.compile(r"<format\b", re.IGNORECASE)
CLOSE_FORMAT = "</format>"

WHERE_LINE_RE = re.compile(r"^\s*WHERE:\s*$", re.IGNORECASE | re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"<([A-Z0-9_]{1,64})>")

FENCE_OPEN_RE = re.compile(r"^(?P<fence>`{3,})format:(?P<id>[^\s`]+)\s*$")
FENCE_CLOSE_RE = re.compile(r"^(?P<fence>`{3,})\s*$")


def _read_text(p: Path) -> str:
    # Use 'replace' to avoid hard failures on odd encodings.
    return p.read_text(encoding="utf-8", errors="replace")


def _posix(p: Path) -> str:
    # Stable output across OSes.
    return p.as_posix()


def _iter_files(root: Path, patterns: Sequence[str]) -> Iterable[Path]:
    """Yield unique files under root matching any glob pattern."""
    seen: set[Path] = set()
    for pat in patterns:
        for p in root.glob(pat):
            if not p.is_file():
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p


def _parse_attrs(open_tag: str) -> Dict[str, str]:
    return {k: v for (k, v) in ATTR_RE.findall(open_tag)}


def _split_where(body: str) -> Tuple[str, Dict[str, str], List[str], List[str], List[str], List[str], List[str]]:
    """
    Split a <format> body into the main contract body and the WHERE section.

    Returns:
      - contract_body: body without WHERE section (if present)
      - where_map: placeholder -> raw constraint line text (best-effort)
      - placeholders_in_body: unique placeholder names found in contract_body
      - where_placeholders: placeholder names defined anywhere in WHERE lines
      - where_missing: placeholders used but not defined
      - where_extra: placeholders defined but not used
      - where_duplicates: placeholders defined more than once
    """
    where_map: Dict[str, str] = {}
    where_placeholders: List[str] = []
    duplicates: List[str] = []

    m = WHERE_LINE_RE.search(body)
    if not m:
        contract_body = body
        placeholders = sorted(set(PLACEHOLDER_RE.findall(contract_body)))
        return contract_body, {}, placeholders, [], placeholders, [], []

    contract_body = body[: m.start()]
    where_body = body[m.end() :]

    # Pragmatic parsing:
    # - APS recommends one placeholder per WHERE line, but some real-world contracts
    #   (and examples) mention multiple placeholders on a single definition line.
    # - We treat *any* placeholders mentioned on a "- ..." line as being "defined"
    #   by that line, and store the raw line text as the "constraint".
    for line in where_body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        phs = PLACEHOLDER_RE.findall(line)
        if not phs:
            continue
        constraint = stripped[1:].strip()  # remove leading '-'
        for ph in phs:
            if ph in where_map:
                duplicates.append(ph)
            else:
                where_map[ph] = constraint
            where_placeholders.append(ph)

    placeholders = sorted(set(PLACEHOLDER_RE.findall(contract_body)))
    where_keys = sorted(set(where_placeholders))

    missing = sorted(set(placeholders) - set(where_keys))
    extra = sorted(set(where_keys) - set(placeholders))
    duplicates = sorted(set(duplicates))

    return contract_body, where_map, placeholders, where_keys, missing, extra, duplicates


@dataclass(frozen=True)
class FormatContract:
    id: str
    name: Optional[str]
    purpose: Optional[str]
    attrs: Dict[str, str]
    file: str
    start_offset: int
    end_offset: int
    block: str
    body: str
    contract_body: str
    where: Dict[str, str]
    placeholders: List[str]
    where_missing: List[str]
    where_extra: List[str]
    where_duplicates: List[str]


def extract_format_contracts_from_text(text: str, *, file_label: str = "<memory>") -> List[FormatContract]:
    """
    Extract *all* <format ...>...</format> blocks found in a text blob.

    Notes:
    - This is a pragmatic extractor, not a full XML parser.
    - Assumes no nested <format> tags.
    """
    out: List[FormatContract] = []
    pos = 0
    while True:
        m = OPEN_FORMAT_RE.search(text, pos)
        if not m:
            break

        open_start = m.start()
        open_end = text.find(">", m.end())
        if open_end == -1:
            break

        close_start = text.find(CLOSE_FORMAT, open_end)
        if close_start == -1:
            break

        close_end = close_start + len(CLOSE_FORMAT)

        open_tag = text[open_start : open_end + 1]
        attrs = _parse_attrs(open_tag)

        fmt_id = attrs.get("id")
        if fmt_id:
            body = text[open_end + 1 : close_start]
            contract_body, where_map, placeholders, where_keys, missing, extra, dups = _split_where(body)

            out.append(
                FormatContract(
                    id=fmt_id,
                    name=attrs.get("name"),
                    purpose=attrs.get("purpose"),
                    attrs=attrs,
                    file=file_label,
                    start_offset=open_start,
                    end_offset=close_end,
                    block=text[open_start:close_end],
                    body=body,
                    contract_body=contract_body,
                    where=where_map,
                    placeholders=placeholders,
                    where_missing=missing,
                    where_extra=extra,
                    where_duplicates=dups,
                )
            )

        pos = close_end

    return out


def find_format_contracts(
    root: Path,
    fmt_id: str,
    *,
    patterns: Sequence[str],
    prefer_paths_containing: Sequence[str] = ("skill/agnostic-prompt-standard/assets/formats", "assets/formats"),
) -> List[FormatContract]:
    """Search a directory tree for <format id="..."> definitions matching fmt_id."""
    matches: List[FormatContract] = []

    for p in _iter_files(root, patterns):
        text = _read_text(p)
        # Fast prefilter.
        if fmt_id not in text and f'id="{fmt_id}"' not in text:
            continue
        for fc in extract_format_contracts_from_text(text, file_label=_posix(p)):
            if fc.id == fmt_id:
                matches.append(fc)

    # Deterministic ordering.
    matches.sort(key=lambda m: (m.file, m.start_offset))

    # Prefer certain canonical locations (e.g. assets/formats) if ambiguous.
    if len(matches) > 1 and prefer_paths_containing:
        scored: List[Tuple[int, FormatContract]] = []
        for m in matches:
            path_l = m.file.lower()
            score = 0
            for needle in prefer_paths_containing:
                if needle.lower() in path_l:
                    score += 10
            scored.append((score, m))
        scored.sort(key=lambda t: (-t[0], t[1].file, t[1].start_offset))
        best_score = scored[0][0]
        best = [m for (s, m) in scored if s == best_score]
        if len(best) == 1:
            return best

    return matches


@dataclass(frozen=True)
class RenderedFormatBlock:
    id: str
    fence: str
    start_line: int
    end_line: int
    block: str
    body: str


def extract_rendered_format_blocks_from_text(text: str) -> List[RenderedFormatBlock]:
    """
    Extract all fenced blocks whose info string matches `format:<ID>`.

    A block is:

        ```format:ID
        ...
        ```

    Fence length may be 3+ backticks; closing fence must match opening fence length.
    """
    lines = text.splitlines()
    out: List[RenderedFormatBlock] = []
    i = 0
    while i < len(lines):
        m = FENCE_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue

        fence = m.group("fence")
        fmt_id = m.group("id")
        start_line = i + 1  # 1-indexed for humans

        # Find closing fence of same length.
        j = i + 1
        while j < len(lines):
            if lines[j].startswith(fence) and FENCE_CLOSE_RE.match(lines[j]):
                break
            j += 1
        if j >= len(lines):
            # Unterminated; treat as no match and continue scanning after start.
            i += 1
            continue

        end_line = j + 1  # inclusive
        body_lines = lines[i + 1 : j]
        body = "\n".join(body_lines)
        block = "\n".join(lines[i : j + 1])

        out.append(
            RenderedFormatBlock(
                id=fmt_id,
                fence=fence,
                start_line=start_line,
                end_line=end_line,
                block=block,
                body=body,
            )
        )
        i = j + 1

    return out


def find_rendered_block(text: str, fmt_id: str) -> List[RenderedFormatBlock]:
    return [b for b in extract_rendered_format_blocks_from_text(text) if b.id == fmt_id]


# -------------------------
# CLI output helpers
# -------------------------

def _print_json(obj: object) -> None:
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def _closest_ids(candidates: Sequence[str], target: str, n: int = 5) -> List[str]:
    return difflib.get_close_matches(target, list(candidates), n=n, cutoff=0.0)


def _render_contract(fc: FormatContract, mode: str) -> None:
    if mode == "raw":
        sys.stdout.write(fc.block)
        if not fc.block.endswith("\n"):
            sys.stdout.write("\n")
        return
    if mode == "body":
        sys.stdout.write(fc.body)
        if not fc.body.endswith("\n"):
            sys.stdout.write("\n")
        return
    if mode == "where":
        _print_json(fc.where)
        return
    if mode == "json":
        _print_json(asdict(fc))
        return
    raise ValueError(f"Unknown mode: {mode}")


def _render_block(b: RenderedFormatBlock, mode: str) -> None:
    if mode == "raw":
        sys.stdout.write(b.block)
        if not b.block.endswith("\n"):
            sys.stdout.write("\n")
        return
    if mode == "body":
        sys.stdout.write(b.body)
        if not b.body.endswith("\n"):
            sys.stdout.write("\n")
        return
    if mode == "json":
        _print_json(asdict(b))
        return
    raise ValueError(f"Unknown mode: {mode}")


# -------------------------
# Commands
# -------------------------

def cmd_contract(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}", file=sys.stderr)
        return 4

    patterns = args.pattern or ["**/*.md", "**/*.txt", "**/*.prompt.md", "**/*.agent.md"]
    matches = find_format_contracts(
        root,
        args.id,
        patterns=patterns,
        prefer_paths_containing=args.prefer or (),
    )

    if not matches:
        # Build a candidate list for helpful suggestions.
        all_ids: set[str] = set()
        for p in _iter_files(root, patterns):
            txt = _read_text(p)
            for fc in extract_format_contracts_from_text(txt, file_label=_posix(p)):
                all_ids.add(fc.id)
        suggestions = _closest_ids(sorted(all_ids), args.id)
        print(f"NOT FOUND: <format id=\"{args.id}\"> under {root}", file=sys.stderr)
        if suggestions:
            print(f"Did you mean one of: {', '.join(suggestions)}", file=sys.stderr)
        return 2

    if len(matches) > 1 and not args.allow_multiple:
        print(
            f"AMBIGUOUS: found {len(matches)} contracts with id={args.id}. "
            f"Use --allow-multiple or tighten --root/--pattern/--prefer.",
            file=sys.stderr,
        )
        for m in matches:
            print(f"- {m.file} @ {m.start_offset}", file=sys.stderr)
        return 3

    if args.allow_multiple:
        if args.mode == "json":
            _print_json([asdict(m) for m in matches])
        else:
            for idx, m in enumerate(matches):
                if idx > 0:
                    sys.stdout.write("\n")
                _render_contract(m, args.mode)
        return 0

    _render_contract(matches[0], args.mode)
    return 0


def cmd_block(args: argparse.Namespace) -> int:
    if args.file:
        text = _read_text(Path(args.file).expanduser().resolve())
    else:
        text = sys.stdin.read()

    matches = find_rendered_block(text, args.id)

    if not matches:
        found_ids = sorted({b.id for b in extract_rendered_format_blocks_from_text(text)})
        suggestions = _closest_ids(found_ids, args.id)
        print(f"NOT FOUND: ```format:{args.id} ...```", file=sys.stderr)
        if found_ids:
            print(f"Found format blocks: {', '.join(found_ids)}", file=sys.stderr)
        if suggestions:
            print(f"Closest: {', '.join(suggestions)}", file=sys.stderr)
        return 2

    if len(matches) > 1 and not args.allow_multiple:
        print(
            f"AMBIGUOUS: found {len(matches)} rendered blocks with id={args.id}. "
            f"Use --allow-multiple to output all.",
            file=sys.stderr,
        )
        for b in matches:
            print(f"- lines {b.start_line}-{b.end_line}", file=sys.stderr)
        return 3

    if args.allow_multiple:
        if args.mode == "json":
            _print_json([asdict(b) for b in matches])
        else:
            for idx, b in enumerate(matches):
                if idx > 0:
                    sys.stdout.write("\n")
                _render_block(b, args.mode)
        return 0

    _render_block(matches[0], args.mode)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    patterns = args.pattern or ["**/*.md", "**/*.txt", "**/*.prompt.md", "**/*.agent.md"]

    all_contracts: List[FormatContract] = []
    for p in _iter_files(root, patterns):
        txt = _read_text(p)
        all_contracts.extend(extract_format_contracts_from_text(txt, file_label=_posix(p)))

    by_id: Dict[str, List[FormatContract]] = {}
    for fc in all_contracts:
        by_id.setdefault(fc.id, []).append(fc)

    rows = []
    for fmt_id in sorted(by_id.keys()):
        fcs = by_id[fmt_id]
        fcs_sorted = sorted(fcs, key=lambda m: (m.file, m.start_offset))
        canonical = fcs_sorted[0]
        rows.append(
            {
                "id": fmt_id,
                "count": len(fcs),
                "name": canonical.name,
                "purpose": canonical.purpose,
                "canonical_file": canonical.file,
            }
        )

    if args.mode == "json":
        _print_json(rows)
    else:
        for r in rows:
            sys.stdout.write(f'{r["id"]}\t{r["count"]}\t{r["canonical_file"]}\n')

    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="extract_format.py",
        description="Extract APS format contracts (<format id=...>) or rendered format blocks (```format:ID```) by id.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_contract = sub.add_parser("contract", help="Extract a <format id=...>...</format> contract block by id.")
    p_contract.add_argument("--id", required=True, help="Format id (e.g., CODE_MAP_V1).")
    p_contract.add_argument("--root", default=".", help="Root directory to search (default: .).")
    p_contract.add_argument(
        "--pattern",
        action="append",
        help="Glob pattern(s) to include (repeatable). Default includes **/*.md and **/*.txt.",
    )
    p_contract.add_argument(
        "--prefer",
        action="append",
        help="Prefer matches whose file path contains this substring (repeatable).",
    )
    p_contract.add_argument(
        "--mode",
        choices=("raw", "body", "where", "json"),
        default="raw",
        help="Output mode: raw (full <format> block), body (inside), where (WHERE map JSON), json (full metadata).",
    )
    p_contract.add_argument(
        "--allow-multiple",
        action="store_true",
        help="If multiple contracts share the same id, output them all instead of erroring.",
    )
    p_contract.set_defaults(func=cmd_contract)

    p_block = sub.add_parser("block", help="Extract a rendered ```format:ID ...``` fenced block by id.")
    p_block.add_argument("--id", required=True, help="Format id (e.g., HELLO_V1).")
    p_block.add_argument("--file", help="Read input text from a file instead of stdin.")
    p_block.add_argument(
        "--mode",
        choices=("raw", "body", "json"),
        default="raw",
        help="Output mode: raw (whole fenced block), body (inside), json (metadata).",
    )
    p_block.add_argument(
        "--allow-multiple",
        action="store_true",
        help="If multiple blocks share the same id, output them all instead of erroring.",
    )
    p_block.set_defaults(func=cmd_block)

    p_list = sub.add_parser("list", help="List all <format> ids found under a root.")
    p_list.add_argument("--root", default=".", help="Root directory to search (default: .).")
    p_list.add_argument(
        "--pattern",
        action="append",
        help="Glob pattern(s) to include (repeatable). Default includes **/*.md and **/*.txt.",
    )
    p_list.add_argument(
        "--mode",
        choices=("tsv", "json"),
        default="tsv",
        help="Output mode: tsv (id, count, canonical_file) or json.",
    )
    p_list.set_defaults(func=cmd_list)

    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    try:
        return int(args.func(args))
    except BrokenPipeError:
        # Allow piping into head/grep/etc.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
