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

**Commit signature rule:** strip the `Co-Authored-By:` trailer from every commit made under this skill (initial implementation, fix-loop commits, everything). If `commit-msg` produces messages with a trailer, remove it before committing. Commits should look human-authored.

If the user asked for "skip checkpoints", you may batch commits. Otherwise commit per coherent unit of work.

## Step 5 — Open the pull request

When implementation is complete and the suite is green:

1. **Local pre-flight (this skill, not gh-pr):** detect and run the project's typecheck / lint / build commands — read `package.json` scripts, `Makefile`, `pyproject.toml`, `Cargo.toml`, etc. to pick the right ones. Do *not* assume `npm run build`. If any fail, return to Step 4 to fix before pushing. Tell `gh-pr` you have already done the pre-flight so it does not duplicate the work (pass that context when invoking it).
2. Invoke the `gh-pr` skill, which will push the branch and open a PR using the appropriate template.

Capture the PR number as `PR_NUMBER`.

## Step 5.5 — Watch CI

After the PR is open, check CI before waiting on humans:

```bash
gh pr checks <PR_NUMBER> --watch
```

- **If CI is green:** proceed to Step 6.
- **If CI is red:** do not advance. Report the failing check, return to Step 4 to fix the failure (write a regression test first, per TDD discipline), commit, push, and re-run `gh pr checks`. Loop until green.
- **If there is no CI configured for the repo:** note it once and continue.

## Step 6 — Autonomous review → fix loop (max 3 rounds)

Run an automated review-and-fix cycle. The orchestrator (this skill) drives the loop; a fresh subagent does each review.

### Round structure

For each round (`ROUND` from 1 to 3):

**6a. Dispatch review subagent.** Use the Agent tool with `subagent_type: "general-purpose"`. The subagent's job is one round of review only — it returns a verdict and exits.

Subagent prompt template:

> You are reviewing PR #`<PR_NUMBER>` in this repo. Use the `review` skill to perform the review against the linked issue (#`<ISSUE_NUMBER>`) and the project's CLAUDE.md conventions.
>
> When done, post your findings as a single PR comment using the `gh-comment` skill (feedback template). **Do not include any Claude attribution, "🤖 Generated with Claude Code" footer, or `Co-Authored-By:` trailer in the comment body.** The comment must read as a plain human review.
>
> Return a structured verdict to me as your final message:
> - `VERDICT: approve` — no blocking issues, only nits or none
> - `VERDICT: request-changes` — list each blocking item as a one-line bullet
>
> Do not edit code. Do not merge. Review and comment only.

**6b. Parse verdict.** From the subagent's return message:

- `VERDICT: approve` → break the loop, proceed to Step 7
- `VERDICT: request-changes` → continue to 6c
- Anything else → treat as `request-changes` and continue

**6c. Apply fixes.** Invoke the `gh-fix` skill on `PR_NUMBER`. It triages each review comment (Apply / Disagree / Defer), commits fixes (no Co-Authored-By trailer — see Step 4 rule), pushes, and posts a summary reply via `gh-comment` (also signature-free — strip any Claude attribution before posting).

**6d. Increment `ROUND`.** Loop back to 6a unless `ROUND > 3`.

### Round-cap safety net

If the loop exits because `ROUND > 3` without an `approve` verdict:

1. Stop the autonomous loop — do NOT merge
2. Collect every still-blocking item from the last review's `request-changes` list
3. Invoke the `gh-issue` skill to open a follow-up issue titled `Follow-up: unresolved review items from PR #<PR_NUMBER>`, body listing the blockers and a link back to the PR
4. Surface to the user: "Hit 3-round review cap. Filed follow-up issue #X. PR is left open for human decision."
5. **Stop the orchestration.** Do not proceed to Step 7.

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

**If `gh pr merge` reports conflicts** (server-side rebase failed):

1. Stop. Do not retry the merge with `--squash` or `--merge` as a workaround unless the user requests it.
2. Surface the exact error to the user.
3. Offer the local-rebase recovery path and wait for confirmation:
   ```bash
   git fetch origin
   git checkout issues/<N>
   git rebase origin/<BASE_BRANCH>
   # resolve conflicts, run tests, then:
   git push --force-with-lease
   ```
   Use `--force-with-lease`, never `--force`. Do not force-push if anyone else may have based work on this branch — ask first.
4. After the local rebase pushes cleanly, re-run `gh pr merge --rebase --delete-branch`.

Never `git reset --hard`, delete the branch, or abandon work as a "fix" for merge conflicts.

## Step 8 — Switch to default branch

After successful merge:

```bash
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git checkout "$DEFAULT_BRANCH"
git pull --ff-only
```

Always switch to the repo's default branch (not `dev` / `develop`), regardless of what `BASE_BRANCH` was during development.

## Step 9 — Archive

Invoke the `gh-archive` skill to refresh README/docs and snapshot project state. This is the explicit end of the workflow.

## Hard rules

- **Never** merge to `dev`, `main`, or any base branch directly without going through a PR
- **Never** create a branch outside the `issues/<N>` convention from `gh-dev`
- **Never** force-push, reset hard, or delete branches as a shortcut around conflicts
- **Never** skip the failing-test step in TDD, even when the change "looks trivial" — write the test first
- **Never** claim CI is green without running `gh pr checks` first
- **Never** include Claude attribution, "🤖 Generated with Claude Code" footers, or `Co-Authored-By:` trailers in commits, PR comments, review comments, or follow-up issues created under this skill
- If a checkpoint bypass was granted, **state once** that you are proceeding without pausing, then proceed; do not re-ask each phase

## Failure recovery

If any delegated skill fails or produces an unexpected state:

1. Stop the orchestration
2. Report exactly which step failed and the observed state
3. Ask the user how to proceed — do not retry destructively or attempt to "fix" by inventing new commands

This skill values *visibility over throughput*. The user has explicitly chosen to bundle these phases; surprises mid-flight are worse than pauses.
