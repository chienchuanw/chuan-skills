# The song-macro engine — anatomy & command recipes

## Anatomy (what already exists in the show)

The user's show ships a name-driven engine. You build the per-song objects it
points at; you do **not** modify these framework pieces.

- **Template — Macro 99 "Song Change Template"**: 3 lines you clone per song —
  `SetVar $song = ""`, `SetVar $songbpm = ""`, `Macro "Song Change"`.
- **Engine — Macro 100 "Song Change"** (runs after a song macro sets `$song`/`$songbpm`):
  1. `Label Macro 13 $"song"`  — relabel UI buttons to the song
  2. `Label Macro 12 $"song"`
  3. `Macro $"song"`           — calls the macro named like the song (see caveat)
  4. `Off Page Thru - Page "Basic"` — release all pages except Basic
  5. `Select Executor "Set List".$"song"` — select that song's exec on the Set List page
  6. `Goto Cue 0.5`            — jump to the song sequence's home cue
  7. `SpecialMaster "SpeedMaster"."BPM" At $songbpm` — set tempo master
- **Control macros**: `Basic` (Page "Basic"), `Deal`/page (`Page $"song"`),
  view (`Assign View $"song" …`), `Prev`/`Next` (`GoBack`/`Go Executor "Basic"."Set List"`),
  `Goto` (`Goto Executor "Set List".$"song"`), `Off Song`, BPM Default/±5/Double/Half.
- **Master cuelist**: a sequence labelled **"Set List"** assigned to
  **`Executor "Basic".210`**, fixed, button mode **Goto**; one cue per song,
  cue CMD `Macro <id>`.

**Caveat — engine line 3 `Macro $"song"`** resolves to the macro named like the
song, i.e. the song's own selector macro → it can recurse (song macro → Song
Change → `Macro "<song>"` → song macro …). It's the user's engine; leave it alone.
After building, have the user trigger one song on the console (finger on Pause) to
confirm it doesn't wedge — don't trigger it over Telnet where a loop could hang the
session.

## Two different "Set List" objects (don't conflate)

- **Page "Set List"** (page 100) — holds one executor per song, named by song.
  Engine line 5 selects on it.
- **Executor "Basic"."Set List"** (page 1 = Basic, exec 210) — the master cuelist
  the operator walks with Prev/Next/Goto.

## Naming & numbering conventions

- **Name is the functional key** (engine matches by `$song` string); the number is
  organizational. Keep one number across macro / sequence / Set-List exec / page /
  view, all labelled identically.
- One unique English word per song. Translate/condense Chinese or long titles.
  Uniqueness is mandatory; synonym before number suffix.
- Artist *k* block start `100+(k-1)*10+1` (101/111/121…), +1 per song, jump a
  ten-block if >9 songs.
- Default `$songbpm` = 60 when unknown.

## Command recipes

All run via the gma2 MCP (`send_raw_command`, or `build_set_list` for the master).
Page 1 = "Basic"; Page 100 = "Set List"; master sequence/exec = 100 / 1.210.

### Wipe old songs (confirm range first)
```
Delete Macro 1.<lo> Thru 1.<hi> /nc
```

### Infrastructure
```
Label Page 1 "Basic"
Store Page 100
Label Page 100 "Set List"
Assign Sequence 100 At Executor 1.210
Fix Executor 1.210
Assign Goto At Executor 1.210
```

### Per song  (id, name, bpm)
```
# macro — clone template, keep line 3, overwrite SetVar lines
Copy Macro 1.99 At 1.<id> /o /nc
Label Macro 1.<id> "<name>"
Assign Macro 1.<id>.1 /cmd="SetVar $song='<name>'"
Assign Macro 1.<id>.2 /cmd="SetVar $songbpm=<bpm>"

# sequence + home cue (empty programmer => empty cue)
ClearAll
Store Sequence <id> Cue 0.5 /nc
Label Sequence <id> "<name>"
Label Sequence <id> Cue 0.5 "LOADING SONG"
Appearance Sequence <id> Cue 0.5 /r=0 /g=0 /b=0

# per-song page + view shells
Store Page <id>
Label Page <id> "<name>"
Store View <id>
Label View <id> "<name>"

# Set List executor (inherits sequence name) + Select button
Assign Sequence <id> At Executor 100.<id>
Assign Select At Executor 100.<id>
```

### Master cuelist (one cue per song, show order, cue n = 1..N)
```
Store Sequence 100 Cue <n> /nc
Label Sequence 100 Cue <n> "<name>"
Assign Cue <n> Sequence 100 /cmd="Macro <id>"
Appearance Sequence 100 Cue <n> /r=<R> /g=<G> /b=<B>   # artist colour, low brightness
Label Sequence 100 "Set List"
```
`build_set_list(sequence_id=100, sequence_name="Set List", songs=[{cue_id, macro_id, name}])`
covers cue create + label + CMD; add the per-artist `Appearance` calls separately.

### Artist colours (low brightness — white text stays readable), RGB 0–100
Red `40,0,0` · Amber `40,22,0` · Green `0,38,0` · Teal `0,35,38` · Navy `0,8,55`
· Purple `33,0,45` — cycle for >6 artists.

## Verification notes

- Macro lines: `List Macro 1.<id>.*`. Sequences: `List Sequence`. Pages: `List Page`.
- Executors: `List Executor 1.210` (master → `Name=Set List Sequence=Seq 100`),
  `List Executor 100.<id>` (song → `Name=<song>`). Filter data rows with
  `^Exec\s+\d+\.\d+\s+No\.=` — the echo line "Executing :" also starts with "Exec".
- **Not exposed over Telnet**: cue Name/CMD/appearance, executor button function,
  executor Fix flag. Commands run error-free but eyeball these on the console.
- Fixed executors are not listed under other pages over Telnet, and `Fix` is
  user-scoped (Administrator's `Fix` doesn't reach the operator's user). Correct
  syntax `Fix Executor x.y` (toggle; no `On`).

## Worked example — 2026 GMA Showcase
6 artists, 26 songs at 101–104 / 111–114 / 121–125 / 131–134 / 141–144 / 151–155.
Names are single words (Idle, Market, Youth, Only, Expired, Bird, Sky, Melt,
Freedom, Alice, Love, Ocean, Coconut, Blossom, Reluctant, Rascal, Leave, Guitar,
Voice, Close, Heartbeat, Note, Whisper, Vitamin, Fiction, WUI). Master Sequence 100
on Executor "Basic".210, cues 1–26 coloured by the six artist colours above.
