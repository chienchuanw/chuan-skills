---
name: readme
description: >
  Write a new README.md or improve an existing one for any repository.
  Use this skill whenever the user asks to create, generate, write, update, rewrite, or improve a README,
  says "add a README", "this repo needs a README", "update the README", "clean up the README",
  "make a better README", or any similar request related to project documentation in README format.
  Also trigger when the user says "document this project" or "write docs for this repo" and no other
  documentation skill is more specific.
---

# readme

Generate or improve a README.md that is well-structured, informative, and free of decoration. The goal is a document that helps both newcomers and contributors understand what the project does, how to use it, and how it is organized -- without wasting their time.

## Hard rules

- Never use emojis anywhere in the README. Not in headings, not in lists, not in badges, nowhere.
- Never invent information. If you cannot determine something from the repo, leave a clear placeholder in braces (e.g., `{describe the deployment process}`) so the user knows to fill it in.
- Preserve any existing content that is still accurate. When updating a README, restructure and rewrite for clarity, but do not discard correct information.

## Step 1: Gather context

Explore the repository to understand what it is and how it works. Run these in parallel where possible:

```bash
# Package metadata
cat package.json 2>/dev/null || cat pyproject.toml 2>/dev/null || cat Cargo.toml 2>/dev/null || cat go.mod 2>/dev/null || cat pom.xml 2>/dev/null || cat Gemfile 2>/dev/null || true

# Existing README
cat README.md 2>/dev/null || cat readme.md 2>/dev/null || cat Readme.md 2>/dev/null || true

# Project conventions and contributing guides
cat CLAUDE.md 2>/dev/null || true
cat CONTRIBUTING.md 2>/dev/null || cat .github/CONTRIBUTING.md 2>/dev/null || true

# License
cat LICENSE 2>/dev/null || cat LICENSE.md 2>/dev/null || true

# CI/CD and config files (existence check)
ls .github/workflows/ 2>/dev/null || true
ls Makefile Dockerfile docker-compose.yml .env.example 2>/dev/null || true
```

Also generate a project structure tree using the bundled script:

```bash
bash <skill-path>/scripts/generate_tree.sh . 3
```

Replace `<skill-path>` with the actual path to this skill's directory.

Read a few key source files (entry points, main modules) to understand what the project actually does. Do not read every file -- just enough to write an accurate overview.

## Step 2: Detect language

Check the existing README and other documentation files for their written language (e.g., English, Chinese, Japanese). If documentation exists, write the README in the same language. If there is no existing documentation, default to English.

## Step 3: Decide whether to create or update

- **No README exists**: Start from scratch using the template at `<skill-path>/assets/template.md`. Read the template, then fill in each section with real content based on what you gathered in Step 1.
- **README exists**: Read it carefully. Identify what is missing, outdated, poorly structured, or unclear. Restructure it to follow the template's section order where it makes sense, but keep any project-specific sections the author added intentionally.

## Step 4: Write the README

Follow the template structure from `assets/template.md` as a guide. Here is how to handle each section:

### Project title and description

Use the actual project name. Write one or two sentences that explain what it does and why someone would use it. Be specific -- "A CLI tool that converts OpenAPI specs to TypeScript client libraries" is better than "A useful developer tool."

### Table of Contents

Include a Table of Contents with anchor links when the README has more than three sections. Omit it for very short READMEs.

### Overview

Expand on the opening description. Cover the problem the project solves, who it is for, and any important design decisions. This section should give a reader enough context to decide whether the project is relevant to them.

### Features

List each major feature with a short description. For projects with a visual interface (web apps, SaaS, desktop apps, CLI tools with rich output), include screenshots or demo GIFs to show what the feature looks like in practice.

Format image references like this:

```markdown
- **Dashboard view** -- Real-time metrics for all connected services.

  ![Dashboard view](assets/screenshots/dashboard.png)
```

If screenshots do not exist yet, add a placeholder and tell the user:

```markdown
  ![Dashboard view](assets/screenshots/dashboard.png)
  <!-- TODO: Add a screenshot of the dashboard -->
```

