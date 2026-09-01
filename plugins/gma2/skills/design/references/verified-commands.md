# Verified command ledger

This file is the first of the three lines of defence. Consult it **before**
reaching for any grandMA2 command; append to it **after** confirming one. It is
the reason this skill gets more reliable with use instead of re-guessing the
same syntax every session.

The split below is the whole point. Do not promote a command from one section to
another without doing the work — a plausible-looking command that was never run
is exactly the failure this ledger exists to prevent.

---

## Tier A — field-proven

Commands the sibling gma2 skills have actually run against this console, with
real results read back. Use freely.

| Command | Notes |
|---|---|
| `ClearAll` | Empties the programmer. Bracket every store operation with it. |
| `Store Sequence <seq> Cue <n> "<name>" /nc` | Label bakes into the Store. `/nc` = no confirm. |
| `Label Sequence <seq> "<name>"` | |
| `Label Sequence <seq> Cue <n> "<name>"` | |
| `Appearance Sequence <seq> Cue <n> /r=<0-100> /g= /b=` | Keep brightness low — white cue text must stay readable. |
| `Assign Sequence <seq> At Executor <page>.<exec>` | Executor inherits the sequence name. |
| `Assign Select At Executor <page>.<exec>` | Sets the button function. |
| `Assign Cue <n> Sequence <seq> /cmd="<command>"` | Cue-attached command line. |
| `Assign Macro 1.<id>.<line> /cmd="<command>"` | Writes one macro line. |
| `Copy Macro 1.<src> At 1.<dst> /o /nc` | |
| `Delete Macro 1.<lo> Thru 1.<hi> /nc` | Destructive — confirm the range with the user first. |
| `Fix Executor <page>.<exec>` | A toggle. Do **not** append `On`. Per-user (see gotchas). |
| `List Fixture 1 Thru 1000` | One big read beats many small ones (see gotchas). |
| `List Group` / `List Page` / `List Sequence` | |
| `List Sequence <seq>` | Row ends with `(N)` = cue count. |
| `List Cue Sequence <seq>` | Does **not** expose cue Name / CMD / Appearance. |
| `List Executor <page>.<exec>` | |
| `List Macro 1.<id>.*` | Lists a macro's lines. |
| `List Preset <pool>.<a> Thru <pool>.<b>` | Range form works where whole-pool `List Preset <pool>` may report NO OBJECTS. |

**Preset pools** (confirmed by the `presets` skill): Dimmer = 1, **Position = 2**,
Gobo = 3, Color = 4, Beam = 5, Focus = 6.

---

## Tier B — documented, not yet field-proven

Written up in a sibling skill's reference from the manual, but never actually
executed against this desk. Verify on first use, then promote to Tier A with the
date and what was read back.

| Command | Source | What to confirm |
|---|---|---|
| `Assign Cue <n> Sequence <seq> /fade=<seconds>` | `cuelist/references/cue-options.md` | That the fade lands on the cue and survives a read-back on the desk surface. |
| `Assign Cue <n> Sequence <seq> /trig=follow` | same | Trig column changes from Go. |
| `Assign Cue <n> Sequence <seq> /trig=time /trigtime=<s>` | same | |
| `Assign Cue <n> Sequence <seq> /note="<text>"` | same | Note is not readable over Telnet — confirm by eye. |

---

## Tier C — UNVERIFIED, needed by this skill

Nothing here has been confirmed. **Every one of these must go through the
verification protocol before it is used on the user's show.** They are listed
with what specifically is uncertain, so the check is targeted rather than vague.

### C1 · Preset link on store — HIGHEST PRIORITY

Everything about this skill's "reference presets, don't bake values" policy rests
on cues storing a *link* to the preset rather than a snapshot of its values. If
MA2 bakes the values, the promise that editing Preset 4.11 updates every cue
using it is **false**, and the design strategy has to be renegotiated with the
user before any programming happens.

- Uncertain: whether preset links are kept by default, and whether a setting
  (something in the store options / "store with preset link") governs it.
- How to check: store a throwaway cue referencing a preset, change the preset's
  value, and see whether the cue's output follows. This is an empirical test —
  the manual's wording alone is not enough to settle it.
