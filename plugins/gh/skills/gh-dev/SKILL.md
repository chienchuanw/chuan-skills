---
name: gh-dev
description: >
  Create a branch linked to a GitHub issue via gh issue develop, then implement the work with
  regular convention-following commits. Use when starting work on an issue, picking up a ticket,
  developing a feature branch, or any intent to begin coding against a GitHub issue.
---

# gh-dev

Create a development branch linked to a GitHub issue, then implement the work with disciplined, convention-following commits. This skill handles the full loop from branch creation through development, but never pushes to the remote — the user retains full control over when and how to share their work.

## Step 1: Identify the target issue

Determine which issue to work on. The user may provide:

- An issue number (e.g., `42`)
- An issue URL (e.g., `https://github.com/owner/repo/issues/42`)
- A description of the work without referencing a specific issue

If the user provides a number or URL, use it directly. If they describe the work without an issue reference, search for a matching open issue:

```bash
gh issue list --limit 20 --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
```

Present matching issues and ask the user to confirm. If no matching issue exists, ask whether to create one first (suggest the `gh-issue` skill) or proceed with just a branch.

Store the result as `ISSUE_NUMBER`.

## Step 2: Check working tree state

Before creating a branch, check for uncommitted changes:

```bash
git status --porcelain
```

If the working tree is dirty, inform the user and ask how to proceed:

- Stash changes (`git stash`)
- Commit current changes first
- Abort and let the user handle it

Do not silently discard or stash changes — always get explicit consent.

## Step 3: Create the linked branch

The branch name follows a fixed convention: `issues/ISSUE_NUMBER`. For example, issue #1 becomes `issues/1`, issue #42 becomes `issues/42`.

### Pre-flight: Confirm base branch

Before creating the branch, check whether a `dev` or `develop` branch exists on the remote:

```bash
git ls-remote --heads origin dev develop
```

Store the result as `BASE_BRANCH` — either `dev`, `develop`, or the repo's default branch (e.g., `main`) if neither exists.

### Create the branch

Pass `--base` with the detected `BASE_BRANCH` so the new issue branch is based on the correct branch:

```bash
gh issue develop ISSUE_NUMBER --checkout --name "issues/ISSUE_NUMBER" --base BASE_BRANCH
```

Handle these error cases:

- **Branch already exists**: If `issues/ISSUE_NUMBER` already exists, ask the user whether to check out the existing branch (`git checkout issues/ISSUE_NUMBER`) or delete and recreate it.
- **Issue not found**: Inform the user the issue number is invalid and re-prompt.
- **No remote**: Inform the user a GitHub remote is required and suggest `gh repo create` or `git remote add origin`.

After success, confirm the branch name and that it is linked to the issue.

## Step 4: Gather project conventions

Before writing any code, understand how this project handles commits:

```bash
# Recent commit history for convention patterns
git log --oneline -20

# Explicit conventions
cat CLAUDE.md 2>/dev/null || true
cat .github/CONTRIBUTING.md 2>/dev/null || true
cat CONTRIBUTING.md 2>/dev/null || true
```

Infer from the history:

- **Prefix style**: conventional commits (`feat:`, `fix:`), ticket prefixes (`PROJ-123`), or plain prose
- **Scope usage**: parenthetical scopes like `(auth)`, `(api)`, or none
- **Tense**: imperative ("add feature") vs past ("added feature")
- **Capitalization**: sentence case, lowercase after prefix, etc.
- **Message length**: single line vs multi-line body

Explicit documented conventions (in CLAUDE.md, CONTRIBUTING.md) override inferred patterns. Store the result as `COMMIT_CONVENTION` for use throughout development.

## Step 5: Read the issue for context

Fetch the full issue details to understand what needs to be implemented:

```bash
gh issue view ISSUE_NUMBER --json title,body,labels,assignees
```

Use the issue title, body, acceptance criteria, and any referenced files or code paths to guide the implementation. If the issue references specific files, read them to understand the current state before making changes.

## Step 6: Develop the feature or fix

Implement the changes described in the issue. During development:

- Work incrementally — complete one logical unit of work at a time.
- After each logical unit, proceed to Step 7 to commit before continuing.
- Logical commit points include: adding a new file, completing a function, fixing a specific bug, adding tests for a module, updating configuration.
- Do not accumulate all changes into a single commit at the end — this makes review harder and loses the development narrative.

