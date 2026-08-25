# Brain & Code Audit Extension — Setup

Adds the **Chrome-assisted data tier** to Phase 0 of the `seo-audit` skill.

## What it changes

Core `claude-seo` Phase 0 checks data access before crawling and offers two paths for
an unavailable source: connect the API, or proceed with the source marked
`not-assessed`.

This extension adds a third: **read the numbers from the product UI** when a browser
with Chrome tools is available in the session. That covers the common real-world case
where the user has Search Console and GA4 open in a browser but no service account
configured, and the alternative would be an audit that reports "Not Assessed" for data
that is sitting on screen.

## Install

```bash
./install.sh
```

Requires `claude-seo` and the `seo-audit` skill already installed. No API keys, no MCP
server, no network calls of its own — it reuses whatever browser tooling the session
already has.

Windows:

```powershell
.\install.ps1
```

## Uninstall

```bash
./uninstall.sh
```

Phase 0 then falls back to options (a) and (c) only, which is core behaviour.

## What it installs

One file: `~/.claude/skills/seo-audit/references/chrome-assisted-data.md`.

## Constraints worth knowing before you use it

- **Read-only.** The reference forbids changing settings, submitting forms, or fixing
  findings through the browser, even when the control is right there. Settings fixes
  are reported as recommendations for a human to apply.
- **Confidence is capped at `Medium`.** A UI reading is a spot-check, not a structured
  export, and findings must name the specific screen they were read from.
- **It does not substitute for everything.** Backlink profiles and field CrUX data
  stay `not-assessed`; there is no UI reading that makes them scoreable.
- **It is not sufficient for the cannibalization merge gate.** Verifying query overlap
  between two pages needs the GSC API, so merge recommendations built on a
  chrome-assisted reading stay `confidence: Low`.

## Why this is an extension rather than core

The Chrome-assisted tier assumes a working style — an operator with the relevant
dashboards already open, running audits interactively — that is specific to how Brain &
Code runs audits, not a universal default. Core Phase 0 stands on its own without it.
