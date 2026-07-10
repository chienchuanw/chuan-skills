# Proposal — `nutritionist` skill (health@chuan-skills)

Spec agreed via grilling on 2026-07-10. Build in `chienchuanw/chuan-skills` (this repo); data lives in the Mind vault. Ship via PR (cf. PR #48 learning-coach).

## Purpose
Acts as the user's dietitian: reviews meals, gives diet advice grounded in his health data, and continuously tracks intake toward his target weight/body-fat. Diet-first (the lever his flat-2.5-month weight is missing).

## Shape (10 locked decisions)
1. **Single skill, dual-mode** — one skill that switches between "log/review a meal" and "advise / weekly review" (like `portfolio-advisor` running review then advice).
2. **Per-meal審查 = 紅綠燈判讀 + 粗估熱量** — each meal: a verdict tuned to his conditions (TG/fatty-liver/blood-sugar friendly?), one swap suggestion, high/med/low kcal + protein level, one log row. No gram-level macro obsession.
3. **Input = 照片為主、文字為輔** — accept a meal photo (primary) or a text description; tolerate estimation (eating out).
4. **Data storage = TRACKED, new `Personal/Nutrition/` folder** (user chose tracked over gitignored `Personal/Health/`). Note: profile *references* o4's blood panel rather than duplicating it (that data is already tracked in `o4-health-bloodlipid.md`).
5. **Tracking loop = 即時 + 每週回顧 + 血檢計分板** — instant per-meal capture; weekly roll-up vs weight-週均/waist; the real scoreboard is the 7/31 (and future) metabolic blood panel.
6. **Coach-type: sets targets + self-calibrates** — computes a daily kcal target + protein floor + the 3 cuts from his stats/goals; scores each meal/week against it; auto-lowers the target if weight-週均 stalls 2–3 weeks.
7. **Medical safety: 原型食物優先, 保健品只點到** — nutrition/lifestyle only; clinical decisions (meds/doses) deferred to doctor + 7/31 follow-up; whole-food first; evidence-based supplements (e.g. omega-3 for high TG) *mentioned* not dosed; standing disclaimer.
8. **Note integration = 日結行 + 週回顧更新 O4** — writes a one-line `## 飲食` rollup into the day's daily note; weekly review updates `o4-health-bloodlipid.md` 目前進度. Independent skill, user-triggered; `daily-reviewer` may read the 飲食 line but doesn't own it.
9. **Home/name = new `health@chuan-skills`, skill `nutritionist`** — first invocation runs a one-time intake interview to build `nutrition-profile.md`, pulling known data from o4/lifestyle so it doesn't re-ask.
10. **Damage-control mode for uncontrollable meals** — eating-out/tour/家庭聚餐: give "best of the available options" + rebalance the day/week; a single bad meal ≠ failure; the **weekly** trend is the scoreboard (counters his all-or-nothing / worth=output tendency).

## Data files (Mind vault, tracked, `Personal/Nutrition/`)
- **`nutrition-profile.md`** — patient chart: current stats (weight/BF/waist), targets (≤72kg by 2026-07-31; long-term 65kg; BF <20%), constraints (→ references `[[o4-health-bloodlipid]]` for TC 251/LDL 160/TG 168/ratio 6.28/HbA1c 5.8/mild fatty liver; ECG T-wave; Ibuprofen allergy; biotin↔blood-test caution), computed daily kcal target + protein floor (~1.5–2 g/kg ≈ 113–150g) + 3-cut list, food likes/dislikes, cooking-vs-eating-out pattern, cuisines.
- **`food-log-YYYY-MM.md`** — running monthly log; per-meal row: date/time · meal · photo-derived description · 紅/綠 verdict · rough kcal + protein level · 3-cut flags · one-line swap. Daily subtotal + vs-target.

## Triggers (zh-TW + en)
- Meal log: food photo, "記一餐", "這餐可以嗎", "幫我看這餐吃得如何", "log this meal".
- Weekly review: "本週飲食回顧", "這週吃得如何", "飲食週回顧".
- On-demand advice: "我該吃什麼", "外食怎麼點", "幫我規劃菜單".
- First run (no profile): auto-runs intake interview.

## Judgment axis (tuned to his metabolic cluster)
Priority order: cut **sugar / refined carbs / alcohol** (fastest TG + liver-fat drop) → **late-night eating** (finish dinner ≤8:30pm, per lifestyle.md) → **protein + fiber** every meal (深海魚 ≥3×/wk) → **sat/trans fat down** (LDL). Modest deficit (~0.3–0.5 kg/wk). Output in zh-TW (vault rule).

## Non-goals
Not medical diagnosis; not gram-perfect macro tracking; does not prescribe meds/supplement doses; does not add risky HIIT (he already does adequate exercise; diet is the lever).

## Build mechanics (this repo)
- New `plugins/health/` family: `plugins/health/skills/nutritionist/SKILL.md` (+ templates for `nutrition-profile.md` / `food-log`), `plugins/health/.claude-plugin/plugin.json`, register in `.claude-plugin/marketplace.json`.
- Create `Personal/Nutrition/` in the Mind vault on first run (or seed now).
- Ship via PR.

## Open items to confirm before build
- Deficit rate default (recommend 0.3–0.5 kg/wk) and starting daily kcal target — computed at intake once real activity/TDEE confirmed.
- Whether to seed `Personal/Nutrition/` + run intake now, or leave to first invocation.
