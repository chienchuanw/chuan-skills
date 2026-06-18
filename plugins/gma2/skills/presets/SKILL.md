---
name: presets
description: >
  Build grandMA2 Gobo / Color / Beam / Focus preset palettes from fixture-type
  XML profiles, programming the correct per-fixture-type DMX value for each named
  function so one logical preset works across mixed fixtures. Use whenever the
  user wants to "build presets", "make a color palette", "set up gobo/beam/focus
  presets", "program a preset pool", or hands over fixture XML files and a console
  to populate presets on. Requires the gma2 MCP server connected (run the connect
  skill first). Prefer this over hand-writing preset commands — it resolves
  fixture-specific values from the profiles instead of guessing.
---

# gma2 presets

Program preset palettes (Gobo=pool 3, Color=4, Beam=5, Focus=6) that work across
a mix of fixtures. The hard part is that "Strobe Fast", "wide", "Iris Closed",
"gobo 1.3" map to different DMX values on every fixture type — that info lives in
the MA2 fixture-type XML, not on the wire. `scripts/profile_palette.py` reads the
XML and resolves each named function to `(attribute, At%)` per type, which you
merge into one Global preset.

## Inputs (ask the user)

- **Fixture-type XML paths** — exported from the console to USB (e.g.
  `/Volumes/USB DISK/gma2/library/manufacturer@fixture@mode.xml`). The user
  provides these each time; rigs differ. One XML per fixture type in use.
- **Which preset types** to build (default: all four — Gobo/Color/Beam/Focus).
- The console must be connected via the gma2 MCP (see the connect skill).

## Workflow

### 1. Inspect the profiles
Run the bundled resolver to see what each fixture can do:

```bash
python3 plugins/gma2/skills/presets/scripts/profile_palette.py FIXTURE1.xml FIXTURE2.xml --dump
```

Note which fixtures support which preset types — dimmer-only profiles (a lone
`DIM` channel) get no Gobo/Color/Beam/Focus and are excluded. Report a capability
table so the user sees, e.g., "only the 600L has gobos; CT+ has no Focus."

### 2. Map fixture types to patched Fixture IDs
Query the live patch (`List Fixture 1 Thru 1000` via `send_raw_command`) to learn
the Fixture ID range for each type (e.g. Fine 600L = 101–109). You program presets
by selecting real patched fixtures — the XML is only the value source. If a type's
XML was given but it isn't patched, say so and skip it.

### 3. Choose palette contents (the only creative input — ask)
Use `AskUserQuestion`. Sensible defaults for a music show:

- **Color** (extended, ~13–23): Red, Orange, Amber, Yellow, Green, Cyan, Blue,
  Lavender, Magenta, Pink, White, Warm White, Cool White — plus a pastel set
  (Soft Pink, Peach, Pale Gold, Mint, Sky Blue, Lilac…) if asked. Express colors
  as R/G/B/W 0–100; for light tints keep the lowest channel ~45–65 so they read as
  a colour, not washed-out white.
- **Scope**: **Global** by default (one preset applies across all fixtures of the
  included types, by feature). Selective only if the user wants per-fixture values.
- **Gobo** (600L-class only): Open + each wheel-1 and wheel-2 gobo, plus
  index/rotate/spin if "full".
- **Beam**: Open, Closed, Strobe Slow, Strobe Fast, Prism, Frost, Iris Closed
  (each only on fixtures that have the function).
- **Focus**: Zoom Wide/Medium/Narrow + Focus Near/Far (Focus only where present).

### 4. Resolve per-type values
For Beam/Gobo/Focus, build a JSON query list and resolve across all profiles:

```bash
python3 .../profile_palette.py *.xml --queries \
  '[{"label":"Strobe Fast","query":"max Strobe","feature":"SHUTTER"},
    {"label":"Zoom Wide","query":"wide","feature":"FOCUS"},
    {"label":"Prism","query":"4 facet prism"},
    {"label":"Gobo 1","query":"gobo 1.1"}]'
```

The output gives `{label: {fixture_name: [attribute, at_percent]}}`. See
`references/resolving.md` for the query vocabulary (band vs. named-slot, strobe,
zoom reversal, gobo/prism/frost/iris) and worked examples.

### 5. Check the pools are empty, then build
Read back `List Preset 4.1` etc. first — don't clobber existing presets without
confirming. Build via the MCP tools:

- **Color**: `build_color_palette` with `scope="global"`, target = all colour
  fixtures (e.g. `Fixture 101 Thru 109 + Fixture 201 Thru 208`), each colour as
  `{id, name, r, g, b, w}`. It sets COLORRGB1/2/3/5, stores, labels, and sets the
  pool swatch.
- **Gobo/Beam/Focus**: `build_preset_palette` with per-preset `by_target` —
  one target per fixture type, each with the resolved `(attribute, at_percent)`
  pairs. Targets accumulate (merge) into one Global preset.

Clear the programmer before and after (`ClearAll`) so the rig isn't left lit.

### 6. Verify and report
`List Preset <pool>.<first> Thru <pool>.<last>` to confirm count + labels (note:
`List Preset 4` whole-pool may say "NO OBJECTS"; range form works). Report what was
built, what was excluded and why, and remind the user the show isn't saved.

## Preset pools
Gobo = **3**, Color = **4**, Beam = **5**, Focus = **6**.
