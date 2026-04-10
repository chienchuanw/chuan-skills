---
name: gh-pr
description: >
  Push a development branch and create or update a pull request via gh CLI using type-specific
  templates. Optionally updates README, docs, and project tracking before opening the PR. Use after
  finishing development, when ready to open a PR, submit work for review, or push changes.
---

# gh-pr

Push a development branch and create or update a GitHub pull request. Before opening the PR, optionally update project documentation (README, docs directory, planning files) so the PR includes all relevant changes. This skill is the natural next step after `gh-dev`.

## Step 1: Verify prerequisites

```bash
gh auth status
```

If `gh` is not installed or not authenticated, stop and guide the user (see Gotchas).

Then confirm the repo state:

```bash
# Current branch
git branch --show-current

# Commits ahead of default branch
git log --oneline origin/main..HEAD 2>/dev/null || git log --oneline origin/master..HEAD 2>/dev/null

# Uncommitted changes
git status --porcelain
```

If the current branch is `main` or `master`, stop and tell the user to check out a feature branch first.

If there are uncommitted changes, inform the user and ask how to proceed — commit them, stash them, or abort.

If there are no commits ahead of the default branch, tell the user there is nothing to open a PR for and stop.

Store the current branch name as `BRANCH_NAME`.

## Step 2: Detect the linked issue

Extract the issue number from the branch name. If the branch follows the `issues/N` convention:

```bash
echo "$BRANCH_NAME" | grep -oE 'issues/[0-9]+' | grep -oE '[0-9]+'
```

If a number is found, fetch the issue details:

```bash
gh issue view ISSUE_NUMBER --json title,body,labels,state
```

Store as `ISSUE_NUMBER`, `ISSUE_TITLE`, and `ISSUE_LABELS`. The labels are used in Step 9 to determine the PR type.

If no issue number can be extracted, ask the user whether this PR is linked to an issue. If not, proceed without one.

## Step 3: Determine language

Decide which language to use for the PR body. Check in this order:

1. If the user explicitly states a language preference, use that.
2. Read `CLAUDE.md` in the project root. If it is written in Traditional Chinese or contains a language directive, use Traditional Chinese.
3. Default to **English**.

Store as `PR_LANG` — either `en` or `zh-TW`.

## Step 4: Gather project conventions

```bash
git log --oneline -20
cat CLAUDE.md 2>/dev/null || true
cat CONTRIBUTING.md 2>/dev/null || cat .github/CONTRIBUTING.md 2>/dev/null || true
```

Infer the commit convention (prefix style, tense, scope, capitalization) the same way `gh-dev` does. Store as `COMMIT_CONVENTION`.

## Step 5: Update README (optional)

Check whether the `readme` skill is available in the current session's available skills list.

If available:

1. Review the changes on this branch to determine whether the README needs updating (new features, changed APIs, modified configuration, new dependencies).
2. If updates are warranted, invoke the `readme` skill using the Skill tool.
3. After the skill completes, stage and commit the README changes following `COMMIT_CONVENTION`:

```bash
git add README.md
git commit -m "docs: update README to reflect branch changes"
```

Adapt the commit message prefix to match `COMMIT_CONVENTION`. No Co-Authored-By or attribution.

If the `readme` skill is not available, skip this step silently.

## Step 6: Update docs directory (optional)

```bash
ls -d doc/ docs/ 2>/dev/null
```

If `doc/` or `docs/` exists:

1. Review the diff (`git diff main..HEAD` or equivalent) to identify whether any documented APIs, features, workflows, or configuration changed.
2. Read the relevant documentation files.
3. If updates are needed, edit the affected files.
4. Stage and commit each documentation update:

```bash
git add docs/affected-file.md
git commit -m "docs: update affected-file to reflect new behavior"
```

Adapt the commit message prefix to match `COMMIT_CONVENTION`. No Co-Authored-By or attribution.

If no `doc/` or `docs/` directory exists, skip this step.

## Step 7: Update project tracking (optional)

Check whether the `planning-with-files` skill is available in the current session's available skills list.

If available:

1. Invoke the `planning-with-files` skill using the Skill tool to update project plan files with the completed work from this branch.
2. Stage and commit any changes to planning files:

```bash
git add task_plan.md progress.md findings.md
git diff --cached --stat
git commit -m "docs: update project tracking for completed work"
```

Adapt the commit message prefix to match `COMMIT_CONVENTION`. No Co-Authored-By or attribution.

If the `planning-with-files` skill is not available, skip this step silently.

## Step 8: Push the branch

```bash
git push -u origin "$BRANCH_NAME"
```

