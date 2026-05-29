---
name: gh-comment
description: >
  Post formatted comments on GitHub PRs or issues, approve PRs, and merge PRs
  via gh CLI using purpose-specific templates (feedback, question, status,
  approval, request-changes). Use when commenting on a PR, leaving feedback,
  asking a question on an issue, posting a status update, approving a pull
  request, merging a PR, or any intent to interact with an existing PR or
  issue — even implicit phrases like "tell them", "approve it", "merge this",
  "LGTM", or "ship it".
---

# gh-comment

Post formatted comments on GitHub PRs and issues, approve PRs, and merge PRs using the `gh` CLI. Comments follow purpose-specific templates for consistency. This skill does not perform code review analysis — use Claude Code's built-in `/review` for that.

Two workflows:

| Workflow | What it does |
|----------|-------------|
| Comment | Post a formatted comment on a PR or issue |
| Approve & merge | Approve a PR and/or merge it (prefers rebase) |

Comment types:

| Type | Shorthand | Use when |
|------|-----------|----------|
| Feedback | `feedback` | Reviewing code, suggesting improvements, noting observations |
| Question | `question` | Asking for clarification on implementation, design, or intent |
| Status | `status` | Posting a progress update on in-progress work |
| Approval | `approval` | Summarizing approval rationale before or after approving |
| Request Changes | `request-changes` | Requesting specific code changes with action items |

## Step 1: Verify prerequisites

Run `gh auth status` to confirm the CLI is installed and authenticated.

If `gh` is not installed, guide the user:
- **macOS**: `brew install gh`
- **Linux**: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
- **Windows**: `winget install --id GitHub.cli` or `scoop install gh`

If `gh` is installed but not authenticated, guide the user through `gh auth login`.

Check that the token has `repo` scope. If it does not, the user needs:

```bash
gh auth refresh -s repo
```

If the repository has no GitHub remote, inform the user and suggest `gh repo create` or `git remote add origin`.

## Step 2: Determine target

Identify the PR or issue from the user's input. The user may provide:

- A number (`#42`, `42`)
- A URL (`https://github.com/owner/repo/pull/42`)
- A contextual reference ("the current PR", "this issue", "that PR")

Resolve the target and fetch context:

```bash
# For a PR
gh pr view N --json number,title,body,state,author,reviewDecision,mergeStateStatus,baseRefName,headRefName,labels

# For an issue
gh issue view N --json number,title,body,state,author,labels
```

If the user said "issue", use issue commands. If "PR", "pull request", or ambiguous, try PR first. If the PR does not exist, try as an issue.

Store `TARGET_TYPE` (`pr` or `issue`) and `TARGET_NUMBER`.

## Step 3: Determine workflow

Choose between the two workflows based on user signals:

- **Comment workflow**: "comment", "feedback", "question", "ask", "update", "status", "suggest", "request changes", "needs changes"
- **Approve & merge workflow**: "approve", "LGTM", "merge", "ship it", "looks good"

If the user says "approve" without "merge", perform approval only (Step 6 without Step 7). If the user says "merge" without "approve", ask whether to approve first or just merge directly.

If the workflow is unclear, ask the user with `AskUserQuestion`.

Store `WORKFLOW` (`comment` or `approve-merge`).

## Step 4: Determine language

Decide which language to use for the comment. Check in this order:

1. If the user explicitly states a language preference in this conversation, use that.
2. Read `CLAUDE.md` in the project root. If it is written in Traditional Chinese or contains a language directive (e.g., `language: zh-TW`), use Traditional Chinese.
3. Default to **English**.

When the user asks for "Chinese" without specifying a variant, default to Traditional Chinese (繁體中文).

Store `COMMENT_LANG` — either `en` or `zh-TW`. This determines which template file to read in Step 5.

## Step 5: Comment workflow

### 5a: Determine comment type

Map the user's request to one of the five types. Use these signals:

- **Feedback**: "feedback", "suggestion", "review", "comment on the code", "note", "thoughts on"
- **Question**: "question", "ask", "clarify", "why", "how come", "unclear", "wondering"
- **Status**: "status", "update", "progress", "where are we", "what is done", "check in"
- **Approval**: "approve", "LGTM", "looks good", "ship it", "thumbs up"
- **Request Changes**: "request changes", "needs changes", "please fix", "change this", "action items", "blocking"

If ambiguous, ask the user with `AskUserQuestion` presenting the five options.

Store `COMMENT_TYPE`.

### 5b: Gather context

Run in parallel:

```bash
# Read existing conversation on the target
gh pr view N --comments --json comments
# or
gh issue view N --comments --json comments

# Repo info
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Also gather context from the conversation and codebase:

- If the user mentioned specific files, functions, or code concerns, read those files to produce concrete, specific comment content.
- If this is a follow-up to a prior discussion, reference the relevant earlier comments.

The goal is to fill the template with **specific, concrete information** — not vague placeholders.

### 5c: Read and fill the template

Read the appropriate template from `<skill-path>/templates/{COMMENT_TYPE}.md` (or `{COMMENT_TYPE}-zh-TW.md` if `COMMENT_LANG` is `zh-TW`).

Fill in every section using information gathered from the conversation and codebase. For each template section:

- Replace placeholder guidance text with concrete details.
- Include actual file paths with line numbers (e.g., `src/auth/middleware.ts:42`).
- Write action items as specific, actionable checkbox items where applicable.
- If a section truly cannot be filled because information is missing, omit that section entirely rather than leaving placeholder text.

### 5d: Present for review

Show the user the complete comment in a fenced markdown block:

````
**Target:** PR #42 — The PR title
**Comment type:** feedback

---

{filled template body}
````

Use `AskUserQuestion` to ask the user to approve or request changes. If the user requests changes, revise and present again.

### 5e: Post the comment

After the user approves, post the comment:

```bash
# For PR
gh pr comment N --body "$(cat <<'COMMENT_EOF'
{filled comment body}
COMMENT_EOF
)"

