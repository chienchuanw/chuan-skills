# chuan-skills

A personal plugin marketplace for [Claude Code](https://claude.ai/code) skills (slash commands), hosted as a GitHub repository. Install curated skills into Claude Code with a single command.

## Table of Contents

- [Overview](#overview)
- [Available Plugins](#available-plugins)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
- [Project Structure](#project-structure)
- [Adding a New Skill](#adding-a-new-skill)
  - [Skill Format](#skill-format)
- [Contributing](#contributing)
- [License](#license)

## Overview

Claude Code supports a plugin system that lets users install and invoke custom skills as slash commands. This repository serves as a **marketplace** -- a registry of skills that can be installed directly into Claude Code. It contains both locally authored skills and references to external skill repositories.

## Available Plugins

Local plugins are organized into **domain bundles** -- each plugin groups the skills for one workflow domain.

| Plugin | Source | Skills | Description |
|--------|--------|--------|-------------|
| `dev` | local | `feature`, `health-audit` | Development lifecycle: end-to-end feature delivery (issue → branch → TDD → PR → review-fix → archive) and five-dimension codebase health audits |
| `git` | local | `commit-msg`, `branch-report`, `pre-push-test`, `gh-issue`, `gh-dev`, `gh-pr`, `gh-comment`, `gh-fix`, `gh-archive` | Git & GitHub workflow: commit messages, branch reports, a test-before-push hook, plus the full `gh` suite for issues, branches, PRs, comments, and review feedback |
| `docs` | local | `readme`, `seo-meta` | Documentation & content: write/improve a README, and generate SEO frontmatter for markdown articles |
| `skill-optimize` | local | `gotcha-capture`, `skill-benchmark` | Skill-authoring meta-tools: document pitfalls into a skill, and score/improve skill quality |
| `daily` | local | `gmail-helper`, `daily-planner`, `daily-reviewer` | Personal daily workflow (Obsidian + Gmail): inbox triage, morning plan, evening retrospective |
| `portfolio` | local | `portfolio-update`, `portfolio-review` | Personal investing tracker (Obsidian): ingest broker screenshots and review thesis drift |
| `gma2` | local | `connect`, `presets`, `setlist`, `bpm` | grandMA2 lighting console (via the gma2 MCP server): connect/verify the desk, build Gobo/Color/Beam/Focus presets from fixture XML, build a per-song set-list system from a rundown, and detect audio BPM into song macros |
| `skill-creator` | external | -- | Create, test, evaluate, and iteratively improve Claude Code skills |
| `superpowers` | external | -- | Advanced skills for brainstorming, planning, debugging, TDD, code review, and parallel agents |
| `graphify` | external | -- | Converts code, docs, PDFs, and images into queryable knowledge graphs |
| `mempalace` | external | -- | Mine projects and conversations into a searchable memory palace with semantic search |
| `planning-with-files` | external | -- | Manus-style file-based planning to organize and track progress on complex tasks |

> `daily`, `portfolio`, and `gma2` are personal/hardware-specific bundles -- `daily` and `portfolio` are hardcoded to a specific Obsidian vault, Gmail accounts, and portfolio schema; `gma2` drives a specific grandMA2 console through the companion `gma2-mcp` server -- not drop-in reusable yet. A few more external references (`understand-anything`, `impeccable`, `openspec`, `mattpocock-skills`, `find-skills`) are registered in `marketplace.json`.

Local plugins keep their skill definitions under `plugins/<bundle>/skills/<skill>/`. External plugins reference an upstream repository in `marketplace.json`.

## Getting Started

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed and configured

### Installation

Add this repository as a marketplace (one-time setup):

```bash
/plugin marketplace add chienchuanw/chuan-skills
```

Then install any plugin you want:

```bash
/plugin install dev@chuan-skills
/plugin install git@chuan-skills
/plugin install docs@chuan-skills
/plugin install skill-optimize@chuan-skills
/plugin install skill-creator@chuan-skills
/plugin install graphify@chuan-skills
/plugin install mempalace@chuan-skills
```

Installing a bundle makes all of its skills available as slash commands.

### Usage

Once a bundle is installed, invoke any of its skills as a slash command inside Claude Code.

**`dev`**
- `/feature` -- End-to-end feature delivery: issue → branch → design → strict TDD → PR → review-fix → archive, with approval checkpoints.
- `/health-audit` -- Five-dimension codebase audit (security, architecture, doc drift, dead code, test gaps) producing a ranked report, filed issues, and approved auto-fix PRs.

**`git`**
- `/commit-msg` -- Analyzes your staged changes and presents 3 commit message suggestions matching your project's conventions, then commits.
- `/branch-report` -- Compares the current branch against the default branch and explains the changes in plain language, followed by a senior-developer review.
- `/pre-push-test` -- Installs a git pre-push hook that runs tests before push with automatic failure repair.
- `/gh-issue` -- Creates a structured GitHub issue using type-specific templates (bug, feat, refactor, doc, perf, security).
- `/gh-dev` -- Creates an `issues/N` branch linked to an issue, then develops with convention-following commits.
- `/gh-pr` -- Pushes the branch and creates or updates a pull request using type-specific templates.
- `/gh-comment` -- Posts formatted comments on PRs/issues, approves PRs, and merges them.
- `/gh-fix` -- Reads unresolved PR review comments, evaluates each, then fixes or pushes back with a reasoned reply.
- `/gh-archive` -- Captures end-of-session state by updating README.md and project status files.

**`docs`**
- `/readme` -- Explores the repository and generates or improves a README.md with accurate, well-structured content.
- `/seo-meta` -- Generates SEO metadata as YAML frontmatter for markdown articles.

**`skill-optimize`**
- `/gotcha-capture` -- Mines conversation history for failure knowledge and writes it into a skill's Gotchas section.
- `/skill-benchmark` -- Scores skill quality with variance analysis and produces an improvement report.

**External**
- `/skill-creator` -- Walks you through creating, testing, and refining a new Claude Code skill.

## Project Structure

```text
chuan-skills/
├── .claude-plugin/
│   └── marketplace.json        # Plugin registry (lists all available plugins)
├── plugins/                    # One directory per plugin (domain bundle)
│   ├── dev/
│   │   └── skills/
│   │       ├── feature/        # End-to-end feature delivery orchestrator
│   │       └── health-audit/   # Five-dimension codebase health audit
│   ├── git/
│   │   └── skills/
│   │       ├── commit-msg/     # Commit message suggestions
│   │       ├── branch-report/  # Branch-vs-default comparison report
│   │       ├── pre-push-test/  # Test-before-push git hook
│   │       ├── gh-issue/       # Structured issue creation (6 types)
│   │       ├── gh-dev/         # Issue-linked branch development
│   │       ├── gh-pr/          # Pull request creation with templates
│   │       ├── gh-comment/     # PR/issue commenting, approval, merge
│   │       ├── gh-fix/         # Review-feedback triage and reply
│   │       └── gh-archive/     # End-of-session documentation capture
│   ├── docs/
│   │   └── skills/
│   │       ├── readme/         # Write/improve a README
│   │       └── seo-meta/       # SEO frontmatter for markdown articles
│   ├── skill-optimize/
│   │   └── skills/
│   │       ├── gotcha-capture/ # Document pitfalls into a skill
│   │       └── skill-benchmark/# Score skill quality
│   ├── daily/                  # Personal: gmail-helper, daily-planner, daily-reviewer
│   │   └── skills/
│   ├── portfolio/              # Personal: portfolio-update, portfolio-review
│   │   └── skills/
│   └── gma2/                   # Hardware: grandMA2 console via the gma2 MCP server
│       └── skills/
│           ├── connect/        # Register the MCP + verify the console
│           ├── presets/        # Gobo/Color/Beam/Focus palettes from fixture XML
│           ├── setlist/        # Per-song macro/seq/page/exec/view + master cuelist
│           └── bpm/            # Audio BPM → song macros (librosa)
├── CLAUDE.md                   # Project conventions for Claude Code
└── README.md
```

- **`.claude-plugin/marketplace.json`** -- The marketplace manifest. Defines each plugin's name, description, source, and skill paths.
- **`plugins/`** -- Contains local skill definitions. Each plugin is a domain bundle following the `plugins/<bundle>/skills/<skill>/` convention.
- **`CLAUDE.md`** -- Instructions that Claude Code follows when working in this repository.

## Adding a New Skill

1. Use the `/skill-creator` skill to scaffold and iterate on your new skill.
2. Place the resulting skill directory inside the matching domain bundle:
   - **Fits an existing domain** (`dev`, `git`, `docs`, `skill-optimize`, `daily`, `portfolio`) -- copy it to `plugins/<bundle>/skills/<skill>/`. No `marketplace.json` change is needed.
   - **New domain** -- create `plugins/<bundle>/skills/<skill>/` and register the bundle in `.claude-plugin/marketplace.json`.
3. Omit the `evals/` subfolder when copying (it's gitignored).

### Skill Format

Each skill directory contains a `SKILL.md` file with YAML frontmatter and a prompt body:

```markdown
---
name: skill-name
description: When and why to trigger this skill
---

Instructions that Claude follows when the skill is invoked...
```

Skills may optionally include subdirectories for agents, scripts, reference files, or assets.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-skill-name`)
3. Add your skill under `plugins/<bundle>/skills/<skill>/` and register the bundle in `marketplace.json` if it's a new domain
4. Commit your changes
5. Push to the branch and open a Pull Request

## License

This project does not currently specify a license.
