# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a personal collection of Claude Code skills (slash commands) intended for upload to a GitHub repository for reuse and sharing.

## Skill Structure

Skills are stored as directories under `skills/`, each containing a `SKILL.md` file. The directory name is the skill's identifier.

```
skills/
└── skill-name/
    └── SKILL.md          # Required: frontmatter + instructions
```

Each `SKILL.md` has YAML frontmatter and a prompt body:

```markdown
---
name: skill-name
description: When and why to trigger this skill
---

Instructions that Claude follows when the skill is invoked...
```

Skills may optionally include subdirectories for scripts, references, or assets — but most skills are just a single `SKILL.md`.

## Skills in this collection

| Skill | Description |
|-------|-------------|
| [commit-msg](skills/commit-msg/SKILL.md) | Suggests 3 commit message options based on git diff and project conventions |

## Installing a skill

Copy the skill directory into `~/.claude/skills/`:

```bash
cp -r skills/commit-msg ~/.claude/skills/
```

## Adding a new skill

Use the `/skill-creator` built-in skill, then copy the resulting directory here (omit the `evals/` subfolder — that's test infrastructure, not part of the skill itself).
