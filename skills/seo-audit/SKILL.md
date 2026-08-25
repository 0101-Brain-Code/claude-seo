---
name: seo-audit
description: "Full website SEO audit with parallel subagent delegation. Crawls up to 500 pages, detects business type, delegates to up to 15 specialists (8 always + 7 conditional), generates health score. Use when user says audit, full SEO check, analyze my site, or website health check."
user-invocable: true
argument-hint: "[url]"
license: MIT
metadata:
  author: AgriciDaniel
  version: "2.2.4"
  category: seo
---

# Full Website SEO Audit

## Process

0. **Check data access (before anything else).** Run `claude-seo run google_auth.py --check --json`
   and `claude-seo run backlinks_auth.py --check --json` to establish which data sources are
   actually available *before* crawling begins. Record the outcome for every source in the
   `data_sources` block of `audit-data.json` (see the Structured Audit Data Envelope below).
   An audit must never discover partway through that it has been estimating what it could
   have measured.
1. **Render homepage**: use `claude-seo run render_page.py <url> --mode auto --json` to capture raw HTML, rendered HTML, extracted text, SPA status, and accessibility data when needed
2. **Detect business type**: analyze homepage signals per seo orchestrator
3. **Crawl site**: follow internal links up to 500 pages, respect robots.txt
4. **Delegate to subagents** (if available, otherwise run inline sequentially):
   - `seo-technical` -- robots.txt, sitemaps, canonicals, Core Web Vitals, security headers
   - `seo-content` -- E-E-A-T, readability, thin content, AI citation readiness
   - `seo-schema` -- detection, validation, generation recommendations
   - `seo-sitemap` -- structure analysis, quality gates, missing pages
   - `seo-performance` -- LCP, INP, CLS measurements
   - `seo-visual` -- screenshots, mobile testing, above-fold analysis
   - `seo-geo` -- AI crawler access, llms.txt, citability, brand mention signals
   - `seo-local` -- GBP signals, NAP consistency, reviews, local schema, industry-specific local factors (spawn when Local Service industry detected: brick-and-mortar, SAB, or hybrid business type)
   - `seo-maps` -- Geo-grid rank tracking, GBP audit, review intelligence, competitor radius mapping (spawn when Local Service detected AND DataForSEO MCP available)
   - `seo-google` -- CWV field data (CrUX), URL indexation (GSC), organic traffic (GA4) (spawn when Google API credentials detected via `claude-seo run google_auth.py --check`)
   - `seo-backlinks` -- Backlink profile data: DA/PA, referring domains, anchor text, toxic links (spawn when Moz or Bing API credentials detected via `claude-seo run backlinks_auth.py --check`, or always include Common Crawl domain-level metrics)
   - `seo-cluster` -- Semantic clustering analysis (spawn when content strategy signals detected: blog, pillar pages, topic clusters)
   - `seo-sxo` -- Search experience analysis: page-type mismatch, user stories, persona scoring (always include in full audits)
   - `seo-drift` -- Drift analysis: compare against stored baseline (spawn when drift baseline exists for the URL via `claude-seo run drift_history.py <url>`)
   - `seo-ecommerce` -- Product schema, marketplace intelligence (spawn when E-commerce industry detected)
5. **Score** -- aggregate into SEO Health Score (0-100)
6. **Persist audit artifacts** -- write all outputs under `{domain}-audit/`
7. **Report** -- generate prioritized action plan and optional PDF/HTML report

## Crawl Configuration

```
Max pages: 500
Respect robots.txt: Yes
Follow redirects: Yes (max 3 hops)
Timeout per page: 30 seconds
Concurrent requests: 5
Delay between requests: 1 second
```

## Output Files

- `{domain}-audit/FULL-AUDIT-REPORT.md`: Comprehensive findings
- `{domain}-audit/ACTION-PLAN.md`: Prioritized recommendations (Critical > High > Medium > Low)
- `{domain}-audit/audit-data.json`: Structured audit envelope for report generation
- `{domain}-audit/findings/*.md`: Per-category specialist findings (`technical.md`, `content.md`, `schema.md`, `performance.md`, `visual.md`, etc.)
- `{domain}-audit/screenshots/`: Desktop + mobile captures (if Playwright available)
- **PDF Report** (recommended): Generate a professional A4 PDF using `claude-seo run google_report.py --type full --data {domain}-audit/audit-data.json --domain <domain> --output-dir {domain}-audit/`. This produces a white-cover enterprise report with TOC, executive summary, charts (Lighthouse gauges, query bars, index donut), metric cards, threshold tables, prioritized recommendations with effort estimates, and implementation roadmap. Always offer PDF generation after completing an audit.

## Structured Audit Data Envelope

Write `{domain}-audit/audit-data.json` with this shape so `claude-seo run google_report.py --type full --data {domain}-audit/audit-data.json --domain <domain> --output-dir {domain}-audit/` can generate a report even when Google API data is unavailable:

