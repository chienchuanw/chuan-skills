#!/usr/bin/env python3
"""Measure a song's energy shape, section by section, to inform a lighting design.

Run with uv so librosa lands in an ephemeral env (nothing gets installed):

  uv run --with librosa --with soundfile --with numpy python song_energy.py \
      AUDIO --csv SECTIONS.csv --dump

Requires `ffmpeg` on PATH (decodes any format to mono 22.05 kHz first).

Given the song's audio and its section map (the same per-song CSV the `cuelist`
skill imports), this reports for every section how loud, how busy and how bright
it is — the objective half of "how big should this look be". It NEVER touches
the console; it only prints numbers.

WHAT THIS IS NOT
----------------
RMS is physical loudness, not musical emotion. A stripped-back final chorus can
be the emotional peak of a song and still measure quieter than its second verse.
Treat these numbers as EVIDENCE, not as the design. Where the measurement and
the section names disagree (a CHOR that reads quieter than its VER), that
disagreement is itself the interesting finding — surface it, don't average it
away.

Metrics
-------
level     RMS mean over the section, normalised 0-1 against the loudest section.
peak      Loudest short moment inside the section, same normalisation.
busy      Onset density (note/hit attacks per second) — rhythmic activity, which
          tracks "how much is going on" better than loudness does.
bright    Spectral centroid in Hz — high = airy/cymbals/strings, low = bass/pad.
          Maps intuitively onto colour temperature and beam vs wash choices.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile

import librosa
import numpy as np

_BLOCKS = "▁▂▃▄▅▆▇█"

# Same forgiving header matching as the cuelist skill's parser, so one CSV
# export feeds both skills without the user re-shaping it.
_FIELD_KEYWORDS = {
    "number": ["number", "cue", "no.", "no", "index", "idx"],
    "name": ["name", "label", "section", "title", "marker"],
    "time": ["timecode", "time", "position", "start"],
}


def _match_columns(header: list[str]) -> dict[str, int]:
    found: dict[str, int] = {}
    lowered = [(h or "").strip().lower() for h in header]
    for field, keywords in _FIELD_KEYWORDS.items():
        for kw in keywords:
            for i, h in enumerate(lowered):
                if kw in h and i not in found.values():
                    found[field] = i
                    break
            if field in found:
                break
    return found


def _to_seconds(raw: str) -> float | None:
    """Accept 92.4, 1:32, or 00:01:32.400."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if ":" in raw:
        parts = raw.split(":")
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            return None
        total = 0.0
        for n in nums:
            total = total * 60 + n
        return total
    try:
        return float(raw)
    except ValueError:
        return None


def read_sections(path: str, duration: float) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise SystemExit(f"{path}: empty CSV")
    cols = _match_columns(rows[0])
    if "name" not in cols:
        raise SystemExit(f"{path}: no name/label/section column found in header {rows[0]}")

    sections = []
    for i, row in enumerate(rows[1:], start=1):
        if not any((c or "").strip() for c in row):
            continue

        def cell(field):
            idx = cols.get(field)
            return row[idx] if idx is not None and idx < len(row) else ""

        sections.append({
            "number": (cell("number") or str(i)).strip(),
            "name": cell("name").strip() or f"(row {i})",
            "start": _to_seconds(cell("time")),
        })

    # Sections with no time can't be measured; keep them visible rather than
    # dropping them, so the report matches the cue list one-for-one.
    timed = [s for s in sections if s["start"] is not None]
    timed.sort(key=lambda s: s["start"])
    for a, b in zip(timed, timed[1:]):
        a["end"] = b["start"]
    if timed:
        timed[-1]["end"] = duration
    for s in sections:
        s.setdefault("end", None)
    return sections


def decode(path: str, tmp: str):
    wav = os.path.join(tmp, "_work.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path,
                    "-ac", "1", "-ar", "22050", wav], check=True)
    y, sr = librosa.load(wav, sr=22050, mono=True)
    return y, sr


def measure(y, sr, sections: list[dict]) -> list[dict]:
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    onsets = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop, units="time")
    onsets = np.asarray(onsets)

    out = []
    for s in sections:
        start, end = s.get("start"), s.get("end")
        if start is None or end is None or end <= start:
            out.append({**s, "level_raw": None})
            continue
        a = int(start * sr / hop)
        b = max(a + 1, int(end * sr / hop))
        seg_rms = rms[a:b]
        seg_cen = centroid[a:b]
        if seg_rms.size == 0:
            out.append({**s, "level_raw": None})
            continue
        dur = end - start
        n_onsets = int(((onsets >= start) & (onsets < end)).sum())
        out.append({
            **s,
            "duration_s": round(dur, 1),
            "level_raw": float(seg_rms.mean()),
            "peak_raw": float(seg_rms.max()),
            "busy": round(n_onsets / dur, 2) if dur > 0 else 0.0,
            "bright_hz": int(seg_cen.mean()) if seg_cen.size else None,
        })

    measured = [s["level_raw"] for s in out if s.get("level_raw") is not None]
    peaks = [s["peak_raw"] for s in out if s.get("peak_raw") is not None]
    top = max(measured) if measured else 1.0
    top_peak = max(peaks) if peaks else 1.0
    for s in out:
        if s.get("level_raw") is None:
            s["level"] = s["peak"] = None
        else:
            s["level"] = round(s["level_raw"] / top, 3) if top else 0.0
            s["peak"] = round(s["peak_raw"] / top_peak, 3) if top_peak else 0.0
        s.pop("level_raw", None)
        s.pop("peak_raw", None)
    return out


