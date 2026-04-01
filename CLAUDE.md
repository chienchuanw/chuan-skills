# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a personal plugin marketplace of Claude Code skills (slash commands), hosted as a GitHub repository.

## Repository Structure

```text
.claude-plugin/
└── marketplace.json      # Marketplace manifest (plugin registry)
skills/
└── commit-msg/
    └── SKILL.md          # Local skill
```

### Skill format

Each skill directory contains a `SKILL.md` with YAML frontmatter and a prompt body:

```markdown
---
name: skill-name
description: When and why to trigger this skill
---

Instructions that Claude follows when the skill is invoked...
```

Skills may optionally include subdirectories for scripts, references, or assets.

## Plugins in this marketplace

| Plugin        | Source   | Description                                                                 |
|---------------|----------|-----------------------------------------------------------------------------|
| commit-msg     | local    | Suggests 3 commit message options based on git diff and project conventions        |
| skill-creator  | external | Create, test, evaluate, and iteratively improve Claude Code skills                 |
| branch-report  | local    | Generates a branch comparison report with simple explanations and senior dev review |

Local plugins have their skills under `skills/`. External plugins reference an upstream repo in `marketplace.json` (e.g., [anthropics/skills](https://github.com/anthropics/skills)).

## Installing from this marketplace

```bash
# Add as a marketplace (one-time)
/plugin marketplace add chienchuanw/chuan-skills

# Install a plugin
/plugin install commit-msg@chuan-skills
/plugin install skill-creator@chuan-skills
```

## Adding a new skill

Use the `/skill-creator` skill, then copy the resulting directory into `skills/` (omit the `evals/` subfolder). Register it in `.claude-plugin/marketplace.json`.