- If links are NOT kept: stop and tell the user before continuing. Do not
  silently fall back to absolute values.

### C2 · Effects

- Creating an effect and storing it into the Effects pool.
- Applying an effect to a selection, and what actually ends up in a cue when the
  effect is running in the programmer at store time.
- Effect direction / phase / wings — needed for symmetric L-R sweeps.
- Uncertain: the exact keyword order, and whether an effect must exist before it
  can be assigned or is created by the store itself.

### C3 · Effect speed and the BPM speed master

The design brief locks **all** per-song effects to the BPM speed master, so this
has to be right or every song's movement runs at the wrong rate.

- Which speed master the `setlist` engine's `$songbpm` actually drives. Read
  `List Macro 1.100.*` and follow the line that sets it — do not assume it is
  master 1.
- How an effect's speed is bound to a speed master rather than an absolute rate.
- How to express a fraction of the master (1/1, 1/2, 1/4, 1/8, 1/16) — ambient
  effects need the small divisions so they stay slow on fast songs.

### C4 · Position presets (pool 2)

- Storing a position preset from a live selection.
- Global vs Selective scope for position specifically. Position is inherently
  per-fixture (each light needs its own angle to hit the same point in space),
  which is the opposite of how colour presets work — so the scope that is right
  for Color is likely wrong here. Confirm before building.

### C5 · Individual / layered times

Needed for the "back light first, front light follows" layering that the design
brief calls for.

- Per-attribute or per-feature delay and fade inside a single cue.
- Whether this is done with individual times on the selection, or with cue parts
  (`Part` numbering), and how each reads back.

### C6 · Overwriting an existing cue

- `Store Cue <n> Sequence <seq> /o` — whether `/o` **merges** into the existing
  cue or **replaces** it wholesale. These differ enormously when re-designing a
  song: a merge leaves stale values from the previous design behind.
- Whether there is a distinct "remove and re-store" path that guarantees a clean
  cue.

### C7 · Groups

- `Store Group <n>` from a live selection, and labelling it.
- Whether storing over an occupied group number prompts or silently overwrites.

### C8 · Blind (lower priority)

The user chose live programming, so Blind is not on the critical path. Still
worth establishing, because it would unlock safe programming during a show:

- Whether Blind state is per-user like `Fix` and the current page are. If it is,
  the MCP's Administrator login could program blind without touching the
  operator's live output.

---

## Verification protocol

1. **Check this file first.** If it is in Tier A, use it.
2. **Consult the official manual** for anything else. Record the source (URL or
   manual section) alongside what it says. The manual settles *syntax*; it does
   not settle how this particular console behaves.
3. **Test on the desk with throwaway numbers**, never on the user's show
   objects. Confirm the number is free first (`List …`), run the command, read it
   back, then delete it.

   Suggested scratch numbers — verify each is unused before writing:

   | Object | Scratch |
   |---|---|
   | Sequence | 999 |
   | Effect | 999 |
   | Group | 999 |
   | Preset | `<pool>.999` |

   Clean up every scratch object before moving on. Leaving debris in the user's
   show file is not acceptable.
4. **Write the result back here** — promote to Tier A with the date, the exact
   command as run, and what the read-back showed. Record failures too: a command
   that does *not* work is as valuable to future sessions as one that does.

---

## Inherited gotchas

From the `connect`, `setlist` and `cuelist` skills — these are already paid for
in pain, do not rediscover them.

- **Telnet truncates fast reads.** Use a generous read delay (~1.5 s). Prefer one
  wide read (`List Fixture 1 Thru 1000`) over many narrow ones.
- **Cue Name, CMD and Appearance are not exposed by `List`.** Commands can run
  without error and still need eyeball confirmation on the console surface. Say
  so in the report rather than claiming verification you don't have.
- **`Fix` and the current page are per-user.** The MCP logs in as Administrator;
  the operator is a different user. Show data (sequences, cues, macros, presets,
  effects, groups) is global and shared — only executor Fix and current page are
  user-scoped.
- **`Macro $"song"` on Song Change line 3 can recurse.** Let the user trigger a
  song change on the console with a finger on Pause rather than risking a wedge
  over Telnet.
- **Nothing is saved until the show is saved.** Always say so in the report.