If the push fails due to diverged history, inform the user and ask how to proceed. Never force-push without explicit user consent.

## Step 9: Create or update the PR

### 9a: Check for existing PR

```bash
gh pr view "$BRANCH_NAME" --json number,title,state,url 2>/dev/null
```

If a PR exists and is open, proceed to update flow (Step 9f). Otherwise, create a new PR.

### 9b: Determine PR type

Map the PR to one of six types using the issue labels from Step 2:

- **bug**: labels contain "bug"
- **feat**: labels contain "enhancement", "feature", or no label but issue title starts with "feat:"
- **refactor**: labels contain "refactor" or issue title starts with "refactor:"
- **doc**: labels contain "documentation" or issue title starts with "doc:"
- **perf**: labels contain "performance" or issue title starts with "perf:"
- **security**: labels contain "security"

If the type cannot be determined from labels, infer from the commit history or ask the user.

Store as `PR_TYPE`.

### 9c: Read the template

Read the appropriate template from `<skill-path>/templates/{PR_TYPE}.md` (or `{PR_TYPE}-zh-TW.md` if `PR_LANG` is `zh-TW`).

### 9d: Fill the template

Fill every section using information from:

```bash
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD
```

Plus the issue details from Step 2. Replace placeholder guidance with concrete details — file paths, function names, specific changes. If `ISSUE_NUMBER` exists, include `Closes #ISSUE_NUMBER` in the Summary section.

Build the PR title following `COMMIT_CONVENTION`. Keep under 80 characters.

### 9e: Present for review and create

Show the user the complete PR title and body in a fenced block. Use `AskUserQuestion` to ask for approval or changes. After approval:

```bash
gh pr create \
  --title "{title}" \
  --base "{default_branch}" \
  --body "$(cat <<'PR_EOF'
{filled PR body}
PR_EOF
)"
```

Report the PR URL to the user.

### 9f: Update existing PR

If a PR already exists:

1. Rebuild the PR body using the same template, incorporating all commits including documentation updates.
2. Show the updated body to the user and ask for approval.
3. Update:

```bash
gh pr edit EXISTING_PR_NUMBER \
  --title "{updated_title}" \
  --body "$(cat <<'PR_EOF'
{updated PR body}
PR_EOF
)"
```

Report the PR URL to the user.

## Step 10: Final summary

Report to the user:

- Branch name and PR URL
- Whether the PR was created or updated
- Which optional documentation steps were performed (README, docs, planning)
- Linked issue number (if any)

## Gotchas

Before running any `gh` command, verify that the CLI is available, authenticated, **and has the required token scopes**:

```bash
gh auth status
```

If `gh` is not installed, guide the user to install it first:
- **macOS**: `brew install gh`
- **Linux**: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
- **Windows**: `winget install --id GitHub.cli` or `scoop install gh`

If `gh` is installed but not authenticated, guide the user to log in:

```bash
gh auth login
```

A successful `gh auth status` does not guarantee sufficient permissions. The token must include the `repo` scope for creating and updating pull requests. Check the scopes listed in the `gh auth status` output. If the `repo` scope is missing, the user must refresh their token:

```bash
gh auth refresh -s repo
```

Do not proceed until `gh auth status` succeeds and confirms the `repo` scope is present.

If the repository has no GitHub remote, inform the user that a remote is required and suggest:

```bash
gh repo create
# or
git remote add origin https://github.com/{owner}/{repo}.git
```

If `git log main..HEAD` (or `master..HEAD`) returns no commits, the branch has nothing to submit. Step 1 already checks for this and stops early. Do not attempt to generate a PR title, body, or template when the diff is empty — the template filling logic in Step 9d depends on non-empty `git log` and `git diff --stat` output, and will fail if both are blank.

When checking for the `readme` or `planning-with-files` skills, do not error or warn if they are absent. These are optional enhancements — the core PR workflow works without them.

## Hard rules

- Never append Co-Authored-By, signatures, or attribution of any kind to commit messages.
- Never use `git add .`, `git add -A`, or `git add --all`. Always stage files by explicit path.
- Never force-push without explicit user consent.
- Never create or update a PR without showing the full title and body to the user first and getting explicit approval.
- No emojis in PR titles or bodies.
- Never skip the push step — the branch must be on the remote before creating the PR.
- Never commit files that contain secrets (.env, credentials, keys, tokens).
- Commit messages for documentation updates must match the project's existing conventions.
- If optional skills (`readme`, `planning-with-files`) are not available, skip them silently — do not suggest installing them or warn about their absence.
- Use `Closes #N` consistently in PR bodies to link issues.
