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
| feature        | local    | End-to-end feature delivery orchestrator: issue → branch → design → strict TDD → PR → review-fix → archive, with approval checkpoints |
| health-audit   | local    | Manually-triggered five-dimension codebase health audit producing a ranked report, filed issues, and approved auto-fix PRs |
| skill-optimize | local    | Tools for improving skills: gotcha-capture for documenting pitfalls, skill-benchmark for scoring skill quality |
| graphify       | external | Converts code, docs, PDFs, and images into queryable knowledge graphs with visualization and export            |
| mempalace      | external | Mine projects and conversations into a searchable memory palace with semantic search                            |
| daily-planner  | local    | Personal: plan the day end-to-end (Gmail triage, calendar, Eisenhower matrix) into an Obsidian daily note        |
| daily-reviewer | local    | Personal: evening retrospective that scores the day's plan and updates Obsidian objective tracking              |
| gmail-helper   | local    | Personal: multi-account Gmail triage/labeling secretary that summarizes into an Obsidian journal                |
| portfolio-review | local  | Personal: read-only investing thesis review over an Obsidian portfolio (drift, anchoring, stale theses)         |
| portfolio-update | local  | Personal: ingest broker/wallet screenshots and update the Obsidian portfolio tracker                            |
| mattpocock-skills | external | Reference: Matt Pocock's engineering skills (diagnose, grill-me, handoff, to-prd, improve-codebase-architecture) |
| find-skills    | external | Reference: discover and install agent skills (Vercel Labs)                                                       |

Local plugins live under `plugins/<name>/skills/<name>/`. External plugins reference an upstream repo in `marketplace.json` (e.g., [anthropics/skills](https://github.com/anthropics/skills)).

> Note: the `daily-planner`, `daily-reviewer`, `gmail-helper`, `portfolio-review`, and `portfolio-update` plugins are personal-workflow skills hardcoded to a specific Obsidian vault, Gmail accounts, and portfolio schema. They are not drop-in reusable yet — genericize (placeholder account names, configurable paths) before sharing.

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
