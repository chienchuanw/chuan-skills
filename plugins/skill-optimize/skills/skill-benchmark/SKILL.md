---
name: skill-benchmark
description: >
  Benchmark a skill's quality by analyzing its structure, description, documentation, and live
  value-add from multiple perspectives using parallel agents. Use when the user asks to benchmark,
  evaluate, score, audit, assess, or rate a skill's quality, or wants to know if a skill is worth
  keeping vs. deprecating. Also trigger when the user asks "how good is this skill", "is this skill
  useful", "should I keep this skill", "review skill quality", or wants a thorough multi-dimensional
  analysis of a skill before deciding whether to improve or remove it. Takes a skill name as argument
  (e.g., /skill-benchmark readme). Produces a scored report with actionable improvement suggestions.
  Do NOT use for creating new skills, editing skill code, or capturing gotchas — those are different
  workflows.
---

# skill-benchmark

Benchmark a skill from multiple perspectives — structure quality, description triggering, token efficiency, documentation completeness, and real-world value-add — then produce a scored report with improvement suggestions. Three analyst agents run in parallel to keep the process fast.

For official Anthropic token budget guidelines, see `references/token-guidelines.md` in this skill's directory.

## Agents

| Agent | File | Type | Purpose |
|-------|------|------|---------|
| Structure & Documentation Analyst | `agents/structure-doc-analyst.md` | Static | SKILL.md structure, formatting, bundled resources, token efficiency |
| Description & Triggering Analyst | `agents/description-analyst.md` | Static | Description effectiveness, trigger coverage, boundaries |
| Value-Add Tester | `agents/value-add-tester.md` | Live + Analytical | Generates test prompts, compares with/without skill |

## Step 1: Resolve the target skill

The user provides a skill name as an argument (e.g., `/skill-benchmark readme`). Resolve it to a SKILL.md file path.

Use the Glob tool to search:

```
plugins/*/skills/{argument}/SKILL.md
```

**If no match**, list all available skills by globbing `plugins/*/skills/*/SKILL.md` and present the skill names. Use `AskUserQuestion` to let the user pick.

**If the argument matches a plugin with multiple skills** (e.g., `gh` contains `gh-issue`, `gh-dev`, `gh-pr`), list all skills inside that plugin and ask the user to specify.

**If the argument is a file path**, use it directly after confirming the file exists.

Store the resolved path as `TARGET_SKILL_PATH` and its parent directory as `TARGET_SKILL_DIR`.

## Step 2: Inventory the skill

Read the full content of the target SKILL.md using the Read tool. Store as `SKILL_CONTENT`.

Then inventory the skill's bundled resources by globbing each subdirectory:

```
{TARGET_SKILL_DIR}/agents/*.md
{TARGET_SKILL_DIR}/scripts/*
{TARGET_SKILL_DIR}/assets/*
{TARGET_SKILL_DIR}/references/*
{TARGET_SKILL_DIR}/templates/*
{TARGET_SKILL_DIR}/evals/evals.json
```

Compile the results into `SKILL_INVENTORY` — a structured summary like:
```
agents: scout.md, explainer.md, analyst.md, checker.md (4 files)
scripts: none
assets: template.md, template-zh-TW.md (2 files)
references: none
templates: none
evals: evals.json present (3 test cases)
```

Briefly inform the user what you found: "Benchmarking {skill-name} — found {N} agents, {N} scripts, {N} assets. Launching 3 analyst agents in parallel..."

## Step 3: Launch analyst agents in parallel

Read the three agent definition files from this skill's `agents/` directory:
- `agents/structure-doc-analyst.md`
- `agents/description-analyst.md`
- `agents/value-add-tester.md`

Spawn all three using the Agent tool **in a single message** (three Agent tool calls). Pass each agent the data it needs:

**Structure & Doc Analyst prompt:**
```
You are the Structure & Documentation Analyst. Read your instructions at:
{this-skill-path}/agents/structure-doc-analyst.md

Then analyze this skill:
- SKILL_CONTENT: {full SKILL.md text}
- SKILL_INVENTORY: {inventory summary}
- TARGET_SKILL_PATH: {path}

Follow your output format exactly.
```

**Description Analyst prompt:**
```
You are the Description & Triggering Analyst. Read your instructions at:
{this-skill-path}/agents/description-analyst.md

Then analyze this skill:
- SKILL_CONTENT: {full SKILL.md text}

Follow your output format exactly.
```

