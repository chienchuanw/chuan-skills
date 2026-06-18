# Resolving named functions to per-type DMX values

`scripts/profile_palette.py` turns a named function into `(attribute, At%)` for
each fixture type. `At%` is 0–100 — grandMA2 maps that across the channel's full
DMX range, so a named slot resolves to its DMX midpoint as a percentage.

## How resolution works (three strategies, in order)

1. **Band query** (`strobe`): finds the channel function whose name/subattribute
   contains the word and returns a position *within* its range (`position` 0 =
   slow end, 1 = fast end). Random/pulse variants are skipped.
2. **Named slot**: matches a `ChannelSet` name substring and returns its DMX
   midpoint %. This is the precise, preferred path for discrete slots.
3. **Fallback**: matches an attribute or function name and positions within it.

`open` / `closed` / `strobe` / `random` auto-scope to the `SHUTTER` feature so they
don't collide with the "open"/"closed" slots on colour wheels or white channels.
Pass an explicit `feature` to scope other queries (e.g. `GOBO1`, `FOCUS`).

## Prefer precise named-slot queries over band/position

Band/position resolution depends on the XML's logical `from`/`to` percentages,
which are NOT always the DMX percentage — it can land on the wrong sub-range on
some fixtures. Whenever a named slot exists, query it by name:

- Strobe: query **`min Strobe`** (slow) and **`max Strobe`** (fast), feature
  `SHUTTER` — both exist on most strobing fixtures and resolve precisely.
- Focus position: **`max Focus`** / **`min Focus`** rather than `focus` + position.

## Query vocabulary (examples)

| Want | query | feature | notes |
|---|---|---|---|
| Shutter open | `open` | `SHUTTER` | auto-scoped |
| Shutter closed | `closed` | `SHUTTER` | |
| Strobe slow | `min Strobe` | `SHUTTER` | precise slot |
| Strobe fast | `max Strobe` | `SHUTTER` | precise slot |
| Prism in | `4 facet prism` | — | name as printed in XML |
| Frost full | `max Frost` | — | |
| Iris closed | `closed Iris` | — | |
| Zoom wide | `wide` | `FOCUS` | |
| Zoom medium | `normal` | `FOCUS` | |
| Zoom narrow | `narrow` | `FOCUS` | |
| Focus near/far | `max Focus` / `min Focus` | `FOCUS` | |
| Gobo wheel-1 slot | `gobo 1.1` … `gobo 1.7` | — | static slots come before `*` shake variants |
| Gobo wheel-2 slot | `gobo 2.1` … | — | |
| Gobo index | `zero` | — | on the GOBO*_POS attribute |
| Gobo rotate CW/CCW | `Rotate 100` / `Rotate -1` | — | |
| Gobo spin CW/CCW | `Spin 100` / `Spin -1` | — | |

## Watch-outs

- **Zoom direction is not universal.** Some fixtures map `wide`→DMX 0 and others
  `wide`→DMX 255 (reversed). Querying the *named slot* `wide`/`narrow` handles this
  automatically per type — don't hardcode a percentage.
- **Fixtures that lack a function are simply omitted** from the resolver output —
  that preset just won't carry a value for them, which is correct.
- A profile that resolves a query to `None` won't appear for that label; report
  unresolved labels so the user can rename or drop them.

## Worked example (the 2026 showcase rig)

Profiles: Fine 600L BSWF (full moving head), Fine 4019 Pixie (RGBW + zoom),
Fine 1514 Zoom (RGBW + zoom). Gobo exists only on the 600L. A "Strobe Fast" beam
preset resolved to SHUTTER 41% on the 600L (DMX≈105) and SHUTTER 81% on the Pixie
(DMX≈207) — same logical preset, correct per-type DMX, merged Global.
