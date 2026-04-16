---
name: gh-archive
description: >
  Capture the current state of a project by updating documentation at the end of a development session.
  Invokes the readme skill to refresh README.md and the planning-with-files skill to record project status
  in a doc/ or docs/ directory. Use after merging a PR, finishing a feature, wrapping up a coding session,
  or any time the user wants to snapshot where the project stands — even implicit phrases like "archive this",
  "wrap up the session", "document current status", "update project docs", "snapshot this repo", or
  "I'm done for today". Also use when the user says "end of session" or asks to prepare documentation
  before stepping away from a project.
---

# gh-archive

Capture the current state of a project at the end of a development session by orchestrating two existing skills: **readme** (for README.md) and **planning-with-files** (for project status tracking). This skill automates the documentation step you'd otherwise do manually before stepping away.

## Workflow

### Step 1: Gather session context

Understand what happened during this session so the documentation reflects reality:

- `git log --oneline -20` — recent commits
- `git branch --show-current` — current branch
- `gh pr list --state merged --limit 5` — recently merged PRs (skip if gh CLI is unavailable)
- `git diff --stat HEAD~10` — scope of recent changes (adjust range based on session length)

Take note of key themes: what features were added, what bugs were fixed, what was refactored. This context informs both the README update and the status files.

### Step 2: Detect language

Check existing documentation for written language:

1. Read README.md if it exists
2. Check files in `doc/` or `docs/` if they exist
3. Use the detected language for all generated content
4. Default to English if no existing documentation is found

If the user explicitly specifies a language, use that instead regardless of what exists.

### Step 3: Detect or create documentation directory

Look for an existing documentation directory in this order:

1. `docs/` exists → use it
2. `doc/` exists → use it
3. Neither exists → create `doc/` with `mkdir -p doc`

Store the resolved path (e.g., `docs/` or `doc/`) as `{doc_dir}`. Every file created in Steps 5 must go inside this directory — never in the project root.

### Step 4: Update README.md

Invoke the **readme** skill to update or create the project's README.md.

```
Skill: readme
```

The readme skill handles its own detection of project structure, metadata, and content. Let it do its job — no need to pre-process anything for it.

### Step 5: Update project status files

Invoke the **planning-with-files** skill to capture current project status.

```
Skill: planning-with-files
```

**Directory override:** The planning-with-files skill normally creates `task_plan.md`, `findings.md`, and `progress.md` in the project root. For gh-archive, all three files must go inside `{doc_dir}/` (the directory resolved in Step 3). Concretely:

- Write `{doc_dir}/task_plan.md` (not `./task_plan.md`)
- Write `{doc_dir}/findings.md` (not `./findings.md`)
- Write `{doc_dir}/progress.md` (not `./progress.md`)

If these files already exist in `{doc_dir}/`, update them to reflect the current session. If they exist in the project root but not in `{doc_dir}/`, move them into `{doc_dir}/` first, then update.

### Step 6: Report what was captured

Provide a brief summary:

- Whether README.md was created or updated, and what changed
- Which status files were created or updated in the documentation directory
- Key highlights from the session that were documented
