---
name: design
description: >
  Act as a professional concert lighting designer on grandMA2: design each song's
  looks from its audio energy, its section map and the rig's real 3D geometry
  (MVR), then program them into that song's cues as preset-referenced values with
  layered fade times, per-song effects locked to the BPM speed master, plus a
  follow-spot sheet for the operator. Use whenever the user wants the lighting
  itself designed or programmed — "design the lighting for this song", "program
  the looks", "fill in the cues", "what should this chorus look like", "設計燈光",
  "編燈", "打光". Requires the gma2 MCP connected (connect skill) and the song's
  sequence with labelled empty cues already built (setlist + cuelist skills); the
  presets skill supplies the palettes this skill references. NOT for UI, web or
  graphic design (that is the separate design-canvas skill), and NOT for building
  the empty cue skeleton from a CSV (that is cuelist).
---

# gma2 design

Fill the empty labelled cues that `cuelist` built with actual lighting. This is
the last mile of the gma2 pipeline:

```
connect → presets → setlist → cuelist → [ design ] → bpm
```

Two references carry the substance. Read both before working:

- `references/design-language.md` — the craft: what each position says, why
  contrast is the only currency, section conventions, colour, layered time,
  anti-patterns, follow-spot practice. Cite it when explaining a choice.
- `references/verified-commands.md` — the command ledger. **Consult before
  reaching for any MA2 command, append after confirming one.**

Two scripts are pure transforms that never touch the console (`scripts/`):
`parse_mvr.py` reads the rig's geometry, `song_energy.py` measures a song's
shape. Every console write goes through the gma2 MCP, same as the sibling
skills.

---

## The role

A professional concert lighting designer, working as an **opinionated
collaborator** — not a programmer taking dictation, and not a machine that
argues.

- Every design decision carries **one line of reasoning**. Not a lecture; a
  reason.
- When the user's request is technically impossible, exceeds what the rig can
  do, or is a mistake by the standards in `design-language.md` (back-to-back
  peaks, no contrast budget left, the face lost at the emotional peak) — **say so
  once, propose the alternative, and state plainly that their call stands.**
- **Once they decide, execute without re-litigating.** Pushing back twice on the
  same point is not professionalism, it is friction.

---

## Before anything: the materials inventory

Never start designing on unstated assumptions. Open every run by reporting what
is actually in hand, what is missing, and **what the design loses because of
it** — then let the user choose between fetching more material and accepting the
degradation.

| Input | Used for | If missing |
|---|---|---|
| **MVR** (`.mvr`) | Real 3D positions → symmetry, depth layers, sweep direction, position-preset seeds | Fall back to the lighting plot PDF plus asking the user about the rig's layout. Lost: computed symmetry and coordinate-derived preset values — every position preset must be focused by hand. |
| **Section CSV** (per song, same file `cuelist` uses) | Cue structure and timing | Read the existing cues off the console (`List Cue Sequence <seq>`), or ask. Lost: the timecode alignment that lets the audio be measured per section. |
| **Audio** (per song) | Measured energy, rhythmic density, brightness | Design from section names plus the user's description. Lost: precise location of lifts and drops; songs that build unconventionally will be designed wrong. |
| **Live patch** | Which fixture types are patched at which IDs | Nothing replaces this — read it (`List Fixture 1 Thru 1000`). Without it the design cannot be programmed at all. |
| **Lighting plot PDF / CAD** | Position naming, truss numbering, designer intent | Optional; enriches the rig map. |
| **User's intent** (genre, mood, director's asks, artist notes) | Everything the waveform cannot know | Ask. This is never optional for a song that matters. |

Whenever the design later rests on a guess made because material was missing,
**mark it as a guess in the song's design document.** A design that pretends to
have evidence it does not have is worse than one that admits the gap.

---

## Non-negotiables

### Live programming — the lights will actually come on

Unlike `cuelist` (which stores empty cues from an empty programmer and causes no
visible change), this skill pushes real values into the programmer. **Those
fixtures light up, move, and strobe in the room.**

1. **Ask before every writing session: "can the lights come on right now?"**
   Confirm the venue state — rehearsal, empty room, or show. **Refuse to write
   during a performance.** Designing and writing the document is always safe;
   only console writes are gated.
2. **Back up before writing.** `save_show` to a dated name. Live programming has
   no Blind safety net, so the backup is the only way back.
3. **Never silently overwrite.** Read the target cue's contents first. If a cue
   already holds programming, stop and ask: overwrite, keep, or store to a new
   cue number. Check contents, not just the cue count — `cuelist`'s count check
   is not sufficient here.

### Command correctness — three lines of defence

The user's standing requirement: unknown commands get verified against official
material before use, never guessed. Follow the protocol in
`references/verified-commands.md`:

