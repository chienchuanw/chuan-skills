#!/usr/bin/env bash
# generate_tree.sh — Print a directory tree for README documentation.
#
# Usage:
#   bash generate_tree.sh [root_dir] [max_depth]
#
# Defaults:
#   root_dir  = . (current directory)
#   max_depth = 3
#
# Respects .gitignore via git ls-files when inside a git repo.
# Falls back to `find` when git is unavailable or the directory is not a repo.

set -euo pipefail

ROOT="${1:-.}"
MAX_DEPTH="${2:-3}"

# Resolve to absolute then back to relative for clean output
ROOT="$(cd "$ROOT" && pwd)"

# ---------- helpers ----------

indent() {
  local depth=$1
  local is_last=$2
  local prefix=""
  for ((i = 1; i < depth; i++)); do
    prefix+="    "
  done
  if [ "$is_last" -eq 1 ]; then
    prefix+="└── "
  else
    prefix+="├── "
  fi
  echo -n "$prefix"
}

# ---------- collect paths ----------

collect_paths() {
  if git -C "$ROOT" rev-parse --is-inside-work-tree &>/dev/null; then
    # Use git ls-files to respect .gitignore; include untracked non-ignored files
    {
      git -C "$ROOT" ls-files --cached --others --exclude-standard
    } | sort -u
  else
    # Fallback: find, excluding hidden dirs and common noise
    (cd "$ROOT" && find . -maxdepth "$MAX_DEPTH" \
      -not -path '*/\.*' \
      -not -path '*/node_modules/*' \
      -not -path '*/__pycache__/*' \
      -not -path '*/venv/*' \
      -not -path '*/.venv/*' \
      -not -name '*.pyc' \
      | sed 's|^\./||' | sort)
  fi
}

# ---------- build tree ----------

print_tree() {
  local paths=()
  while IFS= read -r line; do
    # Filter by max depth
    local slashes="${line//[^\/]/}"
    local depth=$(( ${#slashes} + 1 ))
    if [ "$depth" -le "$MAX_DEPTH" ]; then
      paths+=("$line")
    fi
  done < <(collect_paths)

  # Print root
  echo "$(basename "$ROOT")/"

  # Group by directory and print
  local total=${#paths[@]}
  local i=0

  # Collect unique top-level entries and recurse
  print_level "" 1 "${paths[@]}"
}

print_level() {
  local prefix="$1"
  local depth="$2"
  shift 2
  local all_paths=("$@")

  # Get entries at this level
  local entries=()
  local seen=()
  for p in "${all_paths[@]}"; do
    # Strip prefix
    local rel="$p"
    if [ -n "$prefix" ]; then
      case "$p" in
        "$prefix"/*) rel="${p#"$prefix"/}" ;;
        *) continue ;;
      esac
    fi
    # Top-level name at this depth
    local name="${rel%%/*}"
    # Deduplicate
    local found=0
    for s in "${seen[@]+"${seen[@]}"}"; do
      if [ "$s" = "$name" ]; then found=1; break; fi
    done
    if [ "$found" -eq 0 ]; then
      seen+=("$name")
      # Check if directory (has children)
      local is_dir=0
      if [ "$rel" != "$name" ]; then
        is_dir=1
      elif [ -d "$ROOT/${prefix:+$prefix/}$name" ]; then
        is_dir=1
      fi
      entries+=("$name|$is_dir")
    fi
  done

  local count=${#entries[@]}
  local idx=0
  for entry in "${entries[@]}"; do
    idx=$((idx + 1))
    local name="${entry%|*}"
    local is_dir="${entry#*|}"
    local is_last=0
    if [ "$idx" -eq "$count" ]; then is_last=1; fi

    # Print indentation
    local line_prefix=""
    for ((d = 1; d < depth; d++)); do
      line_prefix+="    "
    done
    if [ "$is_last" -eq 1 ]; then
      line_prefix+="└── "
    else
      line_prefix+="├── "
    fi

    if [ "$is_dir" -eq 1 ]; then
      echo "${line_prefix}${name}/"
      if [ "$depth" -lt "$MAX_DEPTH" ]; then
        local child_prefix="${prefix:+$prefix/}$name"
        print_level "$child_prefix" $((depth + 1)) "${all_paths[@]}"
      fi
    else
      echo "${line_prefix}${name}"
    fi
  done
}

print_tree