```json
{
  "summary": {
    "health_score": 0,
    "business_type": "detected type",
    "top_findings": [],
    "quick_wins": []
  },
  "categories": [
    {
      "name": "Technical SEO",
      "score": 0,
      "what_works": [],
      "findings": [
        {
          "title": "Finding title",
          "severity": "Critical|High|Medium|Low|Info",
          "confidence": "High|Medium|Low",
          "business_impact": "Critical|High|Medium|Low|Info|N/A",
          "description": "Evidence-backed detail",
          "recommendation": "Specific fix",
          "source": "api|chrome-assisted|lab-estimate|not-assessed"
        }
      ]
    }
  ],
  "action_plan": {
    "phases": [
      {"name": "Phase 1: Critical Fixes", "timeframe": "Week 1", "items": []},
      {"name": "Phase 2: High-Impact Improvements", "timeframe": "Weeks 2-3", "items": []},
      {"name": "Phase 3: Content & Authority", "timeframe": "Month 2", "items": []},
      {"name": "Phase 4: Monitoring & Iteration", "timeframe": "Ongoing", "items": []}
    ]
  },
  "artifacts": {
    "findings_dir": "findings/",
    "screenshots_dir": "screenshots/"
  },
  "data_sources": {
    "google_search_console": {"available": false, "method": "not-assessed"},
    "ga4": {"available": false, "method": "not-assessed"},
    "crux": {"available": false, "method": "not-assessed"},
    "pagespeed_insights": {"available": false, "method": "not-assessed"},
    "backlinks": {"available": false, "method": "not-assessed"}
  }
}
```

### Finding Fields

- **`severity`** -- how much this hurts *SEO* specifically. Drives report ordering and colour.
- **`confidence`** -- how sure the specialist is, given the data actually available. This is not a second measure of severity: a `Critical` finding backed only by a lab estimate is `severity: Critical, confidence: Low`.
- **`business_impact`** -- what happens if this is never fixed, independent of SEO severity. This is what lets "zero security headers" be `severity: Low` (it barely touches rankings) while `business_impact: Critical` (it is still a real security gap worth fixing). Severity and business impact are allowed to diverge; **do not collapse them back into one number**. Use `N/A` when the finding is purely an SEO concern with no separate business consequence.
- **`source`** -- where this finding's evidence came from:
  - `api` -- a structured pull from a credentialed API (GSC, GA4, CrUX, PageSpeed, Moz, Bing).
  - `chrome-assisted` -- read from a UI in the browser rather than from an API. Never `confidence: High`.
  - `lab-estimate` -- synthetic/lab measurement standing in for field data.
  - `not-assessed` -- the data source was unavailable and the check was not performed. **A `not-assessed` finding must never carry a numeric score.** Report "Not Assessed", never an estimate.

### Data Sources Block

`data_sources` records what was actually available for this audit. `method` is one of
`api`, `chrome-assisted`, or `not-assessed`. Step 0 of the Process populates this block
before crawling begins, and the report generator renders the "Data Sources & Methodology"
page from it -- only sources with `available: true` are listed as used. Never leave this
block at its defaults if a source was in fact consulted.

## Scoring Weights

| Category | Weight |
|----------|--------|
| Technical SEO | 22% |
| Content Quality | 23% |
| On-Page SEO | 20% |
| Schema / Structured Data | 10% |
| Performance (CWV) | 10% |
| AI Search Readiness | 10% |
| Images | 5% |

## Report Structure

### Executive Summary
- Overall SEO Health Score (0-100)
- Business type detected
- Top 5 critical issues
- Top 5 quick wins

### Technical SEO
- Crawlability issues
- Indexability problems
- Security concerns
- Core Web Vitals status

### Content Quality
- E-E-A-T assessment
- Thin content pages
- Duplicate content issues
- Readability scores

### On-Page SEO
- Title tag issues
- Meta description problems
- Heading structure
- Internal linking gaps

### Schema & Structured Data
- Current implementation
- Validation errors
- Missing opportunities

### Performance
- LCP, INP, CLS scores
- Resource optimization needs
- Third-party script impact

### Images
- Missing alt text
- Oversized images
- Format recommendations

### AI Search Readiness
- Citability score
- Structural improvements
- Authority signals

## Priority Definitions

- **Critical**: Blocks indexing or causes penalties (fix immediately)
- **High**: Significantly impacts rankings (fix within 1 week)
- **Medium**: Optimization opportunity (fix within 1 month)
- **Low**: Nice to have (backlog)

## DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, spawn the `seo-dataforseo` agent alongside existing subagents to enrich the audit with live data: real SERP positions, backlink profiles with spam scores, on-page analysis (Lighthouse), business listings, and AI visibility checks (ChatGPT scraper, LLM mentions).

## Google API Integration

The credential check itself runs in **Step 0 of the Process**, before crawling -- not
here, and not partway through the audit. This section describes what to do with the
result.

If Google API credentials are configured, spawn the `seo-google` agent to enrich the
audit with real Google field data: CrUX Core Web Vitals (replaces lab-only estimates),
GSC URL indexation status, search performance (clicks, impressions, CTR), and GA4
organic traffic trends. The Performance (CWV) category score benefits most from field
data.

If they are not configured, the affected sources are recorded as
`available: false, method: not-assessed` in `data_sources`, and every finding that
would have depended on them is written with `source: not-assessed` and reported as
"Not Assessed" -- never estimated, never scored.

## Error Handling

| Scenario | Action |
|----------|--------|
| URL unreachable (DNS failure, connection refused) | Report the error clearly. Do not guess site content. Suggest the user verify the URL and try again. |
| robots.txt blocks crawling | Report which paths are blocked. Analyze only accessible pages and note the limitation in the report. |
| Rate limiting (429 responses) | Back off and reduce concurrent requests. Report partial results with a note on which sections could not be completed. |
| Timeout on large sites (500+ pages) | Cap the crawl at the timeout limit. Report findings for pages crawled and estimate total site scope. |
