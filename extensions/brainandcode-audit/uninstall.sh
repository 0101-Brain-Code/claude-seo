#!/usr/bin/env bash
set -euo pipefail
REF="${HOME}/.claude/skills/seo-audit/references/chrome-assisted-data.md"
[ -f "${REF}" ] && rm -f "${REF}" && echo "✓ Removed ${REF}"
rmdir "${HOME}/.claude/skills/seo-audit/references" 2>/dev/null || true
echo "Done. Phase 0 falls back to options (a) and (c) only."
echo "(Nothing to remove from settings.json — this extension has no keys.)"
