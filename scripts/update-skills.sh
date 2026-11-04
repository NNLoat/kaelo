#!/usr/bin/env bash
#
# Vendored-skill update helper for .claude/skills.
#
# These skills carry local edits (trimmed frontmatter, a rewritten dispatcher),
# so they are NOT auto-overwritten from upstream. Instead this script
# fetches the pinned upstream copies into a gitignored cache and shows you how your vendored copy differs, so you can apply upstream changes by
# hand and keep the local edits intact.
#
# Workflow to update a skill:
#   1. Bump its SHA below (and in .claude/skills/SKILLS.md).
#   2. Run this script.
#   3. Read the diffs it prints: upstream-at-new-SHA vs. your vendored copy.
#   4. Hand-apply any upstream changes worth taking, preserving local edits.
#   5. Update the date in .claude/skills/SKILLS.md.
#
set -euo pipefail

cd "$(dirname "$0")/.."
SKILLS_DIR=".claude/skills"
CACHE_DIR="$SKILLS_DIR/.upstream-cache"

# --- pinned sources (keep in sync with .claude/skills/SKILLS.md) ---------------
FRONTEND_REPO="anthropics/claude-code"
FRONTEND_SHA="3deb873687379f0c199a69fdaccc65f0865f7a29"
FRONTEND_PATH="plugins/frontend-design/skills/frontend-design/SKILL.md"

MATTPOCOCK_REPO="mattpocock/skills"
MATTPOCOCK_SHA="49dd158d1076134a641b33efb035946536778336"
GRILLING_PATH="skills/productivity/grilling/SKILL.md"
DOMAIN_SKILL_PATH="skills/engineering/domain-modeling/SKILL.md"
DOMAIN_ADR_PATH="skills/engineering/domain-modeling/ADR-FORMAT.md"
DOMAIN_GLOSSARY_PATH="skills/engineering/domain-modeling/GLOSSARY-FORMAT.md"

raw() { # repo sha path -> stdout
  curl -fsSL "https://raw.githubusercontent.com/$1/$2/$3"
}

# Fetch an upstream file into the cache, then show how it differs from the
# vendored copy. Diff is informational only — nothing is overwritten.
# args: <label> <cache-rel-path> <vendored-path> <repo> <sha> <upstream-path>
fetch_and_diff() {
  local label="$1" cache_rel="$2" vendored="$3" repo="$4" sha="$5" path="$6"
  local cache_file="$CACHE_DIR/$cache_rel"
  mkdir -p "$(dirname "$cache_file")"
  raw "$repo" "$sha" "$path" > "$cache_file"
  echo "=== $label ==="
  if diff -u "$cache_file" "$vendored" >/dev/null 2>&1; then
    echo "  vendored copy is byte-identical to upstream@$sha"
  else
    echo "  differs from upstream@$sha (expected: trimmed frontmatter)"
    echo "  review: diff $cache_file $vendored"
  fi
  echo
}

echo "Fetching pinned upstream copies into $CACHE_DIR (gitignored)..."
echo

fetch_and_diff "frontend-design" \
  "frontend-design.SKILL.md" "$SKILLS_DIR/frontend-design/SKILL.md" \
  "$FRONTEND_REPO" "$FRONTEND_SHA" "$FRONTEND_PATH"

fetch_and_diff "grilling" \
  "grilling.SKILL.md" "$SKILLS_DIR/grilling/SKILL.md" \
  "$MATTPOCOCK_REPO" "$MATTPOCOCK_SHA" "$GRILLING_PATH"

fetch_and_diff "domain-modeling" \
  "domain-modeling.SKILL.md" "$SKILLS_DIR/domain-modeling/SKILL.md" \
  "$MATTPOCOCK_REPO" "$MATTPOCOCK_SHA" "$DOMAIN_SKILL_PATH"

fetch_and_diff "domain-modeling/ADR-FORMAT" \
  "domain-modeling.ADR-FORMAT.md" "$SKILLS_DIR/domain-modeling/references/ADR-FORMAT.md" \
  "$MATTPOCOCK_REPO" "$MATTPOCOCK_SHA" "$DOMAIN_ADR_PATH"

fetch_and_diff "domain-modeling/GLOSSARY-FORMAT" \
  "domain-modeling.GLOSSARY-FORMAT.md" "$SKILLS_DIR/domain-modeling/references/GLOSSARY-FORMAT.md" \
  "$MATTPOCOCK_REPO" "$MATTPOCOCK_SHA" "$DOMAIN_GLOSSARY_PATH"

echo "Done. Nothing was overwritten. grill-with-docs and spec are project-maintained and have no"
echo "single upstream file to diff; maintain them by hand."
