---
name: pre-push-test
description: >
  Use when the user wants to prevent broken code from being pushed, block git push when tests fail,
  run tests before push, set up push protection, or add a safety net against pushing untested code.
  Covers any request to gate pushes on test results — whether they mention "hook", "pre-push", or
  just describe wanting to stop bad code from reaching the remote. Also handles auto-fix/auto-repair
  of test failures before push. Trigger for: "block push if tests fail", "run tests before pushing",
  "protect branch from broken pushes", "stop pushing untested code", "catch failures before they
  reach remote", or any test-gated push workflow regardless of language (npm, pnpm, cargo, go, pytest, etc).
---

# pre-push-test

Set up a git `pre-push` hook that blocks pushes when tests fail and uses Claude to auto-fix failures.

The hook script template lives at `scripts/pre-push.sh` in this skill's directory. The installation process copies it, substitutes the detected test command, and makes it executable.

## Step 1: Verify prerequisites

Confirm you're inside a git repository:

```bash
git rev-parse --is-inside-work-tree
```

If not, tell the user and stop.

Check that the `claude` CLI is available (the hook calls it to fix test failures):

```bash
command -v claude
```

If `claude` is not found, tell the user they need Claude Code installed (`npm install -g @anthropic-ai/claude-code`) for the auto-fix feature to work. Offer to install a simpler version of the hook that just blocks the push without auto-fixing.

## Step 2: Detect the test command

Figure out how this project runs its tests. Check these in order — use the **first** match:

| Signal | Test command |
|--------|-------------|
| `package.json` with a `"test"` script (not the default `echo "Error: no test specified"`) | See package manager detection below |
| `Makefile` or `GNUmakefile` with a `test` target | `make test` |
| `Cargo.toml` exists | `cargo test` |
| `go.mod` exists | `go test ./...` |
| `pyproject.toml` or `setup.py` or `setup.cfg` exists, and `pytest` is importable or listed in dependencies | `pytest` |
| `pyproject.toml` or `setup.py` exists (but no pytest) | `python -m unittest discover` |
| `mix.exs` exists | `mix test` |
| `build.gradle` or `build.gradle.kts` exists | `./gradlew test` |
| `pom.xml` exists | `mvn test` |
| `Gemfile` exists with `rspec` | `bundle exec rspec` |
| `Rakefile` with a `test` task | `rake test` |

### Package manager detection (Node.js projects)

When `package.json` has a valid test script, pick the right package manager by checking for lock files:

| Lock file | Test command |
|-----------|-------------|
| `pnpm-lock.yaml` | `pnpm test` |
| `yarn.lock` | `yarn test` |
| `bun.lockb` or `bun.lock` | `bun test` |
| `package-lock.json` (or none of the above) | `npm test` |

### Fallback detection

If none of the above match, look for clues in `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, or `Makefile` for how to run tests. If you still can't determine it, ask the user what command runs their tests.

**Show the user what you detected** before proceeding: "I detected `pnpm test` as your test command. Does that look right?" Wait for confirmation.

## Step 3: Check for an existing pre-push hook

```bash
ls -la .git/hooks/pre-push 2>/dev/null
```

If a `pre-push` hook already exists:
- Read its contents and show the user a summary
- Ask whether to **replace** it, **wrap** it (run the existing hook first, then tests), or **abort**
- If wrapping, back up the original to `.git/hooks/pre-push.backup`

## Step 4: Install the hook

Read the hook template from `scripts/pre-push.sh` (relative to this skill's directory). Copy it to `.git/hooks/pre-push`, replacing `{{TEST_CMD}}` with the detected test command. Then make it executable:

```bash
# Copy template and substitute the test command
SKILL_DIR="<path to this skill's directory>"
sed "s|{{TEST_CMD}}|<detected test command>|g" "$SKILL_DIR/scripts/pre-push.sh" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

## Step 5: Verify the installation

Run a quick sanity check:

```bash
# Confirm the hook is in place and executable
test -x .git/hooks/pre-push && echo "Hook installed successfully" || echo "ERROR: Hook not executable"
```

## Step 6: Confirm to the user

Summarize what was installed:

- **Hook location**: `.git/hooks/pre-push`
- **Test command**: the detected command
- **Behavior**: runs tests before every `git push`. If tests fail, Claude attempts to fix the code and retries up to 3 times. If all attempts fail, the push is blocked.
- **To skip** (emergency): `git push --no-verify`
- **To remove**: `rm .git/hooks/pre-push`

## Important notes

- The hook uses `--no-verify` on its own fix commits to avoid infinite hook recursion.
- The `--allowedTools` flag on the `claude` invocation limits what Claude can do during auto-fix — it can read, search, and edit files, and run commands, but nothing else.
- The hook captures test output and passes it to Claude so it has full context about what broke.
- If the user's project uses a monorepo with multiple test suites, ask which one(s) to run and adjust the test command accordingly (e.g., `pnpm test --filter=packages/core`).
