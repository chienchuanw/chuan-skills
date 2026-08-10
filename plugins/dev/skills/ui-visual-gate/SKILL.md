---
name: ui-visual-gate
description: >-
  Use when starting or integrating work on a UI/visual project — anything that renders a screen, component, page, or
  layout a human looks at. Enforces a visual-first gate: for a UI project you confirm the look (a signed-off Figma
  frame or a throwaway preview page) BEFORE writing implementation code, and any UI change must carry a visual
  comparison (screenshot / preview URL / Figma frame) before it can merge. Fires when a project is flagged
  `ui_project: true` or the diff touches front-end files (.tsx/.jsx/.vue/.svelte/.css), and on "is the design signed
  off", "visual gate", "UI 專案要先確認畫面", "這個要附截圖對照嗎". Figma is the source of truth — this skill reuses the
  existing figma skills for design↔code sync rather than reimplementing them. The `auto-integrate` skill calls this
  as an extra green-light condition for UI projects.
---

# ui-visual-gate

For projects with a visible surface, aesthetics get confirmed **before** code, and no UI change merges without a
visual comparison. Two gates, plus Figma as the single source of truth.

## Is this a UI project?

Decide in this order:

1. **Explicit marker (authoritative).** The repo's `CLAUDE.md` declares `ui_project: true`. Trust it.
2. **File heuristic (fallback hint).** No marker, but the change touches front-end files (`.tsx`, `.jsx`, `.vue`,
   `.svelte`, `.css`, `.scss`, styled components, or the diff references a `figma.com` link). Treat as UI and **tell
   the user** — suggest they add `ui_project: true` to `CLAUDE.md` to make it deterministic next time.
3. **Neither.** Not a UI project — these gates don't apply. Skip.

## Gate 1 — Visual-first sign-off (before coding)

For a UI project, **do not start implementation** until the look is settled and the user has signed off:

- A **Figma frame** finalized for the screen/component, **or**
- A **throwaway preview page** (quick static mockup / temp deploy) the user can eyeball.

Get the user's explicit aesthetic OK on that artifact first. Only then write code. If neither exists, stop and help
produce one (see Figma flow below) rather than coding blind.

## Figma is the source of truth

Don't reimplement Figma integration — reuse the installed figma skills. The direction of truth is Figma → code, then
code changes get pushed back:

| Step | Reuse |
|---|---|
| Finalize the design in Figma | design in Figma; `figma-use` / `figma-generate-design` for authoring |
| Pull tokens/context into the implementation | `get_design_context`, `get_variable_defs` (via `figma-use`) |
| Map components to code | `figma-code-connect` |
| A screen changed in code → push it back to Figma | `figma-generate-design` |

The rule: **finalize in Figma → pull design context/tokens to implement → if the UI changes in code, reflect it back
to Figma** so the two don't drift.

## Gate 2 — Visual comparison at merge (auto-integrate green-light)

When `auto-integrate` runs on a **UI project**, its green light gains one requirement on top of "tests pass + no
blocking findings": the merge must carry **at least one** visual comparison artifact:

- a **screenshot** of the changed surface, **or**
- a **temporary deploy / preview URL**, **or**
- a **Figma frame link** the change was built against.

Record which one (as a link/path) in the `docs/merge-log.md` line for that merge. **No visual artifact → not green →
stop and ask the user** for one. This is where design/code drift gets caught before it lands.

## Constraints

- **Don't block non-UI work.** If the project isn't a UI project (per the detection above), these gates do not apply —
  never impose them on a backend/library change.
- **Reference, don't rebuild.** Point at the figma skills for the actual design↔code mechanics; this skill only
  defines *when* the gates fire and *what* they require.
- **Gate 1 is about taste, Gate 2 is about drift.** Gate 1 asks "does the user like it?" before coding; Gate 2 asks
  "does the shipped screen match the agreed design?" before merging. Both are required for UI projects.
