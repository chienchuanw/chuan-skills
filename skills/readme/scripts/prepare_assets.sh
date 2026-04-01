#!/usr/bin/env bash
# prepare_assets.sh — Create screenshot/GIF directory structure and output a capture checklist.
#
# Usage:
#   bash prepare_assets.sh [project_root] [assets_file]
#
# Arguments:
#   project_root  Path to the project (default: current directory)
#   assets_file   Path to a JSON file listing assets to capture (optional)
#
# If no assets_file is provided, the script creates the directory and prints
# a generic checklist. If provided, it reads the JSON and generates a
# project-specific checklist.
#
# JSON format:
# [
#   {
#     "filename": "dashboard.png",
#     "description": "Main dashboard with sample data loaded",
#     "type": "screenshot",
#     "url_or_context": "http://localhost:3000/dashboard"
#   },
#   {
#     "filename": "setup-flow.gif",
#     "description": "Walkthrough of the initial setup wizard",
#     "type": "gif",
#     "url_or_context": "http://localhost:3000/setup"
#   }
# ]

set -euo pipefail

ROOT="${1:-.}"
ASSETS_FILE="${2:-}"
ASSETS_DIR="$ROOT/assets/screenshots"

# Create directory structure
mkdir -p "$ASSETS_DIR"

echo "=========================================="
echo " Screenshot / GIF Capture Checklist"
echo "=========================================="
echo ""
echo "Directory created: $ASSETS_DIR"
echo ""

if [ -n "$ASSETS_FILE" ] && [ -f "$ASSETS_FILE" ]; then
  # Parse JSON checklist (requires python3, which is available on macOS and most Linux)
  python3 -c "
import json, sys

with open('$ASSETS_FILE') as f:
    assets = json.load(f)

screenshots = [a for a in assets if a.get('type') == 'screenshot']
gifs = [a for a in assets if a.get('type') == 'gif']

if screenshots:
    print('Screenshots to capture:')
    print('')
    for i, a in enumerate(screenshots, 1):
        print(f\"  [ ] {i}. {a['filename']}\")
        print(f\"       {a['description']}\")
        if a.get('url_or_context'):
            print(f\"       Context: {a['url_or_context']}\")
        print(f\"       Save to: $ASSETS_DIR/{a['filename']}\")
        print('')

if gifs:
    print('GIFs / demo recordings to capture:')
    print('')
    for i, a in enumerate(gifs, 1):
        print(f\"  [ ] {i}. {a['filename']}\")
        print(f\"       {a['description']}\")
        if a.get('url_or_context'):
            print(f\"       Context: {a['url_or_context']}\")
        print(f\"       Save to: $ASSETS_DIR/{a['filename']}\")
        print('')

print(f'Total: {len(screenshots)} screenshot(s), {len(gifs)} GIF(s)')
"
else
  echo "No asset list provided. Generic checklist:"
  echo ""
  echo "  [ ] 1. Capture a screenshot of the main interface or landing page"
  echo "       Save to: $ASSETS_DIR/overview.png"
  echo ""
  echo "  [ ] 2. Capture screenshots for each key feature"
  echo "       Save to: $ASSETS_DIR/<feature-name>.png"
  echo ""
  echo "  [ ] 3. Record a GIF of the primary workflow (if applicable)"
  echo "       Save to: $ASSETS_DIR/<workflow-name>.gif"
  echo ""
  echo "Tip: Once captured, reference them in README.md like this:"
  echo ""
  echo "  ![Feature name](assets/screenshots/feature-name.png)"
  echo ""
fi

echo ""
echo "=========================================="
echo " Suggested tools"
echo "=========================================="
echo ""
echo "  Screenshots (macOS):  Cmd+Shift+4 or Cmd+Shift+5"
echo "  Screenshots (Linux):  gnome-screenshot, flameshot, or scrot"
echo "  Screenshots (browser): Browser DevTools > device toolbar for consistent viewport"
echo "  GIF recording:        gifcap (https://gifcap.dev), LICEcap, or Kap (macOS)"
echo "  Terminal recording:   vhs (https://github.com/charmbracelet/vhs) or asciinema"
echo ""