## Step 7: Commit at each checkpoint

At each logical checkpoint during development, follow this process:

### 7a: Check for files that should be gitignored

Before staging, review new untracked files:

```bash
git status --porcelain
```

Look for files that should not be committed:

- Environment files: `.env`, `.env.local`, `.env.*.local`
- Secrets: `credentials.json`, `*.pem`, `*.key`, `token.txt`
- OS files: `.DS_Store`, `Thumbs.db`
- IDE files: `.idea/`, `.vscode/settings.json` (unless the project already tracks it)
- Build artifacts: `node_modules/`, `dist/`, `__pycache__/`, `*.pyc`
- Logs: `*.log`, `npm-debug.log*`

If any such files exist and are not already in `.gitignore`, update `.gitignore` first and commit that change separately:

```bash
echo "pattern" >> .gitignore
git add .gitignore
git commit -m "chore: add pattern to .gitignore"
```

Adapt the commit message prefix to match `COMMIT_CONVENTION`.

### 7b: Stage specific files

Stage only the files related to the current logical change. Always name files explicitly:

```bash
git add src/auth/login.ts src/auth/login.test.ts
```

Review what is staged before committing:

```bash
git diff --cached --stat
```

### 7c: Write and execute the commit

Write a commit message following `COMMIT_CONVENTION`. The message must:

- Match the project's prefix style, tense, scope usage, and capitalization
- Describe the change concisely and accurately
- Contain no Co-Authored-By line, no signatures, no attribution of any kind

```bash
git commit -m "feat(auth): add login endpoint with JWT validation"
```

The commit message is exactly the text above — nothing appended, nothing added after the fact.

### 7d: Return to Step 6

Continue development until the implementation is complete.

## Step 8: Simplify pass

Once the implementation is working and tested — but before reporting completion or opening a PR — run the built-in `simplify` skill as a dedicated cleanup/refactor pass over the recently changed code:

```
Invoke the Skill tool with skill: "simplify"
```

`simplify` reviews changed code for reuse, quality, and efficiency, then fixes the issues it finds. Treat it as a final-mile polish, not a per-commit formatter — it works best when there is a meaningful surface of new code to evaluate.

After `simplify` completes:

- If it made changes, review them, then commit the cleanup separately following `COMMIT_CONVENTION` (e.g., `refactor: simplify auth helpers`). Do not fold simplify edits into unrelated feature commits — keep the cleanup as its own logical commit so reviewers can see the polish step.
- If it made no changes, proceed directly to the next step.

Skip this step only if the work was a trivial one-line fix where there is nothing meaningful to simplify.

## Step 9: Final status

After all work is committed, show a summary:

```bash
# All commits made on this branch
git log --oneline main..HEAD

# Confirm nothing is left uncommitted
git status
```

Report to the user:

- Branch name and linked issue number
- Number of commits made
- Summary of what was implemented
- Remind the user that nothing has been pushed — they can review, squash, or push when ready

## What's Next

After the final status report, offer the user a path forward:

> Ready to open a PR? I can run `/gh-pr` to push and create a pull request.

Wait for the user to confirm before proceeding. Do not automatically invoke `/gh-pr`.

## Multi-issue parallel development

When the user wants to work on multiple issues simultaneously (e.g., "implement issues 17, 18, 19 in parallel"), use this workflow instead of the serial Steps 1-8 above.

### Create all linked branches first

Before dispatching any agents, create all issue branches with the `issues/N` naming convention:

```bash
gh issue develop 17 --name "issues/17" --base dev --checkout=false
gh issue develop 18 --name "issues/18" --base dev --checkout=false
gh issue develop 19 --name "issues/19" --base dev --checkout=false
```

Key flags:
- `--name "issues/N"` — enforces the naming convention (without this, GitHub auto-generates names from issue titles)
- `--checkout=false` — creates the branch on the remote without switching locally (important when creating multiple branches)
- `--base` — specifies the base branch if not the default

### Dispatch agents on worktrees

After creating the linked branches, dispatch parallel agents using `isolation: "worktree"`. Each agent receives **one issue** to implement.