After writing the README, let the user know which screenshots are missing so they can capture them.

### Getting Started (Prerequisites, Installation, Usage)

Only list prerequisites that are genuinely required. Pull version requirements from the package manifest when possible (e.g., `engines` in package.json, `python_requires` in pyproject.toml).

For installation, provide copy-pasteable commands. If there are multiple installation methods (npm, Docker, building from source), list them under separate subheadings.

For usage, show the single most common command or code snippet first, then cover additional examples if the project has multiple modes of operation.

### Configuration

If the project uses environment variables, config files, or CLI flags, document them. A table works well for environment variables. If there is an `.env.example` file, use it as the source of truth.

Skip this section entirely if the project has no configuration.

### Project Structure

Use the tree output from Step 1. Trim it to show only the directories and files that matter for understanding the project's architecture. Add a brief note after the tree explaining what the key directories contain.

```text
myproject/
├── src/
│   ├── api/          # REST endpoint handlers
│   ├── models/       # Database models
│   └── utils/        # Shared helpers
├── tests/
├── Dockerfile
└── package.json
```

### Contributing

If a CONTRIBUTING.md exists, write a short sentence and link to it. Otherwise, include basic instructions: fork, branch, commit, PR. Mention how to run tests if a test command is available (e.g., `npm test`, `pytest`).

### License

State the license name and link to the LICENSE file. If no LICENSE file exists, note that the project does not specify a license.

## Step 5: Review and finalize

Before writing the file, review your draft for:

- Accuracy: Does every claim match what you saw in the code?
- Completeness: Are there sections that are still generic or placeholder-heavy? If so, can you fill them in by reading more source files?
- Brevity: Remove filler phrases like "This project aims to..." or "This section describes..." -- just state the facts.
- Formatting: Consistent heading levels, proper code fences with language tags, no trailing whitespace.
- No emojis: Double-check that no emojis have crept in.

Write the final README.md to the project root. If you replaced an existing README, briefly tell the user what changed.

## Step 6: Capture or prepare missing assets

If the README references images that do not exist yet, try to capture them automatically. If automatic capture is not possible, fall back to a manual checklist.

### 6a. Write the asset list

Create a JSON file listing every missing asset. Use a path (e.g., `/dashboard`) for the `url_or_context` field -- the capture script resolves it against the dev server URL automatically.

```json
[
  {
    "filename": "dashboard.png",
    "description": "Main dashboard with sample data loaded",
    "type": "screenshot",
    "url_or_context": "/dashboard"
  },
  {
    "filename": "setup-flow.png",
    "description": "The initial setup wizard",
    "type": "screenshot",
    "url_or_context": "/setup"
  }
]
```

Save this file to a temporary location (e.g., `/tmp/readme-assets.json`).

### 6b. Try automatic capture

For web application projects, run the capture script. It auto-detects the dev server command from project files (package.json, manage.py, pyproject.toml, etc.), starts the server, takes screenshots with Playwright, and stops the server when done.

```bash
python3 <skill-path>/scripts/capture_screenshots.py . /tmp/readme-assets.json
```

The script:
- Detects the dev server command and port from package.json scripts, Django manage.py, Flask app.py, or pyproject.toml
- Starts the dev server if it is not already running
- Waits for the server to be ready
- Captures each page as a high-resolution (2x) PNG screenshot
- Saves results to `assets/screenshots/` in the project root
- Stops the dev server when done

If Playwright is not installed, the script prints installation instructions and falls back to the manual checklist automatically.

**Prerequisite (one-time setup):**

```bash
pip install playwright && playwright install chromium
```

Tell the user about this requirement if the script reports that Playwright is missing.

### 6c. Fall back to manual checklist

If the project is not a web app, or if automatic capture fails, run the checklist script instead:

```bash
bash <skill-path>/scripts/prepare_assets.sh . /tmp/readme-assets.json
```

This creates the `assets/screenshots/` directory and prints a checklist with filenames, descriptions, and suggested capture tools.

### Skip conditions

If the README has no image placeholders, skip this step entirely.
