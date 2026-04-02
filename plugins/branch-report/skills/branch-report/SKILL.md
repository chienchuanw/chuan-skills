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

This skill uses multiple sub-agents to ensure accuracy. Each agent has a dedicated role defined in the `agents/` directory:

| Agent | File | Purpose | Runs |
|-------|------|---------|------|
| Project Context Scout | `agents/scout.md` | Explores codebase to understand architecture and conventions | First |
| Simple Explainer | `agents/explainer.md` | Writes toddler-friendly change summary | Parallel with Analyst |
| Change Analyst | `agents/analyst.md` | Produces senior developer review with confidence tags | Parallel with Explainer |
| Cross-Checker | `agents/checker.md` | Verifies every technical claim against actual source code | Last |

## Language

By default, write the report in English. If the user asks for the report in another language (e.g., "用中文", "Chinese", "繁體中文"), write the entire report in that language instead — including section headings, metadata labels, bullet points, and the senior developer review. The only things that stay in their original form are git output (commit hashes, branch names, file paths, code snippets) since those are language-neutral.

When the user asks for "Chinese" without specifying, default to **Traditional Chinese (繁體中文)**.

Determine the target language now and pass it to all sub-agents as REPORT_LANGUAGE (either "English" or "Traditional Chinese").

## Step 1: Detect branches

### Determine the target branch

If the user specifies a branch name (e.g., "review branch feature/login", "generate report for develop"), use that as the **target branch**. Otherwise, default to the current branch:

```bash
# Current branch (used when user does not specify one)
git branch --show-current
```

If the user specified a branch, verify it exists:

```bash
git rev-parse --verify {target_branch} 2>/dev/null
```

If the branch does not exist, tell the user: "Branch '{target_branch}' not found. Check the name and try again." and stop.

### Determine the default (base) branch

```bash
# Default branch (try symbolic ref first, then scan remotes)
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
```

If the symbolic ref fails, fall back to:

```bash
git branch -r | grep -E 'origin/(main|master)' | head -1 | sed 's@.*origin/@@' | tr -d ' '
```

If neither works, check for local `main` or `master` branches. If no default branch can be determined, ask the user which branch to compare against.

### Stop conditions

- If using the current branch and `git branch --show-current` returns empty, the repo is in detached HEAD state. Tell the user: "You are in detached HEAD state. Please check out a branch or specify one." and stop.
- If the target branch is the same as the default branch, tell the user: "'{target_branch}' is the default branch. Specify a feature branch to generate a report." and stop.

### Find the fork point

```bash
git merge-base {target_branch} origin/{default_branch}
```

If the remote-tracking branch does not exist (e.g., `origin/main` is missing), try the local default branch instead:

```bash
git merge-base {target_branch} {default_branch}
```

Use `{target_branch}` (not `HEAD`) in all subsequent git commands so the report works correctly even when inspecting a branch you haven't checked out.

## Step 2: Gather diff context

Run all of these in parallel:

```bash
# Commit list since fork point
git log --oneline {merge_base}..{target_branch}

# Detailed commit messages (for understanding intent)
git log --format="%h %s%n%b" {merge_base}..{target_branch}

# File change summary
git diff --stat {merge_base}..{target_branch}

# Full diff (for detailed analysis)
git diff {merge_base}..{target_branch}

# Uncommitted changes check (only relevant when target is the current branch)
git status --short
```

If the commit log is empty (no commits ahead of the default branch), tell the user: "Branch '{target_branch}' has no commits ahead of {default_branch}. Nothing to report." and stop.

Store these results — they will be passed to sub-agents in the following steps.

## Step 3: Gather project context

Read `<skill-path>/agents/scout.md` for the full agent definition.

Use the Agent tool to spawn the **Project Context Scout**. This agent explores the codebase to build a project profile BEFORE anyone looks at the diff. The Change Analyst needs this profile to understand the project's conventions and avoid flagging intentional design choices as problems.

Pass no diff data to this agent — it should only explore the baseline codebase.

Store the agent's response as PROJECT_CONTEXT.

## Step 4: Analyze changes (two sub-agents in parallel)

Read `<skill-path>/agents/explainer.md` and `<skill-path>/agents/analyst.md` for the full agent definitions.

Use the Agent tool to spawn **two sub-agents in parallel** (in a single message with two Agent tool calls):

**Sub-agent A — Simple Explainer:** Pass the commit log and diff stat (NOT the full diff). Replace `{REPORT_LANGUAGE}`, `{commit_log}`, and `{diff_stat}` placeholders in the agent definition with the actual data.

**Sub-agent B — Change Analyst:** Pass the PROJECT_CONTEXT, full diff, and commit log. Replace `{REPORT_LANGUAGE}`, `{PROJECT_CONTEXT}`, `{commit_log}`, and `{full_diff}` placeholders in the agent definition with the actual data.

Wait for both to complete. Store the Simple Explainer's response as SIMPLE_EXPLANATION and the Change Analyst's response as ANALYST_REVIEW.

## Step 5: Cross-check the review

Read `<skill-path>/agents/checker.md` for the full agent definition.

Use the Agent tool to spawn the **Cross-Checker**. This is the quality gate — it verifies every factual claim the Change Analyst made by reading actual source files.

Replace `{REPORT_LANGUAGE}`, `{ANALYST_REVIEW}`, `{PROJECT_CONTEXT}`, and `{full_diff}` placeholders in the agent definition with the actual data.

Store the response as VERIFIED_REVIEW. Extract the Concerns, Suggestions, and What Looks Good sections (excluding the Cross-Check Summary) for use in the final report.

## Step 6: Assemble and write the report

Read the appropriate report template:
- English: `<skill-path>/assets/template.md`
- Traditional Chinese: `<skill-path>/assets/template-zh-TW.md`

Fill in each section of the template:

- **Metadata**: branch_name, default_branch, commit_count, files_changed, date from Steps 1-2.
- **uncommitted_warning**: If `git status --short` showed changes, add the appropriate warning. Otherwise leave blank.
- **commit_list**: Each commit as a bullet point with short hash and message.
- **simple_explanation**: From the Simple Explainer (Step 4).
- **concerns / suggestions / praise**: From the Cross-Checker's verified review (Step 5), excluding the Cross-Check Summary.

Save the completed report to `branch-report.md` in the project root directory. Tell the user the file path.

If a `branch-report.md` already exists, overwrite it — the report reflects the current state of the branch.

## Hard rules

- Never run any command that modifies the working tree, staging area, or repository state. No `git checkout`, `git add`, `git stash`, `git reset`, `git commit`, or `git push`.
- The "Simple Version" section must contain zero technical jargon. If a bullet point would not make sense to a five-year-old, rewrite it until it does.
- Every item in the "Senior Developer Review" must reference a specific change from the diff or commit log. Never give generic advice like "consider adding more tests" without pointing to what specifically lacks test coverage.
- Never fabricate changes. Every claim in the report must be traceable to the actual diff and verified by the Cross-Checker.
- If the diff touches more than 50 files, note that the analysis focuses on the most significant changes and list the remaining files briefly without detailed analysis. Pass only the most impactful file diffs to sub-agents to avoid overwhelming their context.
- Always spawn the Project Context Scout before the Change Analyst. The analyst cannot produce accurate results without understanding the project first.
- Always spawn the Cross-Checker after the Change Analyst. The report must not include unverified technical claims.