**Inject commit rules into every agent prompt.** Before dispatching any agent, read `templates/commit-template.md` (relative to this skill's directory) and include its full content in the agent prompt. Subagents do not load the gh-dev skill, so they will follow system-level defaults (which inject Co-Authored-By trailers) unless explicitly overridden by the template.

**Each agent must work independently.** Do not structure prompts so that one agent's work depends on another agent's output. Every agent should:

- Branch from the same base branch (e.g., `main` or `dev`)
- Contain all the context it needs in its own prompt — do not reference other issues being developed in parallel
- Implement its feature as if it were the only change being made to the codebase
- Run the `simplify` skill as a final cleanup pass after the implementation is working and tested, and commit any resulting changes separately before pushing

**Important**: Agents working in worktrees get their own branch names (`worktree-agent-XXXXX`), not the issue-linked branch names. Include explicit push instructions in each agent's prompt:

```
After committing, push your work to the issue branch:
git push origin HEAD:issues/N
```

Alternatively, have the agent check out the issue branch inside the worktree before starting:

```
git checkout issues/N
```

### After agents complete

If agents used worktree branch names, push each to its corresponding issue branch:

```bash
# From each worktree directory
git push origin worktree-agent-XXXXX:issues/17
git push origin worktree-agent-YYYYY:issues/18
git push origin worktree-agent-ZZZZZ:issues/19
```

If there are conflicts due to the issue branch having extra commits (e.g., from the base branch), rebase first:

```bash
git fetch origin
git rebase origin/issues/N
# Resolve conflicts if any
git push origin HEAD:issues/N
```

### Handling shared code

If multiple issues touch the same files or share a dependency, **do not create sequential dependencies between agents**. Instead, choose one of:

- **Pre-land shared work**: Implement the shared piece on the base branch first, push it, then create the issue branches. All agents start from the same updated base.
- **Duplicate and reconcile**: Let each agent independently implement what it needs (even if overlapping), then resolve conflicts during PR review/merge. This preserves true parallelism at the cost of minor merge work later.

Never make one agent wait for another agent to finish.

## Gotchas

Before running any `gh` command, verify that the CLI is available and authenticated:

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

Do not proceed until `gh auth status` succeeds.

- **Always pass --name with exact issues/N value** -- Without `--name`, GitHub auto-generates branch names from issue titles. Even when `--name` is provided, the value must be exactly `issues/N` — never a descriptive name like `6-macro-management` or anything derived from the issue title. The convention is `issues/ISSUE_NUMBER`, no exceptions. Use `gh issue develop N --name "issues/N"` every time. Common mistake: the model passes `--name` but invents a custom name instead of following the `issues/N` pattern.

- **Worktree agents use their own branch names** -- When dispatching parallel agents with `isolation: "worktree"`, each agent works on a `worktree-agent-XXXXX` branch, not the issue-linked branch. After the agent completes, you must push with an explicit refspec: `git push origin worktree-agent-XXXXX:issues/N`. To avoid this, instruct agents to `git checkout issues/N` inside the worktree before starting work, or include the refspec push command in the agent prompt.

- **Subagents ignore skill hard rules** -- Worktree agents dispatched via `isolation: "worktree"` do not inherit the gh-dev skill's instructions. The system-level harness injects a Co-Authored-By trailer by default, which the agent will follow unless explicitly overridden. Fix: read `templates/commit-template.md` and inject its content into every agent prompt. This is mandatory — without it, every subagent commit will have a Co-Authored-By trailer.

If the repository has no GitHub remote, inform the user that a remote is required and suggest:

```bash
gh repo create
# or
git remote add origin https://github.com/{owner}/{repo}.git
```

## Hard rules

- Never run `git push`, `git push --force`, or any command that sends commits to the remote.
- Never append Co-Authored-By, signatures, or attribution of any kind to commit messages.
- Never use `git add .`, `git add -A`, or `git add --all`. Always stage files by explicit path.
- Never amend a commit that has been pushed to the remote.
- Never force-delete branches (`git branch -D`).
- Never silently discard uncommitted changes — always ask the user first.
- Never commit files that likely contain secrets (.env, credentials, keys, tokens). If such files appear as untracked, update .gitignore and commit that change first.
- Commit messages must match the project's existing conventions — do not invent a new style.
