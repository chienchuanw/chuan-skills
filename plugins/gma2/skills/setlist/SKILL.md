---
name: setlist
description: >
  Build a grandMA2 per-song show system from a set list / rundown: for each song a
  selector macro, a sequence (with a home cue), a same-named executor on the
  "Set List" page, a per-song page and view, plus one cue on a master "Set List"
  cuelist coloured by artist. Everything is linked BY NAME so the existing
  "Song Change" macro engine drives it. Use whenever the user hands over a rundown
  / set list (PDF or text) and wants the song macros / sequences / pages / executors
  built or rebuilt, says "build the set-list system", "set up the songs", "program
  the show structure from this rundown", or wants to understand/map an existing
  song-macro engine. Requires the gma2 MCP connected (run the connect skill first).
---

# gma2 setlist

Grow a complete per-song playback structure from a rundown, wired to the user's
existing **name-driven** song engine. The engine ("Song Change", macro 100)
resolves everything by the song's name string — `Select Executor "Set List".$"song"`,
`Page $"song"`, etc. — so **the song name is the functional key; the ID number is
only an organizational alias** kept aligned across pools.

Read `references/engine.md` for the engine anatomy and the exact MA2 command
recipes before building. Do all console writes through the gma2 MCP tools
(`build_set_list`, `send_raw_command`, …).

## Phase 0 — Introspect the existing engine (always, even "analyze only")

Never assume. Read the engine first and confirm it matches before building:

- `List Macro 1.100.*` — the **Song Change** engine. Confirm it selects
  `Executor "Set List".$"song"`, gotos `Cue 0.5`, sets the BPM speed master.
- `List Macro 1.99.*` — the song-macro **template** you will clone.
- Control macros (Prev/Next/BPM, e.g. 19–24, 41–45) and which executor the master
  cuelist lives on (`Executor "Basic"."Set List"` → page Basic, exec 210).
- `List Page`, `List Sequence`, `List Executor <page>.<exec>` — current state.

If the user only wants to understand the system, stop here and report the map.
**Do not modify framework macros** (template 99, engine 100, control macros).

## Phase 1 — Parse the rundown → names, IDs, BPM

From the rundown (the user provides a PDF/text path), extract artists in show
order and each artist's songs in order. For PDFs, extract text (`pdftotext -layout`)
to read titles accurately rather than trusting an image.

- **Names → one unique English word.** Short English titles: use as-is. Chinese or
  long titles: translate/condense to a single representative word. **Every final
  name must be globally unique** (the engine addresses by name). On collision,
  prefer a different synonym; only add a number suffix as a last resort. You may
  name automatically and report the "original title → chosen word" mapping
  afterward (the user opted out of pre-approval, but the mapping must be shown).
- **Artist-offset IDs.** Artist *k* block starts at `100 + (k-1)*10 + 1`
  → 101/111/121/131…; songs increment by 1 within an artist (101,102,103,104). If
  an artist has >9 songs, jump to the next ten-block. One number spans the song's
  macro / sequence / Set-List executor / per-song page / view.
- **BPM.** If the rundown carries BPM, use it; otherwise default **60**. (BPM can
  be filled later by the `bpm` skill from audio.)

## Phase 2 — Confirm destructive steps

If rebuilding over an existing set, the old song macros (e.g. 101–122) must be
cleared first. Deletion is destructive — **confirm the exact range with the user
once before deleting**, then `Delete Macro 1.<lo> Thru 1.<hi> /nc`. Keep all
framework macros.

## Phase 3 — Build per song (number = song ID)

For each song (see `references/engine.md` for exact commands):

1. **Macro** — clone the template, then relabel and overwrite only its SetVar
   lines: `Copy Macro 1.99 At 1.<id> /o /nc`; `Label Macro 1.<id> "<name>"`;
   set line 1 `SetVar $song='<name>'`, line 2 `SetVar $songbpm=<bpm>`. (Cloning
   keeps line 3 `Macro "Song Change"` intact and avoids nested-quote escaping.)
2. **Sequence + home cue** — `ClearAll`; `Store Sequence <id> Cue 0.5 /nc`;
   `Label Sequence <id> "<name>"`; `Label Sequence <id> Cue 0.5 "LOADING SONG"`;
   `Appearance Sequence <id> Cue 0.5 /r=0 /g=0 /b=0`. Real cues are left for the
   operator to program.
3. **Page + view shells** — `Store Page <id>`/`Label Page <id> "<name>"`;
   `Store View <id>`/`Label View <id> "<name>"`. (Empty, name-labelled; the engine
   only needs them to exist by name.)
4. **Set-List executor** — `Assign Sequence <id> At Executor 100.<id>` (it inherits
   the sequence's name, so `Executor "Set List"."<name>"` resolves), then set its
   **button function to Select**: `Assign Select At Executor 100.<id>` (the engine
   *selects* the song exec; it does not Go it).

## Phase 4 — Infrastructure (once)

- `Label Page 1 "Basic"` (engine's `Page "Basic"` needs this name).
- `Store Page 100`; `Label Page 100 "Set List"` (holds the per-song executors).
- **Master cuelist = Sequence 100 "Set List"**: one cue per song in show order,
  continuous cue numbers 1…N, `Label … Cue n "<name>"`, cue CMD
  `Assign Cue n Sequence 100 /cmd="Macro <id>"`, and **appearance coloured per
  artist** with **low-brightness** RGB (white text must stay readable) — e.g. dark
  red / amber / green / teal / navy / purple cycling per artist.
- Assign and lock the master: `Assign Sequence 100 At Executor 1.210`;
  `Fix Executor 1.210`; `Assign Goto At Executor 1.210`.

## Phase 5 — Verify and report

- Read back macros (`List Macro 1.<lo> Thru 1.<hi>`, and `…1.<id>.*` for lines),
  sequences (`List Sequence`), pages (`List Page`), the master executor
  (`List Executor 1.210` → Name=Set List, Seq 100), and a song exec
  (`List Executor 100.<id>` → Name=<song>).
- Report the **title → word → ID → artist-colour** mapping and the BPM used.
- Flag the things Telnet can't confirm: **cue labels/CMD/appearance** and
  **button function** aren't exposed by `List` (commands ran error-free but verify
  on the surface). **Executor Fix is user-scoped** — your `Fix` as Administrator
  does not carry to the operator's user; the operator fixes on their own user
  (syntax `Fix Executor x.y`, no `On`).
- Note the show is **not saved** (offer to `save_show`), and that **Song Change
  line 3 (`Macro $"song"`)** can recurse into the song macro — let the user verify
  one trigger on the console (finger on Pause) rather than risking a wedge over
  Telnet.

## Read-back gotcha
This console truncates long Telnet replies if read too fast — use a generous read
delay (~1.5 s). `List Cue n Sequence 100` does not show Name/CMD columns; that's a
display limit, not a build failure.
