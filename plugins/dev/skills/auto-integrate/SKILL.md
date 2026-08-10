---
name: auto-integrate
description: >-
  Use when you want an agent to autonomously take a finished feature branch through review, self-fix, and merge into
  an integration branch (`dev`) without a human reading the PR — the agent runs an objective code review, fixes or
  refactors what it can, gates on a hard green light (tests pass AND no blocking findings), then does a clean
  rebase-merge and logs a one-line revert entry. Fires on "auto-integrate this branch", "review-fix-and-merge to
  dev", "run the autonomous merge loop", "自主整合這個分支", "跑自動 merge 迴圈". Manual-only
  (`disable-model-invocation`) because it merges code. It NEVER touches `main`/production (release stays manual).
  Not a PR-review reporter (that is `/code-review`) and not the full issue→PR delivery flow (that is `feature`).
argument-hint: "(optional) target integration branch — defaults to dev"
disable-model-invocation: true
---

# auto-integrate

Autonomously integrate a finished feature branch into `dev`: objective review → self-fix/refactor → hard green-light
gate → clean rebase-merge → one-line revert log. The human confirms by **outcome** (the merge-log line), not by
reading the PR. Safety comes from guardrails plus full version control — never from trust.

**Suggested model/effort:** this is low-reversibility autonomous merging — run it at **Opus 5 · high** (escalate to
`max` if the fixes get architectural). See the `model-advisor` skill for the canonical rubric.

## Hard invariants — violating the letter is violating the spirit

These are not negotiable. If you cannot satisfy one, **STOP and hand back to the user** — do not proceed "mostly."

1. **Never auto-merge to `main`/production.** Only `dev` or an explicit integration branch. Release is always a
   separate manual step. If the resolved target is (or fast-forwards into) a protected/production branch → refuse.
2. **Green light is a hard precondition.** Merge only when tests ALL pass AND the review has ZERO remaining blocking
   findings. "Probably fine", "only one flaky test", "the finding is minor" are not green.
3. **Each merge is one revert unit.** Squash / clean rebase to a single commit, record its sha (and tag if the repo
   tags integrations). Recovery must be exactly `git revert <sha>`.
4. **Never force-push a shared branch.** No `--force`/`--force-with-lease` on `dev`, `main`, or any pushed branch.
5. **Every merge logs one line** to `docs/merge-log.md` before you report done. No log = not done.
6. **Stop on judgment calls.** Architecture decisions and large cross-file refactor trade-offs are the user's, not
   yours. Fix mechanical/local issues autonomously; stop and advise on anything that reshapes the design.

## The loop

Run when the user invokes `/auto-integrate` on a finished feature branch. Target = the argument, else `dev`.

0. **Safety preflight.** Confirm the working tree is clean and you are on a feature branch. Resolve the target
   branch; if it is `main`/production or protected, **refuse** (invariant 1). Confirm the target exists.
1. **Review.** Run `/code-review` at **high** effort over the diff `target..HEAD`.
2. **Triage & fix.** For each finding:
   - Mechanical / local bug / cleanup → fix or refactor it, then **return to step 1 and re-review** (fixes can
     introduce new findings).
   - Needs an architecture decision or a large cross-file trade-off → **STOP** (invariant 6), write the recommendation
     for the user, do not merge.
3. **Test.** Run the project's test command. Must be fully green. Red → **STOP**, report the failure.
4. **Green-light gate.** Re-confirm: tests all pass AND no blocking findings remain (invariant 2). If not → **STOP**.
   **If this is a UI project** (see the `ui-visual-gate` skill — `ui_project: true` in the repo's `CLAUDE.md`, or the
   diff touches front-end files), the green light ALSO requires a visual comparison artifact (screenshot / preview URL
   / Figma frame link). Missing it → **STOP** and ask the user for one.
5. **Merge.** Clean-rebase the feature branch onto the target, then merge as a single squashed commit (invariant 3).
   Record the resulting sha. Never force-push a shared branch (invariant 4).
6. **Log.** Append one entry to `docs/merge-log.md` (create it if absent) using the format below, then report the
   merge-log line as the outcome.

## Stop conditions (report + advise, never merge)

- Any test red, or the test command can't be determined/run.
- A blocking finding that needs an architecture decision or a large cross-file refactor trade-off.
- The resolved target is protected/production, or the branch can't rebase cleanly without conflict resolution that
  changes behavior.

When you stop, output: what you did so far, the exact blocker, and a concrete recommendation — so the user decides
from your summary rather than re-deriving it.

## Merge-log format

Append to `docs/merge-log.md` (newest at top is fine; keep entries greppable):

```markdown
## <date> <short-sha> <feature-branch> → <target>
- did: <one line — what shipped>
- review: <verdict — e.g. "no blocking; 2 nits fixed">
- visual: <UI projects only — screenshot path / preview URL / Figma frame link>
- revert: git revert <short-sha>
```

## GitHub branch protection

The repo-side half of the guardrails. Run once per repo to protect `main` (require PR, require status checks, require
linear history, block force-push + deletion):

```bash
plugins/dev/skills/auto-integrate/scripts/protect-branches.sh <owner>/<repo>
```

The script is idempotent (reads then PUTs; deletes nothing) and prints what it set. Review its `--help` before running
— it changes GitHub repository settings, so the user runs it deliberately; auto-integrate never runs it for them.

## Red flags — STOP and hand back

- "I'll merge to `main` just this once / it's a tiny change." → Invariant 1. Never.
- "One test is flaky, close enough to green." → Invariant 2. Not green. Stop.
- "I'll force-push to clean up the branch." → Invariant 4. Never on a shared branch.
- "This refactor is obviously right, I'll just do it." → Invariant 6. Architecture is the user's call. Stop and advise.
- "I merged, I'll add the log later." → Invariant 5. No log = not done.

| Rationalization | Reality |
|---|---|
| "Review found only minor stuff, skip the re-review" | Fixes introduce findings. Re-review after every fix (step 1). |
| "Tests are slow, I manually checked the change" | Manual check ≠ green suite. Run tests (step 3). |
| "Target `dev` doesn't exist, I'll use `main`" | Missing target = STOP and ask, never fall back to `main`. |
| "The conflict resolution is obvious" | Behavior-changing conflict resolution is a judgment call. Stop (invariant 6). |
