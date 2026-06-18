#!/usr/bin/env python3
"""Estimate BPM for audio files via librosa beat tracking.

Run with uv so librosa is pulled into an ephemeral env (don't pollute anything):

  uv run --with librosa --with soundfile python analyze_bpm.py FILE_OR_DIR ...

Requires `ffmpeg` on PATH (used to decode any format — wav/mp3/… — to a uniform
mono 22.05 kHz wav before analysis, which is robust across codecs).

Output: JSON list to stdout, one entry per audio file, sorted by folder then by
the leading "S<n>" track number in the filename (so it lines up with a rundown's
song order). Each entry: {folder, file, bpm, raw, duration_s, suspect}.

`suspect` flags likely octave errors (auto BPM trackers often lock onto half or
double the musical tempo): bpm < 75 or bpm > 170. When suspect, `half`/`double`
give the obvious alternative so a human can pick. We do NOT auto-correct — the
musically-correct choice needs ears.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

import librosa
import numpy as np

AUDIO_EXT = (".wav", ".mp3", ".aif", ".aiff", ".m4a", ".flac", ".ogg")


def gather(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for n in names:
                    if n.lower().endswith(AUDIO_EXT) and not n.startswith("."):
                        files.append(os.path.join(root, n))
        elif p.lower().endswith(AUDIO_EXT):
            files.append(p)
    return files


def track_num(path):
    m = re.match(r"[Ss](\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 999


def analyze(path, tmp):
    wav = os.path.join(tmp, "_work.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path,
                    "-ac", "1", "-ar", "22050", wav], check=True)
    y, sr = librosa.load(wav, sr=22050, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    raw = float(np.atleast_1d(tempo)[0])
    bpm = int(round(raw))
    entry = {
        "folder": os.path.basename(os.path.dirname(path)),
        "file": os.path.basename(path),
        "bpm": bpm,
        "raw": round(raw, 1),
        "duration_s": round(len(y) / sr, 1),
        "suspect": bpm < 75 or bpm > 170,
    }
    if entry["suspect"]:
        entry["half"] = int(round(bpm / 2))
        entry["double"] = int(round(bpm * 2))
    return entry


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: analyze_bpm.py FILE_OR_DIR [more ...]")
    files = gather(sys.argv[1:])
    files.sort(key=lambda f: (os.path.dirname(f), track_num(f)))
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            try:
                out.append(analyze(f, tmp))
            except Exception as e:  # keep going; report the failure inline
                out.append({"folder": os.path.basename(os.path.dirname(f)),
                            "file": os.path.basename(f), "error": str(e)})
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
