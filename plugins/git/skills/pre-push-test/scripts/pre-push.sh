#!/usr/bin/env bash
#
# pre-push hook: run tests before pushing; auto-fix with Claude on failure
# Installed by the pre-push-test skill
#
# Template variables (replaced during installation):
#   {{TEST_CMD}} — the project's test command

set -euo pipefail

TEST_CMD="{{TEST_CMD}}"
MAX_RETRIES=3
ATTEMPT=1

echo "==> pre-push: running tests before push..."

while [ "$ATTEMPT" -le "$MAX_RETRIES" ]; do
    TEST_OUTPUT=$(eval "$TEST_CMD" 2>&1) && {
        echo "==> Tests passed (attempt $ATTEMPT). Pushing..."
        exit 0
    }

    echo "==> Tests failed on attempt $ATTEMPT."

    if [ "$ATTEMPT" -eq "$MAX_RETRIES" ]; then
        echo "==> All $MAX_RETRIES attempts exhausted. Push blocked."
        echo ""
        echo "Last test output:"
        echo "$TEST_OUTPUT"
        exit 1
    fi

    # Use Claude to auto-fix the failures
    if command -v claude &> /dev/null; then
        echo "==> Invoking Claude to fix test failures..."
        claude -p "The following test failures occurred when running \`$TEST_CMD\`. Fix the code so the tests pass. Do NOT modify the tests unless they are clearly wrong. Here is the test output:

$TEST_OUTPUT" --allowedTools "Edit,Read,Glob,Grep,Bash" 2>&1 || {
            echo "==> Claude auto-fix failed. Push blocked."
            echo "$TEST_OUTPUT"
            exit 1
        }

        # Stage and commit the fixes
        git add -A
        git commit -m "fix: auto-fix test failures (attempt $ATTEMPT)" \
            --no-verify 2>/dev/null || true
    else
        echo "==> 'claude' CLI not found — cannot auto-fix. Push blocked."
        echo ""
        echo "Test output:"
        echo "$TEST_OUTPUT"
        exit 1
    fi

    ATTEMPT=$((ATTEMPT + 1))
done
