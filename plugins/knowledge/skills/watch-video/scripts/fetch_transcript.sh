#!/usr/bin/env bash
# fetch_transcript.sh <video-url>
#
# Prints a video's metadata and a cleaned plain-text transcript to stdout, so the
# watch-video skill can digest a talk without the agent shelling out to yt-dlp by hand.
#
# Output shape (stdout):
#   TITLE:<title>
#   UPLOADER:<channel>
#   DATE:<YYYYMMDD>
#   DURATION:<H:MM:SS>
#   VIEWS:<n>
#   SUBKIND:<manual|auto>  SUBLANG:<lang-code>
#   ---TRANSCRIPT---
#   <one long line of deduplicated caption text>
#
# Exit codes: 0 ok; 2 no captions available; 3 yt-dlp missing.
set -euo pipefail

URL="${1:?usage: fetch_transcript.sh <video-url>}"

command -v yt-dlp >/dev/null 2>&1 || { echo "TRANSCRIPT_ERROR: yt-dlp not installed (brew install yt-dlp)"; exit 3; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- Metadata (best-effort; never fatal) ---
yt-dlp --skip-download --no-warnings \
  --print "TITLE:%(title)s" \
  --print "UPLOADER:%(uploader)s" \
  --print "DATE:%(upload_date)s" \
  --print "DURATION:%(duration_string)s" \
  --print "VIEWS:%(view_count)s" \
  "$URL" 2>/dev/null || echo "TITLE:(metadata unavailable)"

# --- Captions: try a prioritized language set, manual subs preferred over auto ---
# Covers the languages the user actually watches (zh / en, plus ja/ko as common extras).
LANGS="zh-Hant,zh-TW,zh-Hans,zh,zh-Hant-zh-TW,en,en-US,en-orig,ja,ko"

fetch() { # $1 = sub flag(s)
  yt-dlp --skip-download $1 --sub-langs "$LANGS" --sub-format vtt \
    --no-warnings -o "$WORK/sub" "$URL" >/dev/null 2>&1 || true
}

SUBKIND="manual"
fetch "--write-subs"
VTT="$(ls "$WORK"/sub*.vtt 2>/dev/null | head -1 || true)"
if [ -z "${VTT:-}" ]; then
  SUBKIND="auto"
  fetch "--write-auto-subs"
  VTT="$(ls "$WORK"/sub*.vtt 2>/dev/null | head -1 || true)"
fi

# --- Fallback: detect the video's NATIVE auto-caption language and grab just that ---
# (Avoids pulling hundreds of machine-translated tracks via "all".)
if [ -z "${VTT:-}" ]; then
  yt-dlp --skip-download --list-subs --no-warnings "$URL" 2>/dev/null > "$WORK/list.txt" || true
  NATIVE="$(python3 - "$WORK/list.txt" <<'PY'
import re, sys
try:
    rows = open(sys.argv[1], encoding='utf-8', errors='replace').read().splitlines()
except Exception:
    sys.exit(0)
in_auto = False
for ln in rows:
    if 'automatic captions' in ln.lower():
        in_auto = True; continue
    if not in_auto or not ln.strip() or ln.lower().startswith('language'):
        continue
    # Native captions have an EMPTY Name column: "<code><spaces>vtt, srt, ...".
    cols = re.split(r'\s{2,}', ln.strip())
    if len(cols) == 2 and re.match(r'^[A-Za-z]{2,3}(-[A-Za-z]+)?$', cols[0]):
        print(cols[0]); break
PY
)"
  if [ -n "${NATIVE:-}" ]; then
    SUBKIND="auto"
    yt-dlp --skip-download --write-auto-subs --sub-langs "$NATIVE" --sub-format vtt \
      --no-warnings -o "$WORK/sub" "$URL" >/dev/null 2>&1 || true
    VTT="$(ls "$WORK"/sub*.vtt 2>/dev/null | head -1 || true)"
  fi
fi

if [ -z "${VTT:-}" ]; then
  echo "TRANSCRIPT_ERROR: no subtitles or captions available for this video"
  exit 2
fi

SUBLANG="$(basename "$VTT" | sed -E 's/^sub\.?//; s/\.vtt$//')"
echo "SUBKIND:${SUBKIND}  SUBLANG:${SUBLANG:-unknown}"
echo "---TRANSCRIPT---"

# --- Clean VTT -> one deduplicated line (rolling auto-captions repeat lines heavily) ---
python3 - "$VTT" <<'PY'
import re, sys
lines = open(sys.argv[1], encoding='utf-8', errors='replace').read().splitlines()
seen = []
for ln in lines:
    if '-->' in ln or not ln.strip():
        continue
    if ln.startswith(('WEBVTT', 'Kind:', 'Language:')):
        continue
    ln = re.sub(r'<[^>]+>', '', ln).strip()   # strip inline timing tags
    if not ln or re.fullmatch(r'\d+', ln):     # drop bare cue numbers
        continue
    if seen and seen[-1] == ln:
        continue
    seen.append(ln)
# Collapse the rolling overlap where each cue restates the tail of the previous one.
out = []
for s in seen:
    if out and (s in out[-1] or out[-1] in s):
        if len(s) > len(out[-1]):
            out[-1] = s
        continue
    out.append(s)
print(' '.join(out))
PY
