---
name: gh-issue
description: >
  Create structured GitHub issues via gh CLI using type-specific templates (bug, feat, refactor,
  doc, perf, security). Use when filing bugs, requesting features, tracking work, opening tickets,
  or any intent to create a GitHub issue — even implicit phrases like "track this" or "file this".
---

# gh-issue

Create a GitHub issue with structured, agent-friendly content using the `gh` CLI. Issues follow type-specific templates so that any agent picking up the issue later has enough context to implement without asking follow-up questions.

Supported issue types:

| Type | Shorthand | Use when |
|------|-----------|----------|
| Bug | `bug` | Something is broken, crashing, or behaving incorrectly |
| Feature | `feat` | A new capability, endpoint, component, or user-facing behavior |
| Refactor | `refactor` | Restructuring code without changing external behavior |
| Documentation | `doc` | Missing, outdated, or incomplete documentation |
| Performance | `perf` | Slowness, high memory usage, or optimization opportunities |
| Security | `security` | Vulnerabilities, auth issues, data exposure risks |

## Step 1: Determine language

Decide which language to use for the issue content. Check in this order:

1. If the user explicitly states a language preference in this conversation, use that.
2. Read `CLAUDE.md` in the project root. If it is written in Traditional Chinese or contains a language directive (e.g., `language: zh-TW`), use Traditional Chinese.
3. Default to **English**.

When the user asks for "Chinese" without specifying a variant, default to Traditional Chinese (繁體中文).

Store the result as `ISSUE_LANG` — either `en` or `zh-TW`. This determines which template file to read in Step 4.

## Step 2: Determine issue type

Map the user's request to one of the six types. Use these signals:

- **Bug**: "bug", "broken", "not working", "error", "crash", "regression", "fails", "unexpected behavior"
- **Feat**: "feature", "add", "new", "support for", "it would be nice", "request", "enhancement"
- **Refactor**: "refactor", "clean up", "restructure", "tech debt", "code smell", "reorganize"
- **Doc**: "document", "docs", "README", "examples", "API reference", "missing docs"
- **Perf**: "slow", "performance", "optimize", "latency", "memory", "speed up", "bottleneck"
- **Security**: "vulnerability", "CVE", "security", "auth bypass", "injection", "exposure", "leak"

If the type is ambiguous, ask the user with `AskUserQuestion` presenting the six options.

Store the result as `ISSUE_TYPE` (one of: `bug`, `feat`, `refactor`, `doc`, `perf`, `security`).

## Step 3: Gather context

Run these commands in parallel to understand the repo and existing issues:

```bash
# Repo info
gh repo view --json nameWithOwner,url --jq '.nameWithOwner'

# Available labels (only use labels that actually exist)
gh label list --limit 100 --json name --jq '.[].name'

# Open issues (check for duplicates)
gh issue list --limit 20 --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
```

Also gather context from the conversation and codebase:

- If the user mentioned specific files, functions, or errors, read those files to collect concrete details (file paths, line numbers, function signatures).
- If the user described a bug, try to trace the relevant code path.
- If the user described a feature, identify the modules and files that would be affected.

The goal is to fill the template with **specific, concrete information** — not vague placeholders.

## Step 4: Fill the template

Read the appropriate template from `<skill-path>/templates/{ISSUE_TYPE}.md` (or `{ISSUE_TYPE}-zh-TW.md` if `ISSUE_LANG` is `zh-TW`).

Fill in every section using information gathered in Steps 2 and 3. For each template section:

- Replace placeholder guidance text with concrete details from the conversation and codebase.
- Include actual file paths with line numbers (e.g., `src/auth/middleware.ts:42`).
- Write acceptance criteria as specific, testable checkbox items.
- If a section truly cannot be filled because information is missing, write a clear note explaining what is needed — do not leave the placeholder text as-is.

Compose the issue title:
- Format: `type: Concise description of the issue`
- Type prefix uses the lowercase shorthand followed by a colon: `bug:`, `feat:`, `refactor:`, `doc:`, `perf:`, `security:`
- Keep under 80 characters total
- Be specific — "bug: Login 500 error with plus-sign emails" is better than "bug: Fix bug"

## Step 5: Present for review

Show the user the complete issue in a fenced markdown block:

````
**Title:** type: The issue title

**Labels:** label1, label2
**Assignee:** (if identified)
**Milestone:** (if identified)

---

{filled template body}
````

Use `AskUserQuestion` to ask the user to approve or request changes. If the user requests changes, revise and present again.

For labels: only suggest labels that appeared in the `gh label list` output from Step 3. If no matching labels exist, omit the labels line entirely.

## Step 6: Create the issue

After the user approves, create the issue:

```bash
gh issue create \
  --title "{title}" \
  --body "$(cat <<'ISSUE_EOF'
{filled template body}
ISSUE_EOF
)" \
  --label "{label1},{label2}" \
  --assignee "{assignee}" \
  --milestone "{milestone}"
```

Only include `--label`, `--assignee`, and `--milestone` flags if values were identified and confirmed. Do not include flags with empty values.

After creation, report the issue URL back to the user.

## What's Next

After reporting the issue URL, offer to start development:

> Issue #N created. Want me to start development? I can run `/gh-dev` to create a branch and begin implementation.

Replace `N` with the actual issue number from the created issue.

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

Walk the user through the interactive prompts (select GitHub.com vs Enterprise, preferred protocol, and authentication method). Do not proceed with issue creation until `gh auth status` succeeds.

If the repository has no GitHub remote (e.g., a purely local repo), inform the user that a remote is required and suggest:

```bash
gh repo create
# or
git remote add origin https://github.com/{owner}/{repo}.git
```

## Hard rules

- Never create an issue without showing the full content to the user first and getting explicit approval.
- Never invent GitHub labels. Only use labels returned by `gh label list`.
- Every issue body must contain enough context for an agent to implement the work without follow-up questions: specific file paths, function names, expected vs actual behavior, and testable acceptance criteria.
- No emojis in issue titles or bodies.
- Issue titles must be under 80 characters and start with a lowercase type prefix followed by a colon (e.g., `bug:`, `feat:`).
- Never modify any files in the repository. This skill only creates GitHub issues.
- When checking for duplicate issues in Step 3, if a highly similar open issue exists, inform the user before proceeding.
- Never include a signature, attribution line, or "posted by" footer in issue titles or bodies (e.g., "— Claude", "Generated by Claude Code", "🤖 Generated with Claude Code", or any `Co-Authored-By:` trailer). Issues must read as if the user wrote them.
