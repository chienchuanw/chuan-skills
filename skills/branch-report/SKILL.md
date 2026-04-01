---
name: branch-report
description: >
  Generates a comparison report between the current git branch and the default branch.
  The report explains changes in plain, simple language anyone can understand, and includes
  a senior developer review with concerns, suggestions, and praise.
  Use this skill whenever the user asks to "compare branches", "what changed on this branch",
  "summarize my branch", "review my changes", "generate a branch report", "diff report",
  "explain my branch changes", "what did I change", or any similar request to understand
  the delta between their working branch and the default branch. Also trigger when the user
  wants a PR summary, a branch overview, or asks someone to look at their changes before merging.
---

# branch-report

Generate a structured report comparing the current branch against the default branch. The report serves two audiences: someone with zero technical background (the "simple version") and a senior developer doing a pre-merge review.

## Language

By default, write the report in English. If the user asks for the report in another language (e.g., "用中文", "Chinese", "繁體中文"), write the entire report in that language instead — including section headings, metadata labels, bullet points, and the senior developer review. The only things that stay in their original form are git output (commit hashes, branch names, file paths, code snippets) since those are language-neutral.

When the user asks for "Chinese" without specifying, default to **Traditional Chinese (繁體中文)**.

## Step 1: Detect branches

Run these commands to identify the branches:

```bash
# Current branch
git branch --show-current

# Default branch (try symbolic ref first, then scan remotes)
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
```

If the symbolic ref fails, fall back to:

```bash
git branch -r | grep -E 'origin/(main|master)' | head -1 | sed 's@.*origin/@@' | tr -d ' '
```

If neither works, check for local `main` or `master` branches. If no default branch can be determined, ask the user which branch to compare against.

**Stop conditions — check these before continuing:**

- If `git branch --show-current` returns empty, the repo is in detached HEAD state. Tell the user: "You are in detached HEAD state. Please check out a branch first." and stop.
- If the current branch is the same as the default branch, tell the user: "You are already on the default branch ({branch}). Switch to a feature branch to generate a report." and stop.

Once both branches are identified, find the fork point:

```bash
git merge-base HEAD origin/{default_branch}
```

If the remote-tracking branch does not exist (e.g., `origin/main` is missing), try the local default branch instead:

```bash
git merge-base HEAD {default_branch}
```

## Step 2: Gather diff context

Run all of these in parallel:

```bash
# Commit list since fork point
git log --oneline {merge_base}..HEAD

# Detailed commit messages (for understanding intent)
git log --format="%h %s%n%b" {merge_base}..HEAD

# File change summary
git diff --stat {merge_base}..HEAD

# Full diff (for detailed analysis)
git diff {merge_base}..HEAD

# Uncommitted changes check
git status --short
```

If the commit log is empty (no commits ahead of the default branch), tell the user: "This branch has no commits ahead of {default_branch}. Nothing to report." and stop.

## Step 3: Analyze and generate the report

Read the appropriate report template:
- English: `<skill-path>/assets/template.md`
- Traditional Chinese: `<skill-path>/assets/template-zh-TW.md`

Choose the template that matches the language the user requested (default: English).

Fill in each section of the template:

### Metadata

- **branch_name**: The current branch name.
- **default_branch**: The default branch being compared against.
- **commit_count**: Number of commits ahead.
- **files_changed**: Number of files changed (from `--stat` output).
- **date**: Today's date.
- **uncommitted_warning**: If `git status --short` shows changes, add: "> **Note:** There are uncommitted changes in the working tree. This report only covers committed changes." Otherwise leave blank.

### Commit list

List each commit as a bullet point with its short hash and message.

### What Changed — The Simple Version

This section is for someone who knows absolutely nothing about programming. Imagine explaining to a curious toddler what you did today at work.

Write 3-5 bullet points that describe the changes using everyday language and analogies. Frame changes in terms of what the app does for people, not how the code works.

**Guidelines for this section:**
- Use words a child would know: "fixed", "added", "changed", "removed", "moved"
- Use analogies to physical things: doors, buttons, drawers, labels, signs, roads
- Talk about what users see or experience, not implementation details
- Never use these words: refactor, endpoint, schema, migration, dependency, API, module, component, middleware, handler, config, parameter, initialize, deploy, render, callback, async, sync, database, query, index, cache, interface, abstract, polymorphism, inheritance

**Good examples:**
- "Added a new button that lets people save their favorite items, like putting a bookmark in a book."
- "Fixed a problem where the app sometimes forgot who you were after you logged in, like a door that kept locking itself."
- "Changed how the app sorts the list of items so the newest ones show up first, like putting the freshest cookies on top of the jar."

**Bad examples (too technical):**
- "Refactored the authentication middleware to use JWT tokens."
- "Added a new REST API endpoint for user preferences."
- "Migrated the database schema to support polymorphic associations."

### Senior Developer Review

This section speaks to an experienced developer. Be specific and reference actual changes from the diff. Every point must trace back to something visible in the code.

**Concerns:** Issues that could cause bugs, security vulnerabilities, performance problems, or maintenance headaches. Be direct about what the risk is and where it lives. If there are no real concerns, say so — don't manufacture them.

**Suggestions:** Improvements that would make the code better — cleaner structure, better naming, missing tests, error handling gaps, opportunities to simplify. Each suggestion should be actionable: say what to change and where.

**What Looks Good:** Genuine praise for things done well — good patterns, clean abstractions, thoughtful error handling, well-written tests. This section matters because it reinforces good habits and makes the review feel balanced rather than purely critical.

## Step 4: Write the report

Save the completed report to `branch-report.md` in the project root directory. Tell the user the file path so they can find it.

If a `branch-report.md` already exists, overwrite it — the report is meant to reflect the current state of the branch.

## Hard rules

- Never run any command that modifies the working tree, staging area, or repository state. No `git checkout`, `git add`, `git stash`, `git reset`, `git commit`, or `git push`.
- The "Simple Version" section must contain zero technical jargon. If a bullet point would not make sense to a five-year-old, rewrite it until it does.
- Every item in the "Senior Developer Review" must reference a specific change from the diff or commit log. Never give generic advice like "consider adding more tests" without pointing to what specifically lacks test coverage.
- Never fabricate changes. Every claim in the report must be traceable to the actual diff.
- If the diff touches more than 50 files, note that the analysis focuses on the most significant changes and list the remaining files briefly without detailed analysis.