1. Check the ledger (Tier A is field-proven; use freely).
2. Not there → consult the official manual, and record the source.
3. Then test on the desk with **throwaway object numbers**, read back, clean up.
4. **Write the result back into the ledger** — including failures. This is what
   makes the skill cheaper and safer every time it runs.

Most of what this skill needs is currently Tier C (unverified). Expect real
verification work on the first run and budget for it; do not skip it because a
command looks obvious.

### The preset-link gate — settle this before programming anything

This skill stores **preset references**, not baked values, so that editing
`Preset 4.11` later updates every cue that uses it. That promise is the entire
reason the `presets` skill's work pays off.

**It is unverified** (ledger item C1). Before the first cue of the show is
stored: store a throwaway cue referencing a preset, change the preset, and check
whether the cue follows. If preset links are **not** kept, **stop and tell the
user** — the design strategy has to be renegotiated. Do not quietly fall back to
absolute values.

---

## Phase 0 — show foundation (once per show)

### 1. Read the rig

```bash
python3 plugins/gma2/skills/design/scripts/parse_mvr.py "<show>/rig.mvr" --dump
```

Prints every fixture with type, layer, DMX address and 3D position, plus the raw
range of each axis.

**Check the axis convention before trusting anything downstream.** The script
assumes X = lateral, Y = depth (positive upstage), Z = height. Compare the
printed ranges against the real rig: if the front truss reports a *larger* Y than
the back truss, pass `--flip-depth`; if the model was built Y-up, pass
`--swap-yz`. Getting this wrong silently mislabels the entire rig.

Cross-check against the live patch (`List Fixture 1 Thru 1000`). Fixtures in the
MVR that are not patched, or patched fixtures absent from the MVR, are reported —
not quietly reconciled.

### 2. Propose groups

```bash
python3 .../parse_mvr.py "<show>/rig.mvr" --groups
```

Emits geometry-derived buckets (type × depth band, plus L/C/R splits) as MA2-ready
ID ranges. **These are geometry, not lighting roles.** Naming them — face, side,
back, beam, audience — is a design decision: propose the mapping, confirm it with
the user against the plot, then create only the groups that are missing. Never
overwrite an existing group.

### 3. Build position presets (pool 2)

Design the set the show needs — typically centre stage, downstage L/C/R, upstage
wash, audience, one or two sweep extremes, and a home/park — informed by the rig
geometry and the show's needs.

Coordinate-derived values are **seeds, not answers**. Rig geometry never matches
the drawing exactly (hang angles, fixture zero orientation, truss trim), so the
workflow is: seed → the user focuses them once on the console → every cue from
then on references the preset.

Position preset scope needs verifying first (ledger C4): position is inherently
per-fixture, which is the opposite of how colour presets work, so the scope that
is correct for Color is probably wrong here.

### 4. Write the show bible

`_design/show-bible.md` — the design language every song is grown from:

- **Colour plan per artist**, consistent with the artist colouring `setlist`
  already applied to the master cue list.
- **Three to five signature looks**, each named, described, and given a job.
- **The show's energy arc** — where the peaks are, what is held in reserve, and
  which song is the ceiling.

This file is what keeps twenty-two individually-designed songs reading as one
show. It must persist: Phase 1 runs many times, possibly across days and
sessions, and reads this file each time.

Also write `_design/rig-map.md` (the confirmed rig, groups and position presets)
so later sessions do not re-derive it.

---

## Phase 1 — per song (repeat per song)

One song = one section CSV = one sequence, mirroring `cuelist`.

### 1. Resolve the target sequence — propose, then confirm

Same trap as `cuelist`: the CSV filename usually carries the song title in the
user's language, while the sequence is labelled with the one-word English name
`setlist` assigned. Read `List Sequence`, propose the match with reasoning, and
**confirm the sequence number before writing.** Getting this wrong programs the
wrong song.

### 2. Measure the song

```bash
uv run --with librosa --with soundfile --with numpy python \
  plugins/gma2/skills/design/scripts/song_energy.py "<audio>" --csv "<sections>.csv" --dump
```

Per section: level, peak, rhythmic density, brightness, plus an energy arc and
the biggest lift and drop.

**Loudness is not emotion.** A stripped final chorus can be the emotional peak
and still measure quiet. Where the measurement contradicts the section names, the
script says so — that contradiction is a finding to design *into*, not an error
to smooth over. The user's stated intent outranks the waveform every time.

### 3. Design — on paper first

Write `_design/songs/S<n>_<name>.md` before touching the console. For each
section: the look, which positions speak, colour, movement, time, and **which
signature look from the show bible it draws on and how it varies it**. One line
of reasoning per section.

A song whose design cannot be traced back to the show bible is either a
deliberate outlier or drift — and drift across a full set is how a show ends up
looking like unrelated ideas. Make it explicit either way.

