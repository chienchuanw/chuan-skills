---
name: gotcha-capture
description: >
  Use when the user encountered a problem, bug, edge case, or frustration with an existing skill and
  wants to save that knowledge into the skill's file. Trigger phrases include "add a gotcha", "document
  this pitfall", "capture lessons learned", "record edge cases", "pull out what went wrong", but also
  trigger when the user simply describes something that went wrong or was painful with a named skill
  (like readme, commit-msg, seo-meta, branch-report, gh-pr) and asks to update it, save it, or make
  sure it doesn't happen again. This skill mines conversation history for failure knowledge and writes
  it into the skill's Gotchas section. Do NOT use for creating new skills, adding features to skills,
  or changing how skills behave — only for documenting what went wrong.
---

# gotcha-capture

Capture gotcha learnings from the current conversation and write them into a target skill's `## Gotchas` section. This skill mines the conversation for failures, workarounds, edge cases, and non-obvious constraints encountered while using a specific skill, then proposes updates to that skill's SKILL.md.

## Step 1: Resolve the target skill

The user provides a skill name as an argument (e.g., `/gotcha-capture readme`). Resolve it to a SKILL.md file path.

Use the Glob tool to search for the skill:

```
plugins/*/skills/{argument}/SKILL.md
```

**If no match is found**, list all available skills by globbing `plugins/*/skills/*/SKILL.md` and present the skill names to the user. Use `AskUserQuestion` to let them pick one.

**If the argument matches a plugin name containing multiple skills** (e.g., `gh` contains `gh-issue`, `gh-dev`, `gh-pr`), list all skills inside that plugin and ask the user to specify which one.

**If the argument is a file path**, use it directly after confirming the file exists.

Store the resolved path as `TARGET_SKILL_PATH`.

## Step 2: Read the target skill

Read the full content of the target SKILL.md using the Read tool.

Parse the file to identify:
- Whether a `## Gotchas` section already exists
- If it exists, extract all existing gotcha entries
- Detect the formatting style:
  - **Bullet style**: `- **Bold title** -- Explanation text.` (used by readme, gh-pr, gh-issue)
  - **Prose style**: Paragraph-based entries under the heading

Store the existing gotchas and the detected format style for later use. If no `## Gotchas` section exists, default to bullet style.

## Step 3: Extract gotchas from conversation

Review the full conversation context for learnings related to the target skill. The conversation is already in your context window — no tools or agents needed for this step.

Look for these patterns:

**Errors and failures**
- Tool calls that returned errors or unexpected results
- Commands that failed with specific error messages
- Stack traces or exception output
- User statements like "that didn't work", "it failed", "there's an error"

**Workarounds**
- Sequences where an approach was tried, failed, and a different approach succeeded
- Explicit corrections from the user: "actually, you need to...", "the fix was..."
- Retries with different parameters, flags, or approaches

**Unexpected behaviors**
- Results that contradicted what the skill's instructions described
- Silent failures where no error occurred but the output was wrong
- Behavior differences across environments or configurations

**Non-obvious prerequisites**
- Dependencies that needed installing first
- Authentication or permissions issues that blocked progress
- Environment-specific requirements (OS, shell version, tool versions)

**Performance issues**
- Operations that timed out or were unexpectedly slow
- Resource constraints encountered

**Edge cases**
- Inputs that caused unexpected behavior (empty repos, large diffs, special characters)
- Boundary conditions or state-dependent issues (detached HEAD, dirty working tree, no remote)

For each gotcha found, draft an entry with:
- A short title (2-5 words) summarizing the issue
- A concise explanation of the problem and how to handle it (1-3 sentences)
- A code snippet if the workaround involves a specific command

**If no gotchas are found**, inform the user: "I didn't find any gotcha-worthy learnings in this conversation related to {skill-name}. If you have something specific in mind, describe it and I can help draft the entry." Then stop.

## Step 4: Merge with existing gotchas

Compare each new candidate against the existing gotcha entries:

- **New**: The topic is not covered by any existing gotcha. Mark as `[NEW]`.
- **Refine**: The topic overlaps with an existing gotcha, but the conversation revealed new detail — a better workaround, an additional sub-case, or a more precise description. Mark as `[REFINE]` and prepare a merged version incorporating both the existing text and the new information.
- **Duplicate**: The topic is already fully covered by an existing entry. Drop it silently.

If all candidates are duplicates, inform the user: "All the gotchas I found are already documented in {skill-name}'s Gotchas section. No changes needed." Then stop.

## Step 5: Present proposed changes

Show the user a clear summary. For each proposed change:

**For `[NEW]` entries:**
```
1. [NEW] **Title** -- Explanation text here.
```

**For `[REFINE]` entries (show before and after):**
```
2. [REFINE] **Title**
   Before: **Title** -- Original explanation.
   After:  **Title** -- Updated explanation with new detail.
```

After listing all proposed changes, use `AskUserQuestion` to confirm. Offer these options:
- **Approve all** — apply all changes as shown
- **Edit entries** — let the user revise specific entries before applying
- **Cancel** — discard everything

If the user asks to edit, present the revised version and confirm again before writing.

## Step 6: Write changes to SKILL.md

After user approval, apply the changes using the Edit tool:

**If a `## Gotchas` section already exists:**
- For `[NEW]` entries: append at the end of the existing Gotchas section, before the next `##` heading or end of file.
- For `[REFINE]` entries: replace the existing entry text with the merged version in its original position.

**If no `## Gotchas` section exists:**
- Insert a new `## Gotchas` section. Place it after `## Hard rules` if that section exists, otherwise at the end of the file.
- Write all entries under the new heading.

Match the formatting style detected in Step 2. If using bullet style (default), format each entry as:

```markdown
- **Title** -- Explanation text. `code snippet` if applicable.
```

After writing, confirm to the user: "Updated {TARGET_SKILL_PATH} with N new gotcha(s) and M refinement(s)."

## Hard rules

- Never write to the target SKILL.md without explicit user approval.
- Never delete existing gotcha entries. Only append new ones or refine existing ones.
- Never modify any part of the SKILL.md outside the `## Gotchas` section.
- Match the formatting style of the target skill's existing Gotchas section. If none exists, use bullet format with bold titles.
- Each gotcha must describe a real issue encountered in the conversation — never invent hypothetical gotchas.
- Keep gotcha text concise: 2-5 word title, 1-3 sentence explanation.
- When placing a new Gotchas section, insert it after `## Hard rules` if present, otherwise at the end of the file. Never insert it in the middle of instructional steps.
