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
# Staged changes only — this is the sole source for generating commit messages
git diff --cached

# Recent history — your primary source for convention patterns
git log --oneline -20

# Any explicit commit conventions documented
cat CLAUDE.md 2>/dev/null || true
cat .github/CONTRIBUTING.md 2>/dev/null || true
cat CONTRIBUTING.md 2>/dev/null || true
```

If there are no staged changes (`git diff --cached` is empty), tell the user there is nothing staged to commit and stop. Do not consider unstaged changes at any point.

## Step 2: Understand the conventions

Read the git log carefully. Look for:

- **Prefix style**: Does the project use conventional commits (`feat:`, `fix:`, `chore:`), a ticket prefix (`PROJ-123:`), or plain prose?
- **Scope usage**: Are scopes like `(auth)` or `(layout)` common, or absent?
- **Tense**: Imperative ("add feature") vs past tense ("added feature")?
- **Length norms**: Short one-liners, or multi-line with body?
- **Capitalization**: Sentence case, all lowercase, etc.?

If a CONTRIBUTING or CLAUDE.md file explicitly defines conventions, those take priority over what you infer from history.

## Step 3: Generate 3 commit message options

Base all suggestions **only on the staged diff** (`git diff --cached`). Ignore any unstaged changes entirely.

Craft three options that genuinely differ from each other — not minor word swaps. Useful axes of variation:

- **Scope of description**: broad summary vs. specific technical detail
- **Granularity**: one-liner vs. multi-line with a body
- **Focus**: what changed (the "what") vs. why it changed (the "why") vs. impact on the user

All three must follow the project's conventions. If the project uses conventional commits, every option must use the correct type prefix. If scopes are common, use them when appropriate. If the project always uses imperative mood, do that.

## Step 4: Present options and prompt for selection

Format the three options as a clear numbered list. After the options, you may add one brief line of context if it would be genuinely useful — for example, explaining why you chose a particular type prefix if it was a judgment call. Keep it short. Don't explain the obvious.

Then immediately use the `AskUserQuestion` tool to ask:

> Which would you like to use? Select an option — or type your own commit message.

Do not wait for the user to respond on their own. The `AskUserQuestion` tool call is required after presenting the options every time.

## Step 5: Commit with the chosen message

Based on the user's reply:

- If they select an **option**, use the corresponding message exactly as shown.
- If they type a **custom message**, use that exactly as typed.

Run:

```bash
git commit -m "<chosen message>"
```

Use the message text verbatim — no additions, no signature, no "Co-Authored-By" line, no attribution of any kind. The commit message must be exactly what was presented or typed by the user, nothing more.

## Hard rules

- **Never run `git add`** or any command that modifies the staging area.
- **Never append any signature**, attribution, or "Co-Authored-By" line to the commit message.
- The commit message must be **exactly** the text from the selected option or the user's own input — no modifications.
- Don't add boilerplate like "I hope these help!" or "Let me know if you'd like changes." The suggestions speak for themselves.
