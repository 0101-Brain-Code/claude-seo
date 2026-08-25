#!/usr/bin/env bash
# Claude SEO — Brain & Code audit extension installer.
#
# Adds the Chrome-assisted data tier to the seo-audit skill's Phase 0.
# When an API is unavailable, this lets the orchestrator read the same
# numbers from the product UI (Search Console, GA4, CMS settings) instead
# of silently falling back to lab estimates.
#
# Read-only by design, and no API keys — it reuses whatever browser tools
# the session already has.
set -euo pipefail

main() {
    SKILL_DIR="${HOME}/.claude/skills"

    echo "════════════════════════════════════════"
    echo "║   Claude SEO — Brain & Code audit     ║"
    echo "════════════════════════════════════════"

    [ ! -d "${SKILL_DIR}/seo" ]       && { echo "✗ claude-seo base not installed."; exit 1; }
    [ ! -d "${SKILL_DIR}/seo-audit" ] && { echo "✗ seo-audit skill not installed."; exit 1; }

    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd)"

    mkdir -p "${SKILL_DIR}/seo-audit/references"
    cp "${SOURCE_DIR}/skills/seo-audit/references/chrome-assisted-data.md" \
       "${SKILL_DIR}/seo-audit/references/chrome-assisted-data.md"
    echo "✓ Installed reference: ${SKILL_DIR}/seo-audit/references/chrome-assisted-data.md"

    echo ""
    echo "Phase 0 option (b) is now available in full audits."
    echo "Setup notes: docs/BRAINANDCODE-AUDIT-SETUP.md"
}
main "$@"
