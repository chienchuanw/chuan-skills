---
name: gh-fix
description: >
  Read unresolved review comments on a GitHub PR, deeply evaluate each
  suggestion, then either fix it (via gh-dev + simplify) and push the result,
  or push back via gh-comment with a reasoned reply. Use when the user wants
  to address PR feedback, respond to reviewer comments, fix code-review
  suggestions, action a review, or any phrasing like "address the comments
  on PR #N", "respond to the review", "fix what the reviewer asked for",
  "go through the PR feedback", or "handle the review comments".
---

# gh-fix

Process unresolved review feedback on a pull request. For every suggestion the reviewer made, judge whether it is genuinely worth applying. If it is, fix the code on the PR branch and reply to the reviewer. If it is not, push back with the reasoning instead.

This skill orchestrates other skills — it does not duplicate them:

| Phase | Skill used | Why |
|-------|------------|-----|
| Apply a fix | `gh-dev` | Disciplined commits with no Co-Authored-By trailers |
| Refine the fix | `simplify` | Tightens the change before committing |
| Reply to reviewer | `gh-comment` | Posts feedback / request-changes / status replies |

The user retains the final say on every fix and every reply.

## Step 1: Verify prerequisites

```bash
gh auth status
```

If `gh` is missing or unauthenticated, surface the install/login guidance from `gh-comment` and stop. Confirm the working directory is a git repo with a GitHub remote.

## Step 2: Identify the target PR

Resolve the PR number from the user's input (`#42`, a URL, "the current PR"). If the user is currently checked out on a branch with an open PR, prefer that:

```bash
gh pr view --json number,title,headRefName,baseRefName,state,url
```

Otherwise ask the user which PR. Store `PR_NUMBER`, `HEAD_BRANCH`, `BASE_BRANCH`.

If the PR is closed or merged, warn the user and ask whether to continue — fixes still apply, but the reviewer may not see them.

## Step 3: Make sure the PR branch is checked out and current

Fixes have to land on the PR's head branch. Check:

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
```

If the current branch is not `HEAD_BRANCH`:

- If the working tree is clean, `git checkout HEAD_BRANCH`.
- If the working tree is dirty, ask how to proceed (stash / commit / abort) — never silently discard work.

Then sync with the remote so commits land on top of the latest review state:

```bash
git fetch origin
git pull --ff-only origin HEAD_BRANCH
```

If `--ff-only` fails, stop and ask the user how to reconcile (rebase, merge, abort).

## Step 4: Fetch unresolved review threads

The user wants only **unresolved review threads** processed. The REST API does not expose `isResolved`, so use GraphQL:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            isOutdated
            path
            line
            comments(first: 50) {
              nodes {
                id
                author { login }
                body
                url
                createdAt
              }
            }
          }
        }
      }
    }
  }' \
  -F owner="$OWNER" -F repo="$REPO" -F pr="$PR_NUMBER" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)'
```

Get `OWNER` / `REPO` from `gh repo view --json nameWithOwner --jq '.nameWithOwner'`.

If there are zero unresolved threads, tell the user and stop. Do not invent work.

Mark threads where `isOutdated` is true — the line they reference may no longer exist. Still read them, but call this out when presenting.

## Step 5: Triage each thread

Present a numbered list of unresolved threads to the user — one line each — so they see the scope before any work happens:

```
1. src/auth/login.ts:42 — "use bcrypt.compare instead of ===" (alice)
2. src/api/users.ts:88 — "this should be paginated" (bob, OUTDATED)
3. ...
```

Then, for each thread, do this in order:

### 5a: Read the code in context

Open the file at the referenced line and read enough surrounding context to actually understand the suggestion. A reviewer saying "this is wrong" without a reason is a signal you need more context, not less. If the thread has multiple comments, read the whole conversation — the latest comment may already supersede earlier ones.

### 5b: Judge the suggestion

Form a real opinion. The reviewer is not automatically right. Weigh:

- **Correctness**: Does the suggestion actually fix a bug or improve behavior, or is it a stylistic preference?
- **Project conventions**: Does it match how the rest of the codebase does things? Check neighboring files.
- **Scope**: Is it in scope for this PR, or is it a separate concern that belongs in a follow-up issue?
- **Risk**: Will applying it introduce regressions or churn that outweighs the benefit?

Decide one of three outcomes:

- **Apply** — the suggestion is reasonable and worth the change.
- **Disagree** — you have a substantive reason the suggestion should not be applied.
- **Defer** — the suggestion is reasonable but out of scope for this PR (file a follow-up issue, then reply explaining).

