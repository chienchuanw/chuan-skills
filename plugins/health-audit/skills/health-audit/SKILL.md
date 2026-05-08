---
name: health-audit
description: >
  Manually-triggered comprehensive codebase health audit covering security, architecture,
  documentation drift, dead code, and test coverage gaps. Produces a ranked markdown report,
  files prioritized GitHub issues, and proposes (but never autonomously opens) auto-fix PRs
  for trivial safe changes. Use when the user wants to audit, scan, review the health of,
  do a security check on, find dead code in, check doc drift in, or get a backlog of
  improvement issues for a repository — e.g. "/health-audit", "audit this repo",
  "do a full health check", "scan for issues to file", "check what's rotting in here".
  Not for ad-hoc bug hunts on a single file — use feature-dev:code-reviewer for that.
---

# health-audit

Run a five-dimension health audit on the current repository, rank findings by risk × effort, file GitHub issues for actionable items, and propose safe auto-fixes for the user to approve. This skill is **read-mostly**: it never opens PRs autonomously and never edits source code without explicit approval. Issues are filed via `gh-issue`; the report lands as a markdown file in `audits/`.

## Phase 0 — Pre-flight

Before any scanning:

1. **Confirm the working tree is clean.** Run `git status --porcelain`. If dirty, ask the user how to proceed (stash / commit / abort) — do not silently mix audit findings with in-progress work.
2. **Detect language convention.** Inspect the latest 5 issues, README, and CLAUDE.md to infer the project's preferred language for issues and reports (English, Traditional Chinese, etc.). If signals conflict or are absent, ask the user once.
3. **Detect tooling.** Read `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile` to identify: package manager, test runner, lint command, typecheck command, and dependency-audit command (`pnpm audit`, `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, etc.).
4. **Confirm scope.** Show the user which dimensions you will run (default: all five). Let them narrow if they want a faster pass.

## Phase 1 — Parallel scans

Dispatch the four read-only audit dimensions **in parallel** using the Agent tool with `subagent_type: "general-purpose"`. Each agent returns a structured finding list. Use a single message with multiple Agent tool calls so they run concurrently.

**Common return-format every agent must follow.** Restate this verbatim inside each agent's prompt — do not assume the agent will infer the shape:

```
Return ONLY a JSON array of findings. Each finding:
{
  "severity": "high" | "medium" | "low",
  "file": "<repo-relative path>",
  "line": <number or null>,
  "summary": "<one sentence>",
  "suggested_fix": "<one or two sentences>"
}
Cap your output at 25 findings, ranked highest-severity first.
If you have more, append a final element:
{"severity": "info", "file": null, "line": null, "summary": "N additional <severity> findings truncated", "suggested_fix": null}
If a tool you need is not installed, return one finding with severity "info" and summary "DEGRADED: <tool> not available, used <fallback>" — do not abort.
```

The 25-finding cap and truncation marker prevent main context from blowing up on large repos.

### Security dimension

Brief: scan for secrets in tracked files (API keys, tokens, private keys), unsafe deserialization (`pickle.loads`, `eval`, `Function()`, YAML `load` without `SafeLoader`), missing auth checks on routes/handlers, SQL injection risks (string-concatenated queries, unparameterized inputs), and outdated dependencies with known CVEs.

Tools: `git ls-files`, `rg` for patterns, the project's dep-audit command from Phase 0.

Restate the common return-format block above in the agent prompt.

### Architecture dimension

Brief: run `graphify` on the repo to build a dependency graph, then identify circular dependencies, god modules (high fan-in + fan-out), and critical paths with low test coverage.

If `graphify` is unavailable, fall back by language:

| Language | Fallback |
|----------|----------|
| JavaScript / TypeScript | `madge --circular` |
| Python | `pydeps` or `pyan` |
| Go | `go mod graph` + `go list -deps` |
| Rust | `cargo modules` |
| Other | `rg`-based import-graph heuristic |

Pick the fallback that matches the languages identified in Phase 0 — do not run `madge` on a Python project. Note the degraded mode via the "DEGRADED" info finding in the return format.

Restate the common return-format block above in the agent prompt.

### Documentation drift dimension

Brief: diff CLAUDE.md and README against the current code. Flag:
- Models, classes, or modules referenced in docs that no longer exist
- Undocumented environment variables (anything in `process.env.*`, `os.environ[...]`, `.env.example` not mentioned in README/CLAUDE.md)
- Stale commands (commands in README that no longer match `package.json` scripts / Makefile targets)
- New top-level directories or major modules introduced after CLAUDE.md was last updated

Restate the common return-format block above in the agent prompt.

### Dead code + test coverage dimension

Brief: find unreferenced exports (`ts-prune`, `vulture`, or grep-based fallback), orphaned files (no inbound imports), unused dependencies (`depcheck`, `pip-extra-reqs`), and critical business-logic paths with no test coverage. "Critical" = code in payment, auth, data persistence, or anything in a path the user has flagged as load-bearing.

Tool selection should match the language detected in Phase 0 — do not invoke `ts-prune` on a Python project.

Restate the common return-format block above in the agent prompt.

### Aggregation rules

After all four agents return:

- If **0 of 4 succeeded** (all returned errors or empty), abort the audit. Surface the failures and ask the user how to proceed — do not write an empty report.
- If 1-3 succeeded, continue to Phase 2 with the dimensions that worked. Note the failed dimensions clearly in the report's Summary section.

## Phase 2 — Rank and report

Aggregate findings from all four agents. Score each finding on:

- **Risk** (1-5): impact if unaddressed (security → high, dead code → low)
- **Effort** (1-5): rough sizing of the fix
- **Score** = Risk / Effort (higher = better ROI)

Ensure the report directory exists before writing:

```bash
mkdir -p audits
```

Write `audits/<YYYY-MM-DD>-health-audit.md` with:

```markdown
# Health Audit — <date>

## Summary
<short prose: how many findings per dimension, top 3 risks>

## Findings (ranked)
| # | Dim | Severity | File | Summary | Risk | Effort | Score |
|---|-----|----------|------|---------|------|--------|-------|
| 1 | sec | high | src/auth.ts:42 | unparameterized query | 5 | 2 | 2.5 |
...

## Detailed findings
### [SEC-1] Unparameterized query in src/auth.ts:42
**Severity:** high
**Reproduction:** ...
**Suggested fix:** ...

(repeat per finding)

## Architectural facts discovered
<bullet list of new facts that should be added to CLAUDE.md, e.g. "uses
GeoLite2 for IP-to-country lookups", "auth middleware lives in lib/auth/">
```

The report is the **single source of truth** for the rest of the workflow.

## Phase 3 — File issues **[CHECKPOINT]**

Show the user the ranked table and ask: which findings should become GitHub issues? Default suggestion: everything with Severity ≥ medium. The user may:

- Accept the default
- Pick a subset
- Skip issue filing entirely (report-only mode)

**Dedupe before filing.** Run `gh issue list --state open --label audit:* --limit 200 --json number,title` and compare titles against the findings selected for filing. For any near-match (same dimension + same file:line + similar summary), do not refile — instead, link the existing issue number in the report and tell the user it was skipped as duplicate.

For each chosen finding, invoke the `gh-issue` skill with:
- Title in the project's detected language
- Body including: summary, reproduction, suggested fix, link to the line(s) in the report
- Severity label (`severity:high`, `severity:medium`, `severity:low`) — create the labels if they do not exist
- Dimension label (`audit:security`, `audit:architecture`, `audit:doc-drift`, `audit:dead-code`)

Never file all issues silently. Always show the list and pause.

## Phase 4 — Auto-fix proposals **[CHECKPOINT, off by default]**

Identify findings that qualify as **trivial safe fixes**:

- Typos in comments/docs
- Unused imports
- Missing TypeScript types where inference is obvious
- Dead exports with zero references
- Documented-but-missing env vars in `.env.example`

Present this list to the user. **Do not open any PRs unless the user explicitly says so** — this respects the global Git/PR Workflow Rules in `~/.claude/CLAUDE.md`.

If approved, for each cluster of safe fixes:
1. Use the `superpowers:using-git-worktrees` skill to create an isolated worktree
2. Apply the fix
3. Invoke the `gh-pr` skill to open the PR with `audit:auto-fix` label

Cluster fixes by file or theme to avoid 20 single-line PRs.

## Phase 5 — Update CLAUDE.md (optional)

If Phase 1's doc-drift dimension surfaced **new architectural facts** (newly-introduced modules, env vars, or conventions absent from the current CLAUDE.md), present them and ask whether to append. If approved, edit CLAUDE.md directly — this is not a PR-worthy change unless the project's CLAUDE.md says otherwise.

## Hard rules

- **Never** open a PR without explicit user approval at Phase 4.
- **Never** file issues silently — always show the list at Phase 3.
- **Never** edit source code outside an approved Phase-4 worktree.
- **Never** commit the `audits/` report unless the user asks — leave it untracked or staged depending on user preference.
- **Never** spawn more than one set of parallel scan agents — if a scan needs to be re-run, run sequentially to avoid race conditions on shared report files.
- **Never** assume `graphify` exists. Detect, fall back, and note degraded mode.
- The audit is a snapshot. Date the report, do not overwrite previous audits.

## Failure recovery

If any scan agent fails:
1. Note the failed dimension in the report ("Architecture: scan failed — graphify exited 1")
2. Continue with the dimensions that succeeded
3. Surface the failure to the user at Phase 2 so they can decide whether to re-run

Do not block the entire audit on one failed dimension. Partial reports are still useful.
