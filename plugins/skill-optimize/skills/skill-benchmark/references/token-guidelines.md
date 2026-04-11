# Token Guidelines for Claude Code Skills

Official Anthropic guidance on skill sizing and token management, compiled from:
- [Extend Claude with skills](https://code.claude.com/docs/en/skills)
- [Equipping agents for the real world with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)

## Token Budgets

### Description budget
- All skill descriptions share a budget of **1% of the context window** (fallback: 8,000 characters)
- Each individual description is **capped at 250 characters** in the skill listing
- Front-load the key use case — anything past 250 chars may be truncated
- If you have many skills installed, descriptions compete for this shared budget
- Run `/context` to check if any skills are being excluded due to budget limits
- Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable if needed

### SKILL.md body budget
- Recommended: **under 500 lines**
- Loaded into context only when invoked — stays for the rest of the session
- After auto-compaction, only the **first 5,000 tokens** of each skill are re-attached
- Re-attached skills share a **combined 25,000 token budget** (most-recently-invoked fills first)
- Older skills may be dropped entirely after compaction if many skills are invoked

### Bundled resources
- Reference files (`references/`, `templates/`, etc.): loaded on-demand by Claude
- Scripts (`scripts/`): **execute without loading into context** — zero token cost
- Large reference files (>300 lines): include a table of contents so Claude can navigate

## Progressive Disclosure (3 levels)

| Level | What loads | When | Token cost |
|-------|-----------|------|------------|
| Metadata | name + description (~250 chars) | Always in context | Minimal |
| SKILL.md body | Full instructions (<500 lines) | When skill is invoked | Medium |
| Bundled files | References, templates, agents | When Claude decides to read them | On-demand |
| Scripts | Never loaded, only executed | When Claude runs them | Zero |

## Optimization Strategies

### Description optimization
- Keep under 250 characters for full visibility
- Front-load the most important trigger phrase
- Include negative boundaries ("Do NOT use for X") to prevent false triggers
- Be "pushy" — Claude tends to undertrigger, so list specific scenarios

### Body optimization
- Move detailed reference material to separate files
- If contexts are mutually exclusive (e.g., different frameworks), split into separate reference files
- Use scripts for deterministic/repetitive tasks instead of inline instructions
- After 500 lines, add hierarchy with clear pointers to reference files

### Post-compaction survival
- The first 5,000 tokens of your skill are what survive compaction
- Put the most critical instructions at the top of SKILL.md
- Standing instructions (things that should apply throughout a task) should be early in the file
- If your skill is frequently invoked alongside many others, it may be dropped — keep it lean

## Measuring Token Efficiency

Key metrics to assess a skill's token footprint:

1. **Description length** — characters used vs 250-char display cap
2. **Body size** — lines and estimated tokens of SKILL.md
3. **Compaction survival** — how much of the skill fits in the 5,000-token re-attachment window
4. **Progressive disclosure ratio** — how much content is in the body vs offloaded to reference files
5. **Script vs instruction ratio** — deterministic work in scripts (free) vs instructions (costs tokens)
6. **Per-invocation cost** — total tokens loaded when the skill triggers (body + any auto-read references)