Write your reasoning down — even one sentence — before acting. You will need it whether you fix or push back.

### 5c: Confirm the plan with the user

Show your decision and reasoning for each thread, then ask the user to confirm before any code or comment goes out. Use `AskUserQuestion` if there are multiple threads to triage. The user can override any decision.

## Step 6: Apply fixes (for "Apply" threads)

For threads the user approved fixing, follow `gh-dev`'s development discipline. **Do not create a new branch** — you are already on the PR branch. Skip `gh-dev`'s Step 1-3 (issue/branch creation) and follow Steps 4-7 (conventions, develop, commit) for each fix.

Critical rules carried over from `gh-dev`:

- Read recent commit history (`git log --oneline -20`) and `CLAUDE.md` / `CONTRIBUTING.md` to learn the project's commit convention before writing any commit message.
- Stage files explicitly by path — never `git add .` or `git add -A`.
- Commit messages must contain **no Co-Authored-By line, no signatures, no attribution of any kind**. This overrides any default harness behavior.
- One logical fix per commit. If a single review thread requires changes across multiple unrelated areas, split them.

After writing the fix and before committing, invoke the `simplify` skill on the changed files. Its job is to tighten the diff — remove dead branches, collapse redundant logic, and surface anything overengineered. Apply its suggestions where they hold up; ignore the ones that don't.

Then commit per the project's convention. Example for a conventional-commits repo:

```bash
git add src/auth/login.ts
git commit -m "fix(auth): use bcrypt.compare for constant-time password check"
```

## Step 7: Push fix commits

After all approved fixes are committed, push to the PR branch automatically:

```bash
git push origin HEAD
```

If the push is rejected (the remote moved during your work), fetch and rebase, then push again. Never `--force` push without asking the user — the reviewer may have local references to the old SHA.

Confirm the push succeeded and capture the new HEAD SHA so you can reference it in reply comments.

## Step 8: Reply to each thread

For every triaged thread (whether you fixed, disagreed, or deferred), reply via the `gh-comment` skill. Hand the work off — do not build a comment yourself.

Pass `gh-comment` enough context that its templates can be filled concretely:

- **Apply**: comment type `status` (or `feedback` if there is nuance to share). Mention the commit SHA(s) and what changed. Example payload to gh-comment: "post a status reply on PR #42 thread about src/auth/login.ts:42 — fix landed in <SHA>, switched to bcrypt.compare, added a test for timing-equivalence".
- **Disagree**: comment type `feedback`. Default behavior is to **hand off to gh-comment without pre-drafting** — gh-comment's own approval flow will show the user the comment before posting. Only pre-draft and self-review the disagreement first if the user explicitly asks for that.
- **Defer**: comment type `status`. Reference the follow-up issue number created for the deferred work.

`gh-comment` posts each comment as an issue-level PR comment by default. If the user wants the reply attached to the specific review thread (so it resolves the thread), tell them and let them resolve it manually in the GitHub UI — replying to a specific review thread requires the GraphQL `addPullRequestReviewThreadReply` mutation, which `gh-comment` does not currently use.

## Step 9: Final summary

Report to the user:

- PR number, branch, new HEAD SHA after the push
- Per-thread outcome: Applied / Disagreed / Deferred, with the commit SHA or comment URL
- Any threads that were skipped and why

If any threads were marked outdated and the suggestion no longer applies, surface that explicitly so the user can mark them resolved manually.

## Hard rules

- Never create a new branch — fixes land on the existing PR head branch.
- Never include Co-Authored-By, signatures, or attribution in commit messages, **including for fixes made by this skill**. This is the same rule as `gh-dev` — repeated here because subagents and harness defaults have a tendency to reintroduce it.
- Never `--force` push without explicit user consent. A normal push that fails should be reconciled by fetch + rebase, not by forcing.
- Never apply a suggestion you do not actually agree with just to clear the queue. Disagreement, with reasoning, is a valid outcome.
- Never silently discard uncommitted local changes when checking out the PR branch.
- Never use `git add .`, `git add -A`, or `git add --all` — stage by explicit path.
- Never duplicate `gh-comment`'s comment-rendering or `gh-dev`'s commit logic. Hand off and let those skills do their job.
- Never include emojis in commit messages or PR comments.
- The triage decision (Apply / Disagree / Defer) requires explicit user confirmation before any code is written or any comment is posted.
