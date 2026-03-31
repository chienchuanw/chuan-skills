---
name: commit-msg
description: >
  Generates commit message suggestions based on the current git diff and project conventions.
  Use this skill whenever the user wants commit message ideas, asks "what should I write for the commit message?",
  says "suggest a commit message", "help me write a commit message", "what commit message should I use?",
  "give me commit message options", or any similar request to summarize their changes into a commit message.
  Also trigger when the user has just made code changes and seems ready to commit.
  Always present exactly 3 options plus a 4th "write your own" option. Never run git commit.
---

# commit-msg

Generate thoughtful commit message suggestions by reading the actual changes in the repo and understanding the project's own conventions — so suggestions feel native to the codebase, not generic.

## Step 1: Gather context

Run all of these in one shot:

```bash
# What's changed (staged + unstaged)
git diff HEAD

# Staged-only (in case HEAD diff misses staged-only changes on a fresh repo)
git diff --cached

# Recent history — your primary source for convention patterns
git log --oneline -20

# Any explicit commit conventions documented
cat CLAUDE.md 2>/dev/null || true
cat .github/CONTRIBUTING.md 2>/dev/null || true
cat CONTRIBUTING.md 2>/dev/null || true
```

If there's no diff at all (clean working tree and no staged changes), tell the user and stop — there's nothing to describe.

## Step 2: Understand the conventions

Read the git log carefully. Look for:

- **Prefix style**: Does the project use conventional commits (`feat:`, `fix:`, `chore:`), a ticket prefix (`PROJ-123:`), or plain prose?
- **Scope usage**: Are scopes like `(auth)` or `(layout)` common, or absent?
- **Tense**: Imperative ("add feature") vs past tense ("added feature")?
- **Length norms**: Short one-liners, or multi-line with body?
- **Capitalization**: Sentence case, all lowercase, etc.?

If a CONTRIBUTING or CLAUDE.md file explicitly defines conventions, those take priority over what you infer from history.

## Step 3: Generate 3 commit message options

Craft three options that genuinely differ from each other — not minor word swaps. Useful axes of variation:

- **Scope of description**: broad summary vs. specific technical detail
- **Granularity**: one-liner vs. multi-line with a body
- **Focus**: what changed (the "what") vs. why it changed (the "why") vs. impact on the user

All three must follow the project's conventions. If the project uses conventional commits, every option must use the correct type prefix. If scopes are common, use them when appropriate. If the project always uses imperative mood, do that.

## Step 4: Present options

Output exactly this structure — clean, copyable, no extra commentary cluttering the options themselves:

```
Here are 3 commit message suggestions based on your changes:

**Option 1**
```
<message>
```

**Option 2**
```
<message>
```

**Option 3**
```
<message>
```

**Option 4 — Write your own**
None of these feel right? Use them as a starting point and adapt freely.
```

After the options, you may add one brief line of context if it would be genuinely useful — for example, explaining why you chose a particular type prefix if it was a judgment call. Keep it short. Don't explain the obvious.

## Hard rules

- **Never run `git commit`**, `git add`, or any command that modifies the repo state. Your job ends at presenting suggestions.
- Don't ask the user to pick an option or confirm anything — just present all four and let them take it from there.
- Don't add boilerplate like "I hope these help!" or "Let me know if you'd like changes." The suggestions speak for themselves.
