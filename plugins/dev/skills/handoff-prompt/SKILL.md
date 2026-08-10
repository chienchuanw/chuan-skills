---
name: handoff-prompt
description: >-
  Companion to the `handoff` skill that closes the last mile of a session handoff. After `/handoff` has written a
  handoff document to the OS temp directory, run this in the SAME (ending) session to emit a copy-paste English
  prompt an engineer pastes into a FRESH session so a new agent resumes the work seamlessly. It reads the just-saved
  handoff doc plus current context, runs a lightweight reality check against the repo, and outputs a hybrid prompt:
  a pointer to the doc path plus a distilled orientation, next action, acceptance criteria, and suggested skills.
  Use when a session is wrapping up and the user wants the exact prompt to bootstrap the next session — "give me the
  handoff prompt", "what do I paste into the new session", "產生接手 prompt", "handoff-prompt", "下一輪要貼什麼".
  Manual-only (`disable-model-invocation`). It does NOT write the handoff doc (that is `/handoff`) and does NOT
  launch a background agent (that is `claude-handoff`).
argument-hint: "(optional) what the next session will focus on"
disable-model-invocation: true
---

# handoff-prompt

The last mile of a session handoff. `/handoff` writes a handoff document to the OS temp directory but stops there —
the human is left guessing what to paste into a new session. This skill produces that paste string: a single
copy-paste English prompt that boots a fresh agent into the work with sufficient and *correct* context.

**Run this in the same session that is ending, after `/handoff` has already run.** The output is for the human to
copy — end your turn with the prompt in a fenced code block and nothing important after it.

## Step 1 — Locate the handoff document

Find the handoff doc `/handoff` just wrote, in this order:

1. **From this session's context (preferred).** `/handoff` ran earlier in this same conversation and reported the
   path it saved to. Use that path.
2. **Fallback — newest in temp.** If the path isn't in context, glob the OS temp directory (`$TMPDIR`, `/tmp`) for
   the most recently modified handoff-like markdown file (e.g. `*handoff*.md`) and use the newest.
3. **Fallback — ask.** If neither yields a file, ask the user for the path.

**If no handoff document exists at all** (none in context, none in temp): do **not** improvise a prompt from
context. Stop and tell the user to run `/handoff` first, then re-run `/handoff-prompt`. Keeping the two skills
single-purpose is deliberate — `/handoff` writes, this skill packages.

Read the located document.

## Step 2 — Lightweight reality check

Only if the current working directory is a git repository, cross-check the handoff doc's claims against actual
state — cheaply, no deep audit:

- **Current branch** matches what the doc assumes.
- **Uncommitted / unstaged changes** exist or not, as the doc implies.
- **Last test result**, if the doc cites one and it's quick to confirm.
- **Referenced paths** (files, dirs the doc points at) actually exist.

Do not silently paper over mismatches. Any discrepancy becomes an explicit **⚠️ Reality check** note inside the
emitted prompt, so the next session starts from truth rather than a stale assumption. If it's not a git repo, skip
this step.

## Step 3 — Emit the hybrid handoff prompt

Output one fenced code block the user copies verbatim into a new session. Write the prompt in **English**. Structure:

1. **Pointer.** Instruct the new agent to first read the handoff document at `<absolute path>` for full detail.
2. **Distilled orientation.** One short paragraph: what the project/task is and where it currently stands. Do not
   re-dump the whole doc — this is the essential frame so the agent has direction even if the file read fails.
3. **Next action.** The single concrete next step to take.
4. **Acceptance criteria.** How the next session knows that step is done (a test, a check, an observable outcome).
5. **⚠️ Reality check** (only if Step 2 found discrepancies): each mismatch, stated plainly.
6. **Suggested skills.** Skills the new session should invoke. Always include `using-superpowers` (skill-first
   discipline). If `task_plan.md` / `progress.md` / `findings.md` exist in the working directory, suggest
   `planning-with-files` for session recovery. Add others the context clearly calls for.

If the user passed an argument, treat it as what the next session will focus on and bias the orientation, next
action, and suggested skills toward it.

## Constraints

- **Reference, don't duplicate.** Point at the handoff doc, specs, plans, issues, commits, and diffs by path/URL —
  don't paste their contents into the prompt.
- **Redact secrets.** Strip any API keys, passwords, tokens, or PII — the prompt is a plain string the user pastes
  around.
- **Stay in lane.** Don't write or edit the handoff document, and don't launch a background agent.