# For issue
gh issue comment N --body "$(cat <<'COMMENT_EOF'
{filled comment body}
COMMENT_EOF
)"
```

Report success and the link to the comment.

## Step 6: Approve workflow

This step applies only to PRs. If `TARGET_TYPE` is `issue`, inform the user that issues cannot be approved and stop.

### 6a: Check PR state

```bash
gh pr view N --json reviewDecision,reviews,state,mergeable
```

If the user has already approved this PR, inform them and ask whether to re-approve.

### 6b: Compose approval message

Read the `approval` template (same as Step 5c — use `<skill-path>/templates/approval.md` or the zh-TW variant). Fill it with a summary of what was reviewed and why the PR is ready.

Present the approval message to the user via `AskUserQuestion` for confirmation.

### 6c: Submit approval

```bash
gh pr review N --approve --body "$(cat <<'APPROVE_EOF'
{approval message}
APPROVE_EOF
)"
```

Report success.

### 6d: Offer to merge

After reporting the approval, actively offer:

> "PR approved. Want me to rebase-merge it now?"

- If the user accepts, proceed to Step 7 (Merge workflow).
- If the user declines or does not respond affirmatively, stop here.

## Step 7: Merge workflow

This step applies only to PRs. If `TARGET_TYPE` is `issue`, inform the user that issues cannot be merged and stop.

### 7a: Detect allowed merge strategies

```bash
gh api repos/{owner}/{repo} --jq '{
  allow_merge_commit: .allow_merge_commit,
  allow_squash_merge: .allow_squash_merge,
  allow_rebase_merge: .allow_rebase_merge
}'
```

Extract `{owner}/{repo}` from `gh repo view --json nameWithOwner --jq '.nameWithOwner'`.

### 7b: Select merge strategy

Choose from the repo's allowed strategies in this priority order:

1. **Rebase** (`--rebase`) — preferred for linear history
2. **Squash** (`--squash`) — if rebase is not allowed
3. **Merge commit** (`--merge`) — last resort

If none are allowed (unlikely), inform the user and stop.

Store `MERGE_STRATEGY`.

### 7c: Check merge readiness

```bash
gh pr view N --json mergeStateStatus,reviewDecision,statusCheckRollup
```

Check for blockers:

- `mergeStateStatus` is `BLOCKED` — required reviews or checks not satisfied
- CI checks are failing
- Merge conflicts exist

If blocked, inform the user of the specific blocker. Do not attempt to force-merge or bypass required checks.

### 7d: Confirm with user

Show the user:

- PR number and title
- Merge strategy that will be used and why (e.g., "Rebase — preferred and allowed by repo settings")
- Any warnings (CI still running, branch not up to date)

Use `AskUserQuestion` for explicit approval before merging.

### 7e: Execute merge

```bash
gh pr merge N --rebase  # or --squash or --merge per 7b
```

After successful merge, report:

- The merged PR URL
- The strategy used

### 7f: Linked issue follow-up

After a successful merge, check whether the PR is linked to a GitHub issue:

1. Inspect the PR body for `Closes #N`, `Fixes #N`, or `Resolves #N` (case-insensitive).
2. If not found in the body, check whether the branch name matches the pattern `issues/N`.

If a linked issue is detected, offer:

> "PR merged. Issue #N should auto-close via `Closes #N`. Want me to post a wrap-up comment on the issue?"

- If the user accepts, compose a brief wrap-up comment summarizing what was merged and post it using `gh issue comment N --body "..."`.
- If the user declines, skip the comment.

### 7g: Local cleanup prompt

After the linked issue follow-up (or immediately after merge if no linked issue was found), offer to switch back to the PR's base branch (available from `baseRefName` fetched in Step 2) and delete the local issue branch:

> "Want me to switch back to `BASE_BRANCH` and delete the local `issues/N` branch?"

- If the user accepts, run `git checkout BASE_BRANCH && git branch -d issues/N` (where `BASE_BRANCH` is the PR's base branch, e.g., `dev`, `develop`, or `main`).
- If the user declines, stop here.
- Only offer this when the current branch matches `issues/N`. If the branch does not follow this pattern, skip this step.

## Hard rules

- Never post a comment without showing the full content to the user first and getting explicit approval.
- Never approve or merge a PR without explicit user confirmation.
- Never force-merge or bypass required checks (branch protection, CI, required reviews).
- No emojis in comment bodies.
- Never modify any files in the repository. This skill only interacts with GitHub via the `gh` CLI.
- When merging, prefer rebase. Only fall back to squash or merge-commit when rebase is not allowed by repo settings.
- Never delete branches (local or remote) without explicit user consent.
- Do not duplicate Claude Code's built-in `/review` — this skill posts comments and performs approve/merge actions, not code review analysis.
- When the target PR or issue is closed or merged, warn the user before posting a comment — the comment will still be posted, but they should know the state.
- Never include a signature, attribution line, or "posted by" footer in comments (e.g., "— Claude", "Posted via Claude Code", "Generated by AI"). The comment should read as if the user wrote it themselves.