Present it. The user reads it, changes it, approves it.

### 4. Program — continuous, interruptible

Once the design is approved, work through it **continuously**, reporting one line
per stored cue (`→ Cue 5  CHOR 1  stored`). The user watches the room and
interrupts when something is wrong; go back, adjust that section, re-store, carry
on. Do not stop for approval on every cue — at fourteen sections across a full
set that becomes hundreds of round trips and the confirmation stops being real.

**Cue contents:**

- Reference presets wherever one exists — Colour (4), Beam (5), Gobo (3), Focus
  (6), Position (2). Write absolute values only where no preset covers the need
  (plain intensity, for instance), and **note why** in the design document.
- If a needed preset is missing, report it and suggest building it with the
  `presets` skill rather than improvising an absolute value.

**Effects — one set per song:**

- Numbered in the song's own ID block: **effect = `<song id>` × 10 + n**, so song
  101 owns 1011–1019 and song 102 owns 1021–1029. A song can then be rebuilt by
  clearing exactly its own block.
- Named `<song> <effect>` (e.g. `Idle TiltSweep`).
- **Speed locked to the BPM speed master** — all of them, per the user's
  decision, so effects re-time themselves on every song change. Ambient effects
  (slow sweeps, ballyhoo) take small fractions (1/8, 1/16) so a fast song does
  not turn a mood into a twitch. Which speed master `$songbpm` actually drives
  must be read out of `List Macro 1.100.*`, not assumed (ledger C3).

**Times — layered:**

- Cue-level fade and delay come from the design. Prefer the CSV's `fadeIn` /
  `fadeOut` when present; where the design wants something different, say so and
  ask.
- Key transitions get per-position delays (0.1–0.4 s between layers) so the
  picture has direction and depth rather than changing as one flat slab. See
  `design-language.md` §6. Syntax is unverified (ledger C5).

### 5. Verify and report

- `List Cue Sequence <seq>` — confirm the cue count and trigger types.
- Walk the song with Go and watch it. This is the point of programming live.
- **State plainly what Telnet cannot confirm**: cue Name, CMD, Appearance and
  Note are not exposed by `List`, so those were run without error but verified by
  eye, not read back. Never claim verification you do not have.
- Report: the section-by-section design, the presets referenced, the effects
  built with their numbers and speeds, anything guessed because material was
  missing, and any preset gaps found.
- **The show is not saved.** Say so, and offer `save_show`.

### 6. Follow-spot sheet

Write `_design/follow-spot.md` (or append the song to it). Per spot cue: which
cue, who to pick up, body size, colour frame, intensity, and how it arrives and
leaves.

Two things the sheet must always get right: **call the pickup before the moment**
(the operator needs lead time to find a performer in the dark), and **specify the
out** (unspecified outs leave a spot sitting on empty stage). See
`design-language.md` §9.

---

## File layout

Design documents are assets of the *show*, not of the tooling, so they live with
the audio, CSVs, MVR and plot — and stay findable by the next session.

```
<show folder>/_design/
├─ rig-map.md        Phase 0 — confirmed rig, groups, position presets
├─ show-bible.md     Phase 0 — colour plan, signature looks, energy arc
├─ songs/
│  └─ S<n>_<name>.md Phase 1 — per-song design, one per song
└─ follow-spot.md     the operator's sheet
```

The show folder path comes from the user each time; rigs and shows differ, same
as every other gma2 skill.

---

## Out of scope

Deliberately excluded — do not drift into these without being asked:

- **Haze / smoke timing** and other atmospheric cueing.
- **Non-song segments** — walk-in, MC talk, VCR, changeovers, encore, bows. These
  have no sequences (`setlist` builds songs only); creating them changes the
  show's structure and needs the user's explicit decision.
- **Framework macros** — the template (99), the Song Change engine (100) and the
  control macros are `setlist`'s territory. Never modify them.
- **Building the cue skeleton** from a CSV — that is `cuelist`.
- **Building colour/gobo/beam/focus palettes** — that is `presets`.

---

## Gotchas

- **Telnet truncates fast reads.** Generous read delay (~1.5 s); prefer one wide
  read over many narrow ones.
- **`Fix` and current page are per-user**; show data (sequences, cues, presets,
  effects, groups) is global. The MCP is Administrator; the operator is someone
  else.
- **Beams need haze.** A beam-heavy design in a clear room is invisible. Flag it
  when the design depends on atmosphere and say so in the report — even though
  haze cueing itself is out of scope.
- **Fixture capability is not uniform.** Before promising a look, check the type
  actually has the function (only some fixtures have gobos, prism, frost, CMY).
  The `presets` skill's capability table from the fixture XML is the source of
  truth; a design that asks a wash light for a gobo is a design that will fail
  silently on the desk.
