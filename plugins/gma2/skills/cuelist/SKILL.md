---
name: cuelist
description: >
  Import a song's cue-list CSV (section markers like PGM IN / INTRO / VER 1 /
  CHOR 1 with a number, name, and timecode) into that song's grandMA2 sequence,
  building each section as a labelled cue so the operator gets a navigable
  skeleton to program against. Use whenever the user hands over a per-song CSV
  of cues/sections and wants it pushed onto the console — "save this cue list to
  the sequence", "import these cues", "build the cues from this CSV", "turn this
  section map into cues for the song", or points at a file named like
  `S1_<song>.csv`. Assumes the song's sequence already exists (built by the
  setlist skill) and the gma2 MCP is connected (connect skill). Prefer this over
  hand-typing Store commands — it parses the CSV, maps it to the right sequence,
  guards against clobbering existing cues, and verifies the result.
---

# gma2 cuelist

Take a per-song cue-list CSV and store each row as a labelled cue inside that
song's sequence. The cues are **empty placeholders** — a navigation skeleton
(PGM IN → INTRO → VER 1 → …) that the operator walks with Go and programs
later. The CSV is the section map; the lighting comes afterwards.

Parsing lives in `scripts/csv_to_cues.py` (a pure transform — it only prints
commands, never touches the desk). All console writes go through the gma2 MCP
`send_raw_command`, so the console path stays in one place.

## Inputs (from the user)

- **The CSV** — one row per musical section. Columns vary by export tool, but
  there's always a **name** (PGM IN, INTRO, VER 1, CHOR 1, FILL, RISE, END…),
  usually a **cue number** and a **time** (seconds into the song), and often
  `fadeIn`/`fadeOut`/`notes`. Files are commonly named `S<n>_<songtitle>.csv`
  where `<n>` is the song's order within the show.
- The song's **sequence already exists** (built by the `setlist` skill, with a
  home Cue 0.5 "LOADING SONG"); the console is connected (`connect` skill).

## Workflow

### 1. Inspect the CSV
Run the parser to see the sections and catch oddities before writing anything:

```bash
python3 plugins/gma2/skills/cuelist/scripts/csv_to_cues.py "<path>.csv" --dump
```

It prints a `cue · name · time` table, the time span, and warnings (blank
names, duplicate names — legal since cue numbers differ, non-increasing
numbers). Column matching is forgiving (case-insensitive keywords), so most
exports parse without fuss. Report the table so the user can eyeball it.

### 2. Resolve the target sequence (propose, then confirm)
The CSV filename usually carries the **song title** (often in the user's
language), while the sequence is labelled with the one-word English name the
setlist skill assigned. These don't map mechanically, so **don't guess
silently** — read the live sequences and propose the match:

```
List Sequence            # via send_raw_command — lists song sequences by name
```

Use the `S<n>` order in the filename plus the song-title meaning to propose the
matching sequence (e.g. `S1_食等睡等` → the first song → Sequence 101 "Idle").
State your reasoning and **confirm the sequence number with the user** before
writing. Getting this wrong writes cues onto the wrong song.

### 3. Guard against clobbering existing cues
A freshly-built song sequence holds only the home Cue 0.5, so `List Sequence
<seq>` reports `(1)` at the end of its row — the **cue count**. Read it first:

```
List Sequence <seq>      # row ends with (N) = number of cues
```

If `N > 1`, the sequence already has show cues — **stop and ask** before
overwriting or extending. Don't silently store over someone's programming. (A
count of exactly 1 means only the home cue exists → safe to add 1..N.)

### 4. Build the cues
Generate the command list for the confirmed sequence and send each line through
`send_raw_command`:

```bash
python3 .../csv_to_cues.py "<path>.csv" --commands <seq>
```

This emits `ClearAll`, then one `Store Sequence <seq> Cue <n> "<name>" /nc` per
row (label baked into the Store), then a closing `ClearAll`. The `ClearAll`
brackets matter: storing from an empty programmer is what makes each cue an
**empty, labelled placeholder** rather than capturing whatever was live. The
home Cue 0.5 is left untouched.

**Defaults and why:**
- **Empty cues, manual Go trigger** — the setlist engine and its Prev/Next/Goto
  buttons are a hands-on operating model; the cues are a structure to program
  into, not an auto-playing timeline. The timecode column is kept as
  *reference*, not written, by default.
- If the user wants the times recorded on the cues, add `--note-col time` to
  write `@<t>s` into each cue's Note (a separate `Assign Cue … /note` line). For
  auto-advancing cues (Follow / Time / Timecode) see `references/cue-options.md`
  — that's a deliberate opt-in, not the default.

### 5. Verify and report
Read the cues back:

```
List Cue Sequence <seq>
```

Confirm the count went from `(1)` to `(1 + rows)` and that the new cues show
`Trig = Go`, `Mode = Normal`. **Cue Name is not exposed over this console's
Telnet** (a known limitation — see the connect skill), so the labels can't be
read back; confirm them by eye on the console. Report the cue table (number ·
name · time), note the duplicate-name flags, and remind the user the show
isn't saved (Backup / Save Show).

## Notes
- The parser never touches the console — it only prints commands. Every write
  goes through the MCP, keeping one uniform console path (same pattern as the
  other gma2 skills).
- Cue numbers come from the CSV's number column (integers stay integers); if
  there's no number column it falls back to row order 1..N.
- One CSV = one song = one sequence. To do a whole show, run this per song.
