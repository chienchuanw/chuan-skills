#!/usr/bin/env python3
"""Turn a song's cue-list CSV into grandMA2 Store commands.

A cue-list CSV is the per-song section map exported from a structure/marker
tool — one row per musical section (PGM IN, INTRO, VER 1, CHOR 1, …) with a
cue number, a name, and a timecode. This script reads that CSV, sanity-checks
it, and emits the `Store Sequence <seq> Cue <n> "<name>" /nc` lines that build
the cues as a labelled navigation skeleton inside an existing song sequence.

It NEVER touches the console — it only prints. The agent sends the commands
through the gma2 MCP (`send_raw_command`). Keeping the console path in one
place (the MCP) means this script stays a pure, testable transform.

Column detection is forgiving: headers are matched case-insensitively by
keyword, so `number`/`cue`/`no`, `name`/`label`/`section`, and
`time`/`timecode` all resolve. Only a name column is strictly required; cue
numbers fall back to row order (1..N) when absent.

Usage
-----
    # Inspect: readable table + warnings (duplicates, gaps, blanks)
    python3 csv_to_cues.py S1_song.csv --dump

    # Emit the build commands for a target sequence
    python3 csv_to_cues.py S1_song.csv --commands 101

    # Also write each row's time into the cue Note (off by default)
    python3 csv_to_cues.py S1_song.csv --commands 101 --note-col time

    # Structured output for programmatic use
    python3 csv_to_cues.py S1_song.csv --json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional


# Header keywords, longest/most-specific first so "timecode" wins over a bare
# "time" only when both exist; each maps to a logical field.
_FIELD_KEYWORDS = {
    "number": ["number", "cue", "no.", "no", "index", "idx"],
    "name": ["name", "label", "section", "title", "marker"],
    "time": ["timecode", "time", "position", "start"],
    "fade_in": ["fadein", "fade in", "fade_in"],
    "fade_out": ["fadeout", "fade out", "fade_out"],
    "notes": ["notes", "note", "comment"],
}


@dataclass
class Cue:
    number: str          # cue id as it will appear on the console (e.g. "1", "0.5")
    name: str
    time: Optional[float]
    note: Optional[str] = None


def _match_columns(header: list[str]) -> dict[str, int]:
    """Map logical field -> column index by case-insensitive keyword match.

    Matching runs in three passes of decreasing confidence, each claiming
    columns before the next runs: (1) exact header == keyword, (2) keyword is a
    whole word/token of the header (so "cue no" and "fade in" resolve), (3)
    substring, restricted to keywords of >=4 chars. The length guard on pass 3
    is what stops a short keyword like "no" from swallowing an unrelated header
    such as "notes" — short keywords must match exactly or as a token, never as
    a loose substring.
    """
    lowered = [(h or "").strip().lower() for h in header]
    tokens = [set(t for t in re.split(r"[^a-z0-9]+", h) if t) for h in lowered]
    resolved: dict[str, int] = {}
    used: set[int] = set()

    def _claim(field: str, keywords: list[str], predicate) -> None:
        if field in resolved:
            return
        for kw in keywords:
            for i in range(len(lowered)):
                if i not in used and predicate(kw, i):
                    resolved[field] = i
                    used.add(i)
                    return

    # Pass 1: exact header match.
    for field, keywords in _FIELD_KEYWORDS.items():
        _claim(field, keywords, lambda kw, i: lowered[i] == kw)
    # Pass 2: keyword appears as a whole token of the header ("no." -> "no").
    for field, keywords in _FIELD_KEYWORDS.items():
        _claim(field, keywords, lambda kw, i: kw.rstrip(".") in tokens[i])
    # Pass 3: substring, only for keywords long enough to be unambiguous.
    for field, keywords in _FIELD_KEYWORDS.items():
        _claim(field, keywords, lambda kw, i: len(kw) >= 4 and kw in lowered[i])

    return resolved


def _to_float(raw: str) -> Optional[float]:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _fmt_number(raw: str, fallback: int) -> str:
    """Cue id: keep an explicit integer/decimal from the CSV, else row order."""
    raw = (raw or "").strip()
    if not raw:
        return str(fallback)
    f = _to_float(raw)
    if f is None:
        return raw  # non-numeric label — pass through verbatim
    return str(int(f)) if f == int(f) else str(f)


def parse(path: str) -> tuple[list[Cue], list[str]]:
    """Return (cues, warnings). Warnings are advisory, never fatal."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise SystemExit(f"empty CSV: {path}")

    header, *body = rows
    cols = _match_columns(header)
    if "name" not in cols:
        raise SystemExit(
            f"could not find a name/label/section column in header: {header}"
        )

    cues: list[Cue] = []
    for i, row in enumerate(body, start=1):
        if not any((cell or "").strip() for cell in row):
            continue  # skip blank lines

        def cell(field: str) -> str:
            idx = cols.get(field)
            return row[idx] if idx is not None and idx < len(row) else ""

        name = cell("name").strip()
        cue = Cue(
            number=_fmt_number(cell("number"), i),
            name=name,
            time=_to_float(cell("time")),
        )
        cues.append(cue)

    warnings = _sanity(cues)
    return cues, warnings


