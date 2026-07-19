# Spend-Audit Skill — Design Spec

- **Date:** 2026-07-19
- **Status:** Approved (design), pending implementation plan
- **Author:** Chuan + Claude (brainstormed)

## Purpose

An on-demand skill that intercepts a *hesitant* purchase and runs a structured Q&A audit to
separate **impulse / novelty / self-reward** from a **genuine, recurring need** — so the user
avoids unnecessary spending. It is the pre-purchase sibling of `daily-reviewer` (which logs
money *already* spent).

Grounded in the user's own `Personal/money-principles.md` (decision ladder, 替代不剝奪, card
routing, ≥NT$10k review, no revolving credit, subscription/forex-leak checks).

## Non-goals

- Not a budgeting/accounting tool (that's `spend-log` + `daily-reviewer`).
- Not tied to any transient deadline (e.g. the 8/12 TOEFL gate). Timing/opportunity-cost is a
  **general** question, never a hardcoded date.
- Does not pressure the user to buy or not buy — it surfaces the honest picture; the user decides.

## Placement & naming

- **New bundle** `money` — home for personal-finance skills (spend-audit first; future:
  subscription-audit, etc.). Registered in `.claude-plugin/marketplace.json`.
- **Skill:** `plugins/money/skills/spend-audit/SKILL.md` (prompt-only, no scripts).
- **Triggers:** "想買 X 但猶豫", "該不該買", "衝動消費", "幫我審這筆消費", "spend audit",
  "consumption audit", "avoid impulse buy", etc.
- **Disambiguation:** `daily-reviewer` = post-hoc logging of money already spent;
  `spend-audit` = pre-purchase interception of a hesitant buy. Each description points to the
  other one line to keep triggering collision-free.

## Architecture

Single self-contained `SKILL.md` (prompt-only), matching all existing personal skills.
Markdown append handles the log; no helper scripts (rejected Approach B as over-engineering;
rejected Approach C — folding into `daily-reviewer` — as trigger-muddying).

## Workflow

1. **Read** `Personal/money-principles.md` as the judgement basis.
2. **Collect** the item basics: name, price, where/how it'd be bought.
3. **Run the audit** via `AskUserQuestion` — the fixed core question backbone below, wording
   tuned per item; one at a time or in small batches. Encourage answering from *what actually
   happened*, not "I probably will…".
4. **Synthesize a verdict** from the rich set below.
5. **Append one row** to `Personal/Finance/spend-audit-log.md`.
6. If verdict = cool-down, record a **revisit date**; if verdict = buy, remind the user to log
   it into the month's `spend-log` (cross-ref, not auto-written).

## Core question backbone (fixed, item-tuned, NOT gated on 8/12)

1. **真實頻率** — how often has the user *actually* done the underlying activity (play/read/use)?
   (Cuts through "以后應該會".)
2. **真痛點 vs 想要** — what real, recurring pain does it solve, vs novelty / "覺得酷" / self-reward?
3. **現有替代** — decision ladder + 替代不剝奪: do they already own something that does this?
4. **衝動來源** — would they still want it in two weeks? if no one knew they owned it?
5. **時機與機會成本** (general, not 8/12) — does buying now crowd out a current priority? is the
   money earmarked for something else?
6. **money-principles 檢核** — which card, ≥NT$10k review, subscription creep, forex leak,
   never touch revolving credit.

## Verdicts (rich set + cooling-off)

- **買** / **不買** / **先用現有替代** / **找更便宜方案** / **冷卻等 N 天再決定**.
- Cooling-off is the core anti-impulse mechanism: on a cool-down verdict, the log records a
  **revisit date**; when the user re-invokes on/after that date, the skill runs a *brief*
  re-check ("is the urge still there? did you find a substitute meanwhile?").

## Log format — `Personal/Finance/spend-audit-log.md`

Append-only table, one row per audit:

```
| 日期 | 品項 | 金額 | 判定 | 回訪日(冷卻用) | 一句理由 |
```

- Header includes a short blurb + "本 log 是行為軌跡,重點是趨勢不是流水帳" (echoes
  money-principles §四).
- A "買" outcome prompts a reminder to record it in the month's `spend-log` (cross-ref only,
  never auto-written).

## Hard rules

- **No default stance** — never pressure to buy or not-buy; surface impulse-vs-need, user decides.
- **Honesty first** — push for "過去實際發生" answers, not aspirational ones.
- **No secrets** — this skill handles none; N/A but stated for consistency with repo norms.
- A single audit must never rationalize breaking a money-principles bottom line (pay in full,
  never revolve).
- Prompt-only; no scripts, no autoformatters.

## Open items for the implementation plan

- Exact `AskUserQuestion` batching (one-at-a-time vs grouped) and per-item wording guidance.
- `marketplace.json` registration of the new `money` bundle.
- Cross-links in both `spend-audit` and `daily-reviewer` descriptions.
- Repo `CLAUDE.md` update (add `money` bundle to the plugins table + tier map).
