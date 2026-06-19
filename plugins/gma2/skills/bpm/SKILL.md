---
name: bpm
description: >
  Estimate the BPM of a show's audio files and write each tempo into its song
  macro's `SetVar $songbpm` line on grandMA2, so the speed master tracks per song.
  Use whenever the user points at a folder of performance audio and wants BPM
  detected and pushed into the song macros — "analyze the BPM", "calculate tempos
  and update the macros", "fill in $songbpm from these tracks", "get the BPM for
  the set". Requires the gma2 MCP connected and the song macros already built
  (see the connect and setlist skills). Needs ffmpeg; pulls librosa via uv.
---

# gma2 bpm

Detect each song's tempo from its audio and write it into the matching song
macro's line 2 (`SetVar $songbpm=<n>`), which the engine feeds to the BPM speed
master on song change. Detection lives in `scripts/analyze_bpm.py`; all console
writes go through the gma2 MCP.

## Inputs (ask the user)

- **Audio folder/files** — the user provides the path each time (shows differ).
  Typically one subfolder per artist with files named `S1_…`, `S2_…` in song
  order. Mixed `.wav`/`.mp3` is fine.
- Song macros already exist (built by the `setlist` skill); the console is
  connected via the gma2 MCP.

## Workflow

### 1. Analyze
`ffmpeg` must be on PATH. Run the analyzer with uv so librosa loads into an
ephemeral environment (nothing gets installed permanently):

```bash
uv run --with librosa --with soundfile --with numpy python \
  plugins/gma2/skills/bpm/scripts/analyze_bpm.py "<audio folder>"
```

It decodes each file to mono 22.05 kHz via ffmpeg, runs librosa beat tracking, and
prints JSON sorted by folder then by the `S<n>` track number — one entry per file
with `bpm`, `raw`, `duration_s`, and a `suspect` flag (with `half`/`double`
alternatives) for likely octave errors.

### 2. Map files → song IDs
The analyzer sorts by folder + `S<n>`, which mirrors the rundown's artist/song
order. Map each file to its song ID the same way the set list was numbered
(artist-offset blocks: 101/111/121…, +1 per song). Sanity-check the mapping
against the song names — if the audio folders or counts don't match the built
macros (e.g. an extra track that isn't in the rundown), surface the discrepancy
and don't invent a macro for it.

### 3. Flag the suspects (don't silently auto-correct)
Automatic trackers often lock onto half or double the musical tempo. Report the
`suspect` entries (`bpm < 75` or `> 170`) with their half/double alternatives and
let the user confirm — the musically-correct octave needs ears. Write the detected
value by default; offer to halve/double on request. Missing BPM defaults to 60.

### 4. Write into the macros
For each mapped song, set line 2 via the MCP `send_raw_command`:

```
Assign Macro 1.<id>.2 /cmd="SetVar $songbpm=<bpm>"
```

### 5. Verify and report
Read back a few: `List Macro 1.<id>.2` should show `SetVar $songbpm=<bpm>`. Report
the full table (id · name · BPM), mark the suspects you flagged, and remind the
user the show isn't saved.

## Notes
- Tempo is rounded to an integer (the speed master takes a BPM number).
- The analyzer never touches the console — it only prints numbers; the agent does
  all writes through MCP tools (keeps the skill's console path uniform).
