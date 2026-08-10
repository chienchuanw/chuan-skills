---
name: model-advisor
description: >-
  Use when you're about to start a task and want to pick the right Claude model and effort/thinking level for it,
  instead of defaulting one model + one effort to everything. Fires on "which model should I use", "what model and
  effort for this", "model advice", "model-advisor", "用哪個模型", "這個任務該用什麼模型/effort". Manual-only
  (`disable-model-invocation`). This is the CANONICAL model/effort rubric for the repo — `handoff-prompt` reuses the
  same table for its suggested-model line. Not a handoff tool (that is `handoff-prompt`); this just recommends a
  model + effort for the task in front of you.
argument-hint: "(optional) one-line description of the task you're sizing"
disable-model-invocation: true
---

# model-advisor

Pick the right Claude model and effort level for the task at hand. One model + one effort applied to everything
either overpays on trivial edits or under-reasons on hard decisions. This skill asks a few quick questions, maps the
answers onto a fixed rubric, and returns a concrete **model · effort + one-line reason**.

This SKILL.md holds the **canonical rubric**. Other skills (notably `handoff-prompt`) reuse it — edit the table here
and treat that as the single source of truth.

## Step 1 — Ask the sizing questions

Ask only the ones the task hasn't already answered (if the user passed an argument or the context makes an answer
obvious, skip that question). Aim for 2–4 questions total:

1. **Complexity** — brainstorming / architecture / a tricky bug, or a mechanical edit following a set plan?
2. **Reversibility** — how hard is this to undo? (auto-merge, migration, prod change = low reversibility)
3. **Context size** — will this need to hold a lot of files / a large codebase in context at once?
4. **Cost / speed sensitivity** — does the user want fast-and-cheap, or is correctness the only thing that matters?

## Step 2 — Map to the rubric

Current lineup, most → least capable: **Fable 5** (frontier, priciest, extra bio/cyber safeguards) ·
**Opus 5** (near-frontier; thinking on by default; has a `max` effort tier; beats Fable 5 on most evals at ~half the
price — the practical top pick) · **Sonnet 5** (daily-driver coding, handles the large majority of tasks) ·
**Haiku 4.5** (fast + cheap; no thinking/effort knob). All three 5-series models ship a 1M context window as GA.

| Task type | Recommend | Reason |
|---|---|---|
| Brainstorming / spec / architecture decision | Opus 5 · high (→ `max` if stuck) | wide solution space, needs deep reasoning |
| Straight implementation of a settled plan | Sonnet 5 · medium | plan is fixed; optimize for speed + cost |
| Mechanical edit / rename / boilerplate | Haiku 4.5 (or Sonnet 5 · low) | low-risk, reversible; no deep thinking needed |
| Systematic debugging of a tricky bug | Opus 5 · high | root-cause tracing needs deep reasoning |
| Code-review sub-agent | Opus 5 or Sonnet 5 · high | objectivity + correctness come first |
| Large-scale codebase understanding | Sonnet 5 or Opus 5 · medium | any 5-series carries 1M context; pick by reasoning need |
| Handoff-prompt generation itself | Haiku 4.5 (or Sonnet 5 · low) | pure restatement, low risk |

**Weighting signals** (apply on top of the row match):

- **Lower reversibility → bump model and effort up.** An auto-merge or migration decision earns Opus 5 · high (or
  `max`) even if the edit itself looks mechanical. Reach for **Fable 5** only when a task is *both* genuinely
  frontier-hard and low-reversibility and Opus 5 · max isn't enough — its price and safeguards make it overkill otherwise.
- **Large context is no longer a model selector.** All 5-series models are 1M GA; just stay off **Haiku 4.5** (no 1M
  tier) when the task must hold a large codebase at once — pick by reasoning need instead.
- **High cost/speed sensitivity → step down** one notch (Opus 5→Sonnet 5, or high→medium; consider Fast mode) *only*
  when reversibility is also high. Never trade reasoning away on a low-reversibility task.

## Step 3 — Emit the recommendation

Give one concrete line the user can act on:

> **Recommendation:** `<model>` · `<effort>` effort — `<one-line reason tied to their answers>`.

If two rubric rows genuinely tie, name both and state the deciding factor (usually reversibility or context size). Do
not hedge into a vague "it depends" — commit to a pick and give the reason.

## Example

Task: "add a suggested-model line to an existing skill's output — plan already locked."
Answers: complexity low, reversibility high (docs edit), context small, no speed pressure.

> **Recommendation:** Sonnet 5 · medium effort — settled plan, small context, reversible skill-authoring edit;
> save Opus 5 · high for architecture or low-reversibility work.