def _sanity(cues: list[Cue]) -> list[str]:
    warnings: list[str] = []

    blanks = [c.number for c in cues if not c.name]
    if blanks:
        warnings.append(f"blank cue name(s) at cue number(s): {', '.join(blanks)}")

    seen: dict[str, int] = {}
    for c in cues:
        seen[c.name] = seen.get(c.name, 0) + 1
    dups = {n: k for n, k in seen.items() if n and k > 1}
    if dups:
        # Duplicate names are legal (cue numbers differ) but worth flagging so
        # the operator isn't surprised by two "CHOR 1" rows.
        pretty = ", ".join(f'"{n}"×{k}' for n, k in dups.items())
        warnings.append(f"duplicate cue name(s) — fine, numbers differ: {pretty}")

    nums = [_to_float(c.number) for c in cues]
    if all(n is not None for n in nums):
        out_of_order = any(b <= a for a, b in zip(nums, nums[1:]))
        if out_of_order:
            warnings.append("cue numbers are not strictly increasing — check ordering")

    return warnings


def cmd_lines(cues: list[Cue], seq: str, note_col: Optional[str]) -> list[str]:
    """Build the console command list.

    ClearAll brackets the stores so each cue is saved from an empty programmer
    (an empty cue = a labelled placeholder, no lighting baked in). The combined
    `Store ... "<name>"` form labels in the same command.
    """
    lines = ["ClearAll"]
    for c in cues:
        label = c.name.replace('"', "'")  # MA quoting: avoid nested double-quotes
        lines.append(f'Store Sequence {seq} Cue {c.number} "{label}" /nc')
        if note_col == "time" and c.time is not None:
            lines.append(
                f'Assign Cue {c.number} Sequence {seq} /note="@{c.time:.1f}s"'
            )
    lines.append("ClearAll")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="path to the cue-list CSV")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dump", action="store_true",
                   help="print a readable table + warnings (default)")
    g.add_argument("--commands", metavar="SEQ",
                   help="emit Store commands for target sequence SEQ")
    g.add_argument("--json", action="store_true", help="emit structured JSON")
    ap.add_argument("--note-col", choices=["time"], default=None,
                    help="also write this column into each cue's Note (default: off)")
    args = ap.parse_args()

    cues, warnings = parse(args.csv)

    if args.commands:
        for line in cmd_lines(cues, args.commands, args.note_col):
            print(line)
        for w in warnings:
            print(f"# warning: {w}", file=sys.stderr)
        return

    if args.json:
        print(json.dumps(
            {"cues": [asdict(c) for c in cues], "warnings": warnings},
            ensure_ascii=False, indent=2))
        return

    # default: --dump
    span = ""
    times = [c.time for c in cues if c.time is not None]
    if times:
        span = f"   (span {min(times):.1f}s → {max(times):.1f}s)"
    print(f"{len(cues)} cues{span}\n")
    print(f"{'cue':>5}  {'name':<14}  time")
    print(f"{'---':>5}  {'----':<14}  ----")
    for c in cues:
        t = f"{c.time:.1f}s" if c.time is not None else "-"
        print(f"{c.number:>5}  {c.name:<14}  {t}")
    if warnings:
        print("\nwarnings:")
        for w in warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
