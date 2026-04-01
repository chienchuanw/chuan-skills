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

| Plugin | Source | Description |
|--------|--------|-------------|
| `commit-msg` | local | Suggests 3 commit message options based on git diff and project conventions |
| `readme` | local | Write a new README.md or improve an existing one for any repository |
| `skill-creator` | external | Create, test, evaluate, and iteratively improve Claude Code skills |

Local plugins have their skill definitions under `skills/`. External plugins reference an upstream repository (e.g., [anthropics/skills](https://github.com/anthropics/skills)) in `marketplace.json`.

## Getting Started

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed and configured

### Installation

Add this repository as a marketplace (one-time setup):

```
/plugin marketplace add chienchuanw/chuan-skills
```

Then install any plugin you want:

```
/plugin install commit-msg@chuan-skills
/plugin install readme@chuan-skills
/plugin install skill-creator@chuan-skills
```

### Usage

Once installed, invoke a skill as a slash command inside Claude Code:

- `/commit-msg` -- Analyzes your staged changes and presents 3 commit message suggestions that match your project's conventions. Pick one or write your own, and it commits for you.
- `/readme` -- Explores the current repository and generates or improves a README.md with accurate, well-structured content.
- `/skill-creator` -- Walks you through creating, testing, and refining a new Claude Code skill.

## Project Structure

```text
chuan-skills/
├── .claude-plugin/
│   └── marketplace.json   # Plugin registry (lists all available plugins)
├── skills/
│   ├── commit-msg/
│   │   └── SKILL.md       # Commit message generation skill
│   └── readme/
│       └── SKILL.md       # README generation skill
├── CLAUDE.md              # Project conventions for Claude Code
└── .gitignore
```

- **`.claude-plugin/marketplace.json`** -- The marketplace manifest. Defines each plugin's name, description, source, and skill paths.
- **`skills/`** -- Contains local skill definitions. Each subdirectory is one skill.
- **`CLAUDE.md`** -- Instructions that Claude Code follows when working in this repository.

## Adding a New Skill

1. Use the `/skill-creator` skill to scaffold and iterate on your new skill.
2. Copy the resulting skill directory into `skills/` (omit the `evals/` subfolder).
3. Register the skill in `.claude-plugin/marketplace.json`.

### Skill Format

Each skill directory contains a `SKILL.md` file with YAML frontmatter and a prompt body:

```markdown
---
name: skill-name
description: When and why to trigger this skill
---

Instructions that Claude follows when the skill is invoked...
```

Skills may optionally include subdirectories for scripts, reference files, or assets.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-skill-name`)
3. Add your skill under `skills/` and register it in `marketplace.json`
4. Commit your changes
5. Push to the branch and open a Pull Request

## License

This project does not currently specify a license.
