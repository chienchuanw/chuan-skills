#!/usr/bin/env bash
#
# protect-branches.sh — apply the auto-integrate guardrails to a repo's main branch.
#
# Sets, on <owner>/<repo>'s protected branch (default: main):
#   - require a pull request before merging
#   - require status checks to pass (strict / up-to-date) for any checks you pass
#   - require linear history
#   - block force-push and branch deletion
#
# Idempotent: it PUTs the desired protection state (GitHub replaces the branch's
# protection with this payload). It never deletes a branch and never touches code.
# Re-running with the same args converges to the same state.
#
# Requires: gh (authenticated with admin rights on the repo), jq.
#
# Usage:
#   protect-branches.sh <owner>/<repo> [--branch main] [--checks "ci,test"] [--dry-run]
#
# Examples:
#   protect-branches.sh chienchuanw/chuan-skills
#   protect-branches.sh chienchuanw/chuan-skills --branch main --checks "build,test"
#   protect-branches.sh chienchuanw/chuan-skills --dry-run
#
set -euo pipefail

BRANCH="main"
CHECKS=""
DRY_RUN=0
REPO=""

die() { printf 'error: %s\n' "$1" >&2; exit 1; }

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --branch)  BRANCH="${2:?--branch needs a value}"; shift 2 ;;
    --checks)  CHECKS="${2:?--checks needs a value}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -*)        die "unknown flag: $1" ;;
    *)         [ -z "$REPO" ] && REPO="$1" || die "unexpected arg: $1"; shift ;;
  esac
done

[ -n "$REPO" ] || usage 1
command -v gh >/dev/null 2>&1 || die "gh CLI not found"
command -v jq >/dev/null 2>&1 || die "jq not found"
case "$REPO" in */*) : ;; *) die "repo must be <owner>/<repo>, got: $REPO" ;; esac

# Build required_status_checks. Empty --checks => enforce strict with no named
# contexts (you can bind CI contexts later); non-empty => require those contexts.
if [ -n "$CHECKS" ]; then
  CONTEXTS_JSON="$(printf '%s' "$CHECKS" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length>0))')"
else
  CONTEXTS_JSON='[]'
fi

PAYLOAD="$(jq -n --argjson contexts "$CONTEXTS_JSON" '{
  required_status_checks:      { strict: true, contexts: $contexts },
  enforce_admins:              true,
  required_pull_request_reviews: { required_approving_review_count: 0 },
  required_linear_history:     true,
  allow_force_pushes:          false,
  allow_deletions:             false,
  restrictions:                null
}')"

API_PATH="repos/${REPO}/branches/${BRANCH}/protection"

printf 'Target: %s (branch: %s)\n' "$REPO" "$BRANCH"
printf 'Desired protection:\n%s\n' "$PAYLOAD"

if [ "$DRY_RUN" -eq 1 ]; then
  printf '\n[dry-run] would PUT the above to %s — no changes made.\n' "$API_PATH"
  exit 0
fi

# Apply. The protection PUT replaces protection state (idempotent for fixed args).
printf '\nApplying...\n'
gh api -X PUT "$API_PATH" \
  -H "Accept: application/vnd.github+json" \
  --input - <<<"$PAYLOAD" >/dev/null

printf 'Done. Current protection:\n'
gh api "$API_PATH" -H "Accept: application/vnd.github+json" | jq '{
  required_pull_request_reviews: (.required_pull_request_reviews != null),
  required_status_checks: .required_status_checks.contexts,
  required_linear_history: .required_linear_history.enabled,
  allow_force_pushes: .allow_force_pushes.enabled,
  allow_deletions: .allow_deletions.enabled,
  enforce_admins: .enforce_admins.enabled
}'
