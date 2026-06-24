---
name: apply-coding-rules
description: >-
  Stamp a managed coding-discipline rules block into a project's CLAUDE.md (or AGENTS.md / GEMINI.md) — the four
  rules: think before coding, simplicity first, surgical changes, goal-driven execution, plus a guard on
  irreversible/git-history actions. This skill is the single source of truth for those rules; running it writes or
  updates the rules between managed markers, idempotently, leaving the rest of the file untouched. Use when the user
  wants to add, update, sync, or propagate the shared coding rules / coding standards into a repository — "apply the
  coding rules", "add the four rules to this project's CLAUDE.md", "sync our coding standards here", "stamp the
  coding discipline block" — even if they don't name the skill.
---

# apply-coding-rules

This skill owns the canonical text of the shared coding-discipline rules and stamps it into a target repository's
agent instruction file, idempotently. Edit the block **here**, re-run in each project, and every project updates.

## Canonical rules block

This is the single source of truth. Write it **verbatim** (including the marker comments) into the target file:

```markdown
<!-- coding-rules:start (managed by chuan-skills/apply-coding-rules) -->
## Coding discipline

- **Think before coding.** Don't assume, and don't hide confusion — surface tradeoffs instead of burying them.
  When requirements are ambiguous, state your assumptions and ask before proceeding. Before any irreversible or
  wide-impact action — especially git history rewrites (`rebase`, `reset`, `force-push`) — explain the blast radius
  and wait for confirmation.
- **Simplicity first — walk the decision ladder.** Write the minimum code that solves the actual problem. Before
  writing new code, climb this ladder and stop at the first rung that works: (1) is it needed at all? (2) does the
  codebase already have it? (3) standard library? (4) a native platform/OS/browser feature? (5) an already-installed
  dependency? (6) a one-liner? (7) only then, the smallest viable implementation. No speculative features, no
  premature abstraction, no "while I'm here" extras. Simplicity never trims safety: input/trust-boundary validation,
  error and data-loss handling, security, and accessibility always stay.
- **Surgical changes.** Touch only what the task requires. Clean up only the code you introduced; do not
  opportunistically refactor, rename, or reorder unrelated code in the same change.
- **Goal-driven execution.** Define a verifiable success criterion first (a test, an acceptance check), then loop —
  implement, run it, repeat — until it passes. Prefer test-first when a test is feasible.
<!-- coding-rules:end -->
```

## Workflow

1. **Pick the target file.** Default to `CLAUDE.md` in the repo root (the working directory). If the user names a
   different agent file (`AGENTS.md`, `GEMINI.md`) or the repo only has that one, use it. If none exists, create
   `CLAUDE.md`.
2. **Stamp idempotently.**
   - If the file already contains a `<!-- coding-rules:start ... -->` … `<!-- coding-rules:end -->` block, **replace
     everything between (and including) the markers** with the current canonical block. Leave all other content untouched.
   - If there are no markers, **append** the canonical block to the end of the file (with one blank line before it).
   - Never duplicate the block, and never edit content outside the markers.
3. **Allow per-project additions.** If the user wants project-specific rules (e.g. AutoTrade: "validate correctness
   with the project's own test set before trusting any change"), add them as extra bullets **inside** the managed
   block so they survive re-stamping, or as a separate clearly-labelled section **outside** the markers if they
   should not be overwritten. Ask which they prefer when they request a custom rule.
4. **Report.** State which file was written, whether it was a create / update / first-stamp, and show the final
   block. Do not commit unless the user asks — surface the change and let them commit.

## Notes

- This is for **ambient** rules that should always apply, which is why they live in `CLAUDE.md` (always loaded), not
  in skill bodies (loaded on demand). For "all my projects at once", the user can also paste the same canonical
  block into their user-level `~/.claude/CLAUDE.md`.
- Keep the canonical block the single source of truth: change it here, then re-run this skill in each repo to propagate.
