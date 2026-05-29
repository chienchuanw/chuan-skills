# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a personal plugin marketplace of Claude Code skills (slash commands), hosted as a GitHub repository.

## Repository Structure

```text
.claude-plugin/
└── marketplace.json      # Marketplace manifest (plugin registry)
plugins/
└── commit-msg/           # One directory per plugin
    └── skills/
        └── commit-msg/
            └── SKILL.md  # Skill definition
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
| readme         | local    | Write a new README.md or improve an existing one for any repository                |
| skill-creator  | external | Create, test, evaluate, and iteratively improve Claude Code skills                 |
| branch-report  | local    | Generates a branch comparison report with simple explanations and senior dev review |
| gh             | local    | GitHub CLI workflow skills (gh-issue, gh-dev, gh-pr, gh-comment, gh-archive, gh-fix) for issues, branches, PRs, comments, review-feedback handling, and session archival |
| dev            | local    | Development workflow bundle: feature (end-to-end orchestrator: issue → branch → design → strict TDD → PR → review-fix → archive, with approval checkpoints) |
| health-audit   | local    | Manually-triggered five-dimension codebase health audit producing a ranked report, filed issues, and approved auto-fix PRs |
| skill-optimize | local    | Tools for improving skills: gotcha-capture for documenting pitfalls, skill-benchmark for scoring skill quality |
| graphify       | external | Converts code, docs, PDFs, and images into queryable knowledge graphs with visualization and export            |
| mempalace      | external | Mine projects and conversations into a searchable memory palace with semantic search                            |
| daily          | local    | Personal bundle: gmail-helper (inbox triage), daily-planner (morning plan), daily-reviewer (evening retrospective) |
| portfolio      | local    | Personal bundle: portfolio-update (ingest broker screenshots) + portfolio-review (read-only thesis review)        |
| mattpocock-skills | external | Reference: Matt Pocock's engineering skills (diagnose, grill-me, handoff, to-prd, improve-codebase-architecture) |
| find-skills    | external | Reference: discover and install agent skills (Vercel Labs)                                                       |

A plugin can bundle multiple related skills under `plugins/<plugin>/skills/<skill>/` (e.g. `gh`, `skill-optimize`, `daily`, `portfolio`, `dev`). Single-skill plugins use `plugins/<name>/skills/<name>/`. External plugins reference an upstream repo in `marketplace.json` (e.g., [anthropics/skills](https://github.com/anthropics/skills)).

> Note: the `daily` and `portfolio` plugins are personal-workflow skill bundles hardcoded to a specific Obsidian vault, Gmail accounts, and portfolio schema. They are not drop-in reusable yet — genericize (placeholder account names, configurable paths) before sharing.

## Installing from this marketplace

```bash
# Add as a marketplace (one-time)
/plugin marketplace add chienchuanw/chuan-skills

# Install a plugin
/plugin install commit-msg@chuan-skills
/plugin install skill-creator@chuan-skills
```

## Adding a new skill

Use the `/skill-creator` skill, then copy the resulting directory into `plugins/<name>/skills/<name>/` (omit the `evals/` subfolder). Register it in `.claude-plugin/marketplace.json`.
