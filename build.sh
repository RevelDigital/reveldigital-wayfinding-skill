#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/revel-wayfinding-skill"
OUTPUT="$SCRIPT_DIR/revel-wayfinding-skill.zip"

if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
  echo "Error: SKILL.md not found in $SKILL_DIR"
  exit 1
fi

rm -f "$OUTPUT"

cd "$SCRIPT_DIR"
zip -r "$OUTPUT" revel-wayfinding-skill/ \
  -x "revel-wayfinding-skill/.DS_Store" \
  -x "revel-wayfinding-skill/**/.DS_Store"

echo ""
echo "Built: $OUTPUT"
echo ""
unzip -l "$OUTPUT"
