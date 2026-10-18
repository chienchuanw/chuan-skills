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
| dev            | local    | feature, health-audit, apply-coding-rules, handoff-prompt, model-advisor, auto-integrate, ui-visual-gate | Development lifecycle: feature (issue → branch → design → strict TDD → PR → review-fix → archive orchestrator), health-audit (five-dimension codebase health audit → ranked report, filed issues, approved auto-fix PRs), apply-coding-rules (stamp a managed coding-discipline rules block into a project's CLAUDE.md), handoff-prompt (companion to /handoff — emits a copy-paste prompt that bootstraps a fresh session to resume the work), model-advisor (canonical model/effort rubric — recommends a Claude model + effort level for a task; reused by handoff-prompt), auto-integrate (autonomous review→self-fix→green-light→rebase-merge-to-dev loop with hard guardrails + a gh branch-protection script; never touches main), and ui-visual-gate (visual-first gate for UI projects — aesthetic sign-off before coding + a visual-comparison requirement on UI merges; reused by auto-integrate's green-light, defers Figma sync to the figma skills) |
| git            | local    | commit-msg, branch-report, pre-push-test, gh-issue, gh-dev, gh-pr, gh-comment, gh-fix, gh-archive | Git & GitHub workflow: commit messages, branch-comparison reports, a test-before-push hook, plus the gh suite for issues, branches, PRs, comments, review-feedback, and session archival |
| docs           | local    | readme, seo-meta | Documentation & content: write/improve a README, and generate SEO frontmatter for markdown articles |
| skill-optimize | local    | gotcha-capture, skill-benchmark | Skill-authoring meta-tools: document pitfalls into a skill, and score/improve skill quality |
| gma2           | local    | connect, presets, setlist, cuelist, design, bpm | grandMA2 lighting console (drives the gma2 MCP over Telnet): connect (register the MCP + verify the desk), presets (Gobo/Color/Beam/Focus palettes resolved per fixture type from XML), setlist (per-song macro/sequence/page/executor + artist-coloured master cuelist from a rundown), cuelist (import a song's section CSV as labelled empty cues), design (professional concert LD — design each song's looks from audio energy, section map and MVR geometry, then program them into the cues), bpm (detect tempos and write them into the song macros) |
| skill-creator  | external | — | Create, test, evaluate, and iteratively improve Claude Code skills |
| superpowers    | external | — | Advanced skills for brainstorming, planning, debugging, TDD, code review, parallel agents |
| graphify       | external | — | Converts code, docs, PDFs, and images into queryable knowledge graphs |
| mempalace      | external | — | Mine projects and conversations into a searchable memory palace |
| mattpocock-skills | external | — | Reference: Matt Pocock's engineering skills (diagnose, grill-me, handoff, to-prd, …) |
| find-skills    | external | — | Reference: discover and install agent skills (Vercel Labs) |
| heptabase      | external | — | Heptabase's official CLI skills: manage notes, journals, tags, cards, files, whiteboards, goals, courses, lessons via the Heptabase CLI |

> The marketplace also registers a few other external references (`understand-anything`, `planning-with-files`, `impeccable`, `openspec`) — see `marketplace.json` for the full list.

Every plugin bundles its skills under `plugins/<plugin>/skills/<skill>/`. External plugins reference an upstream repo in `marketplace.json` (e.g., [anthropics/skills](https://github.com/anthropics/skills)).

> Vault-bound personal skills (`daily-*`, `gmail-helper`, `end-of-day`, `read-article`, `watch-video`, `learning-coach`, `portfolio-*`, `spend-audit`, `nutritionist`) moved on 2026-10-18 to the Mind vault repo (`chienchuanw/Mind`, `.claude/skills/`), next to the data they read and write. Only vault-independent skills live here.

## Skills map vs Anthropic's official Agent Skills

Anthropic open-sourced 17 official Agent Skills ([`anthropics/skills`](https://github.com/anthropics/skills)), which now overlap parts of this marketplace. Treat the official set as a competitive map: keep our moat, borrow their patterns where useful, and **don't duplicate the commodity tier**. New skills should avoid the commodity column below.

| Tier | Skills here | Stance |
|------|-------------|--------|
| **Moat** — no official counterpart, keep investing | `gma2` (bpm, connect, cuelist, design, presets, setlist) | These solve personal-workflow / domain problems Anthropic doesn't touch. Keep building here. |
| **Improvable** — borrow official patterns | `dev/health-audit` (← official `webapp-testing`), `dev/*` (align with `claude-api` & `mcp-builder` conventions), `skill-optimize` (← official `skill-creator` scaffolding) | Adopt the official patterns to raise quality without rebuilding from scratch. Tracked as follow-ups: #40 (webapp-testing → health-audit), #41 (skill-creator scaffolding → skill-optimize). |
| **Commodity** — do NOT duplicate | Document generation (pdf / docx / pptx / xlsx) | Anthropic covers this well. Do not build skills that re-implement document generation; depend on the official skills instead. |

Keep `SKILL.md` `description:` fields **specific and non-overlapping** so triggering stays collision-free as the catalog grows (progressive disclosure). When two skills share trigger words (e.g. "audit", "review", "PR"), add a one-line disambiguation pointer to the other skill rather than letting descriptions drift toward near-duplicates.

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

- **Fits an existing domain** (`dev`, `git`, `docs`, `skill-optimize`, `gma2`) → copy it to `plugins/<bundle>/skills/<skill>/`. No `marketplace.json` change needed — the bundle already points at `plugins/<bundle>`.
- **New domain** → create `plugins/<bundle>/skills/<skill>/` and register the bundle in `.claude-plugin/marketplace.json`.

Omit the `evals/` subfolder when copying (it's gitignored anyway).