def spark(level: float | None) -> str:
    if level is None:
        return " "
    idx = min(len(_BLOCKS) - 1, max(0, int(round(level * (len(_BLOCKS) - 1)))))
    return _BLOCKS[idx]


def findings(rows: list[dict]) -> list[str]:
    """Call out the moments a designer actually needs: peaks, drops, climbs."""
    timed = [r for r in rows if r.get("level") is not None]
    if len(timed) < 2:
        return []
    notes = []
    peak = max(timed, key=lambda r: r["level"])
    quiet = min(timed, key=lambda r: r["level"])
    notes.append(f"loudest section: {peak['name']} ({peak['level']:.2f})")
    notes.append(f"quietest section: {quiet['name']} ({quiet['level']:.2f})")

    deltas = [(b["level"] - a["level"], a, b) for a, b in zip(timed, timed[1:])]
    rise = max(deltas, key=lambda d: d[0])
    drop = min(deltas, key=lambda d: d[0])
    if rise[0] > 0.12:
        notes.append(f"biggest lift: {rise[1]['name']} → {rise[2]['name']} "
                     f"(+{rise[0]:.2f}) — the natural place for the song's hit")
    if drop[0] < -0.12:
        notes.append(f"biggest drop: {drop[1]['name']} → {drop[2]['name']} "
                     f"({drop[0]:.2f}) — the natural place to strip the rig back")

    # Where the measurement contradicts the section naming, say so plainly.
    chorus = [r for r in timed if re.search(r"chor", r["name"], re.I)]
    verse = [r for r in timed if re.search(r"ver", r["name"], re.I)]
    if chorus and verse:
        c = sum(r["level"] for r in chorus) / len(chorus)
        v = sum(r["level"] for r in verse) / len(verse)
        if c < v:
            notes.append(f"NOTE: choruses measure QUIETER than verses "
                         f"({c:.2f} vs {v:.2f}) — this song does not build the "
                         f"obvious way; don't design it on autopilot")
    return notes


def dump(rows: list[dict], title: str) -> None:
    print(f"{title}\n")
    hdr = f"{'#':>5}  {'section':<12} {'start':>7} {'dur':>6}  {'level':<8} {'peak':>5} {'busy':>6} {'bright':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        start = f"{r['start']:.1f}" if r.get("start") is not None else "—"
        dur = f"{r['duration_s']:.1f}" if r.get("duration_s") is not None else "—"
        lvl = f"{spark(r.get('level'))} {r['level']:.2f}" if r.get("level") is not None else "—"
        pk = f"{r['peak']:.2f}" if r.get("peak") is not None else "—"
        busy = f"{r['busy']:.2f}" if r.get("busy") is not None else "—"
        bright = f"{r['bright_hz']}" if r.get("bright_hz") else "—"
        print(f"{r['number']:>5}  {r['name'][:12]:<12} {start:>7} {dur:>6}  {lvl:<8} "
              f"{pk:>5} {busy:>6} {bright:>7}")

    arc = "".join(spark(r.get("level")) for r in rows)
    print(f"\narc  {arc}")

    notes = findings(rows)
    if notes:
        print("\nfindings")
        for n in notes:
            print(f"  · {n}")
    print("\nReminder: loudness is not emotion. Cross-check against the section "
          "names and the user's intent before turning any of this into a look.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--csv", required=True, help="the song's section CSV")
    ap.add_argument("--dump", action="store_true", help="human-readable table")
    ap.add_argument("--json", action="store_true", help="structured output")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        y, sr = decode(args.audio, tmp)
    duration = len(y) / sr
    sections = read_sections(args.csv, duration)
    rows = measure(y, sr, sections)

    if args.json:
        json.dump({"audio": os.path.basename(args.audio),
                   "duration_s": round(duration, 1),
                   "sections": rows,
                   "findings": findings(rows)},
                  sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    dump(rows, f"{os.path.basename(args.audio)}  ·  {duration:.1f}s  ·  {len(rows)} sections")


if __name__ == "__main__":
    main()