**Value-Add Tester prompt:**
```
You are the Value-Add Tester. Read your instructions at:
{this-skill-path}/agents/value-add-tester.md

Then analyze this skill:
- SKILL_CONTENT: {full SKILL.md text}
- TARGET_SKILL_PATH: {path}
- SKILL_INVENTORY: {inventory summary}

Follow your output format exactly.
```

Wait for all three agents to complete. Store their outputs as `STRUCTURE_DOC_ANALYSIS`, `DESCRIPTION_ANALYSIS`, and `VALUE_ADD_ANALYSIS`.

## Step 4: Compile scores and generate report

Extract the scores from each agent's output by parsing their `**Score: N/10**` lines:
- Structure Quality score → `STRUCTURE_SCORE`
- Documentation Completeness score → `DOCUMENTATION_SCORE`
- Token Efficiency score → `TOKEN_SCORE`
- Description Quality score → `DESCRIPTION_SCORE`
- Value-Add score → `VALUE_ADD_SCORE`
- Efficiency score → `EFFICIENCY_SCORE`

Compute the weighted overall score:

```
overall = (STRUCTURE * 2.0 + DOCUMENTATION * 1.5 + TOKEN * 1.5 + DESCRIPTION * 2.0 + VALUE_ADD * 3.0 + EFFICIENCY * 1.5) / (2.0 + 1.5 + 1.5 + 2.0 + 3.0 + 1.5)
```

Round to one decimal place.

Read the report template from this skill's `assets/template.md`. Fill all `{PLACEHOLDER}` values:
- `{SKILL_NAME}` — the target skill's name from frontmatter
- `{DATE}` — today's date
- `{SKILL_PATH}` — the resolved TARGET_SKILL_PATH
- `{RESOURCE_SUMMARY}` — the SKILL_INVENTORY summary
- `{STRUCTURE_SCORE}`, `{DOCUMENTATION_SCORE}`, `{TOKEN_SCORE}`, `{DESCRIPTION_SCORE}`, `{VALUE_ADD_SCORE}`, `{EFFICIENCY_SCORE}`, `{OVERALL_SCORE}` — the scores
- `{STRUCTURE_ANALYSIS}` — from Structure & Doc Analyst output (the Structure Quality section)
- `{DOCUMENTATION_ANALYSIS}` — from Structure & Doc Analyst output (the Documentation Completeness section)
- `{TOKEN_ANALYSIS}` — from Structure & Doc Analyst output (the Token Efficiency section)
- `{DESCRIPTION_ANALYSIS}` — from Description Analyst output
- `{VALUE_ADD_ANALYSIS}` — from Value-Add Tester output (both Value-Add and Efficiency sections)
- `{IMPROVEMENTS}` — collated from all three agents (see Step 5)
- `{RECOMMENDATION}` — your synthesis (see Step 5)

## Step 5: Write recommendation and present report

Collate all improvement suggestions from the three agents into a single prioritized list. Group by priority level:

```
### High Priority
- {suggestion from any agent}

### Medium Priority
- {suggestion}

### Low Priority
- {suggestion}
```

Write a `{RECOMMENDATION}` section — 2-4 paragraphs synthesizing the scores into an overall assessment. Address these questions:

- Is this skill worth keeping? (Reference the Value-Add score — if it's 4 or below, suggest the user consider whether the skill earns its place)
- What's the single most impactful improvement? (Reference the lowest-scoring dimension)
- Is the skill mature or does it need significant work? (Reference Structure and Documentation scores)

The recommendation should be nuanced — not a binary "keep or deprecate" but a contextualized assessment with specific next steps.

Present the completed report directly in chat. If the user asks to save it, write it to `{TARGET_SKILL_DIR}/benchmark-report.md`.

## Hard rules

- Never modify the target skill's SKILL.md or any of its resources. This skill is read-only analysis.
- Never fabricate test results. If live testing cannot be performed, say so and explain why.
- All scores must be integers from 1 to 10. Never use 0 or scores above 10.
- The overall score must be a computed weighted average, not a subjective number. Show the formula.
- Each score must have at least two sentences of written justification. Never present a bare number.
- When generating test prompts for the Value-Add Tester, base them on what the skill claims to do. Never test capabilities the skill does not claim.
- Present the report in chat by default. Only write to file if the user explicitly requests it.
- Never invent improvement suggestions that contradict the skill's stated purpose or design philosophy.
