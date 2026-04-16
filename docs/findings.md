# Findings

## Architecture Decisions

- **Plugin structure**: Each local plugin follows `plugins/<name>/skills/<name>/SKILL.md` convention with optional subdirectories for templates, agents, scripts, and assets.
- **Marketplace manifest**: `.claude-plugin/marketplace.json` serves as the single registry for all plugins (local and external).
- **External plugins**: Referenced by git URL in marketplace.json, allowing installation without vendoring code.

## Recent Session Observations

- **Base branch handling**: All gh skills (gh-dev, gh-pr, gh-issue, gh-comment) were updated to detect and use the correct base branch instead of hardcoding `dev`. This prevents issues when the default branch is `main`.
- **Post-completion prompts**: Each gh skill now includes a "What's Next?" prompt guiding users to the logical next step in the workflow (e.g., gh-issue suggests gh-dev, gh-dev suggests gh-pr).
- **gh-comment output hygiene**: Signature and attribution lines are now prohibited in gh-comment output to keep comments clean.
- **Commit template injection**: gh-dev subagents use injectable commit templates rather than manual co-author warnings.

## Plugin Inventory (as of 2026-04-16)

- **7 local plugins**: commit-msg, readme, branch-report, gh (5 sub-skills), seo-meta, skill-optimize (2 sub-skills), pre-push-test
- **7 external plugins**: skill-creator, graphify, mempalace, superpowers, planning-with-files, impeccable, openspec
- **Total registered**: 14 plugins in marketplace.json
