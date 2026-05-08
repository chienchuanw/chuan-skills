---
name: feature
description: >
  End-to-end feature delivery workflow that orchestrates issue creation, branch setup,
  strict TDD implementation, PR opening, review-feedback handling, and session archival.
  Use when the user wants to ship a feature from start to finish with one command — e.g.
  "/feature 42", "/feature add RSS feed", "build this end-to-end", "deliver issue 17",
  "take this from issue to merged PR". Bundles the plan → TDD → PR → review-fix → archive
  arc that would otherwise require invoking 5+ separate skills.
---

# feature

Orchestrate a full feature lifecycle: **issue → branch → design → red-green-refactor → PR → review-fix → archive**. This skill is a conductor — it delegates each phase to a specialist skill rather than reimplementing the work. Pause at two checkpoints (after design, before merge) so the user stays in control of scope and timing.

## Argument parsing

The user invokes `/feature <arg>`. Inspect `<arg>`:

- **Numeric (e.g. `42`, `#42`, full URL ending in `/issues/42`)** → existing issue path. Set `ISSUE_NUMBER` and skip Step 1.
- **Free-form text (e.g. `add RSS feed`, `support locale auto-detection`)** → new issue path. Pass the text to Step 1.
- **No arg** → ask the user whether they want to start from an existing issue or describe new work.

## Step 1 — Ensure an issue exists (free-form path only)

Invoke the `gh-issue` skill to file a structured ticket from the user's description. After it completes and the issue is created, record the new number as `ISSUE_NUMBER`.

If the user is on the existing-issue path, skip to Step 2.

## Step 2 — Create the linked branch

Invoke the `gh-dev` skill with `ISSUE_NUMBER`. It will:

- Confirm working tree is clean
- Detect base branch (`dev` / `develop` / default)
- Run `gh issue develop` to create `issues/<N>` linked to the issue
- Check it out

Do not begin implementation yet — `gh-dev`'s commit loop is bypassed for this orchestration.

## Step 3 — Design proposal **[CHECKPOINT 1]**

Read the issue body and any linked context. Explore the relevant parts of the codebase to ground the design. Then write a short design proposal covering:

1. **Goal** — restated in one sentence
2. **Approach** — files to add/modify, key functions, data flow
3. **Test strategy** — what acceptance criteria become tests, what's covered by integration vs unit
4. **Open questions** — anything ambiguous in the issue
5. **Out of scope** — what this PR will *not* do

Present the proposal and **stop**. Wait for the user to approve, request changes, or skip.

**Bypass:** if the user says "skip checkpoints", "auto", "go ahead", or similar at the start of the session, note the bypass and proceed without pausing — but still write the proposal so it lands in conversation history.

## Step 4 — Strict TDD implementation

Invoke the `superpowers:test-driven-development` skill and follow it verbatim. Red-Green-Refactor discipline is non-negotiable in this skill:

- Write a failing test first
- Run it; confirm it fails for the expected reason
- Write the minimum code to make it pass
- Run the full suite; confirm green
- Refactor with tests still green
- Commit at meaningful points using the `commit-msg` skill for messages

If the user asked for "skip checkpoints", you may batch commits. Otherwise commit per coherent unit of work.

## Step 5 — Open the pull request

When implementation is complete and the suite is green:

1. Run typecheck/lint/build locally — if any fail, return to Step 4 to fix before pushing
2. Invoke the `gh-pr` skill, which will push the branch and open a PR using the appropriate template

Capture the PR number as `PR_NUMBER`.

## Step 6 — Review-feedback loop

Wait for the user to report review feedback (or fetch it via `gh pr view <PR_NUMBER> --comments` if asked). When feedback arrives:

- Invoke the `gh-fix` skill, which triages each comment as Apply / Disagree / Defer, applies fixes, and posts a summary comment back on the PR via `gh-comment`

Repeat until the user signals the review round is closed.

## Step 7 — Merge **[CHECKPOINT 2]**

Before merging:

1. Confirm CI is green: `gh pr checks <PR_NUMBER>`
2. Confirm no unresolved review threads
3. Show the user the final commit list and merge target
4. **Stop and wait for explicit "merge it" / "ship it" / "go"**

**Bypass:** same rule as Checkpoint 1 — if the user pre-authorized auto mode, proceed.

Once approved, rebase-merge:

```bash
gh pr merge <PR_NUMBER> --rebase --delete-branch
```

If conflicts arise, surface them and stop — do not force-push or take destructive recovery actions without confirmation.

## Step 8 — Archive

Invoke the `gh-archive` skill to refresh README/docs and snapshot project state. This is the explicit end of the workflow.

## Hard rules

- **Never** merge to `dev`, `main`, or any base branch directly without going through a PR
- **Never** create a branch outside the `issues/<N>` convention from `gh-dev`
- **Never** force-push, reset hard, or delete branches as a shortcut around conflicts
- **Never** skip the failing-test step in TDD, even when the change "looks trivial" — write the test first
- **Never** claim CI is green without running `gh pr checks` first
- If a checkpoint bypass was granted, **state once** that you are proceeding without pausing, then proceed; do not re-ask each phase

## Failure recovery

If any delegated skill fails or produces an unexpected state:

1. Stop the orchestration
2. Report exactly which step failed and the observed state
3. Ask the user how to proceed — do not retry destructively or attempt to "fix" by inventing new commands

This skill values *visibility over throughput*. The user has explicitly chosen to bundle these phases; surprises mid-flight are worse than pauses.
