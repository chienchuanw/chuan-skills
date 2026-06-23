# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a personal plugin marketplace of Claude Code skills (slash commands), hosted as a GitHub repository.

## Repository Structure

```text
.claude-plugin/
└── marketplace.json      # Marketplace manifest (plugin registry)
plugins/
└── git/                  # One directory per plugin (a domain bundle)
    └── skills/
        ├── commit-msg/
        │   └── SKILL.md  # Skill definition
        └── branch-report/
            └── SKILL.md
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

Local plugins are organized into **domain bundles** — each plugin groups the skills for one workflow domain.

| Plugin         | Source   | Skills | Description                                                                 |
|----------------|----------|--------|-----------------------------------------------------------------------------|
| dev            | local    | feature, health-audit | Development lifecycle: feature (issue → branch → design → strict TDD → PR → review-fix → archive orchestrator) and health-audit (five-dimension codebase health audit → ranked report, filed issues, approved auto-fix PRs) |
| git            | local    | commit-msg, branch-report, pre-push-test, gh-issue, gh-dev, gh-pr, gh-comment, gh-fix, gh-archive | Git & GitHub workflow: commit messages, branch-comparison reports, a test-before-push hook, plus the gh suite for issues, branches, PRs, comments, review-feedback, and session archival |
| docs           | local    | readme, seo-meta | Documentation & content: write/improve a README, and generate SEO frontmatter for markdown articles |
| skill-optimize | local    | gotcha-capture, skill-benchmark | Skill-authoring meta-tools: document pitfalls into a skill, and score/improve skill quality |
| daily          | local    | gmail-helper, daily-planner, daily-reviewer | Personal: inbox triage, morning plan, evening retrospective |
| portfolio      | local    | portfolio-update, portfolio-review | Personal: ingest broker screenshots / log trades, and read-only thesis review |
| knowledge      | local    | read-article | Personal: digest pasted article URLs (summarize, fact-check, conclude, map to Objectives/projects) and file an enriched reference note |
| skill-creator  | external | — | Create, test, evaluate, and iteratively improve Claude Code skills |
| superpowers    | external | — | Advanced skills for brainstorming, planning, debugging, TDD, code review, parallel agents |
| graphify       | external | — | Converts code, docs, PDFs, and images into queryable knowledge graphs |
| mempalace      | external | — | Mine projects and conversations into a searchable memory palace |
| mattpocock-skills | external | — | Reference: Matt Pocock's engineering skills (diagnose, grill-me, handoff, to-prd, …) |
| find-skills    | external | — | Reference: discover and install agent skills (Vercel Labs) |

> The marketplace also registers a few other external references (`understand-anything`, `planning-with-files`, `impeccable`, `openspec`) — see `marketplace.json` for the full list.

Every plugin bundles its skills under `plugins/<plugin>/skills/<skill>/`. External plugins reference an upstream repo in `marketplace.json` (e.g., [anthropics/skills](https://github.com/anthropics/skills)).

> Note: the `daily` and `portfolio` plugins are personal-workflow skill bundles hardcoded to a specific Obsidian vault, Gmail accounts, and portfolio schema. They are not drop-in reusable yet — genericize (placeholder account names, configurable paths) before sharing.

## Installing from this marketplace

```bash
# Add as a marketplace (one-time)
/plugin marketplace add chienchuanw/chuan-skills

# Install a plugin
/plugin install git@chuan-skills
/plugin install skill-creator@chuan-skills
```

## Adding a new skill

Use the `/skill-creator` skill, then place the resulting directory under the appropriate domain bundle:

- **Fits an existing domain** (`dev`, `git`, `docs`, `skill-optimize`, `daily`, `portfolio`) → copy it to `plugins/<bundle>/skills/<skill>/`. No `marketplace.json` change needed — the bundle already points at `plugins/<bundle>`.
- **New domain** → create `plugins/<bundle>/skills/<skill>/` and register the bundle in `.claude-plugin/marketplace.json`.

Omit the `evals/` subfolder when copying (it's gitignored anyway).
