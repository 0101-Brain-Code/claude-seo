"""Phase 0: access and data-availability check runs before crawling."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SKILL = REPO_ROOT / "skills" / "seo-audit" / "SKILL.md"
CHROME_REF = REPO_ROOT / "skills" / "seo-audit" / "references" / "chrome-assisted-data.md"


def _audit_text() -> str:
    return AUDIT_SKILL.read_text(encoding="utf-8")


def _phase0_section() -> str:
    text = _audit_text()
    section = text.split("## Phase 0: Access & Data Availability", 1)[1]
    return re.split(r"^## ", section, maxsplit=1, flags=re.M)[0]


# ─── Phase 0 exists, runs first, and offers the three options ───────────────

def test_phase_0_precedes_crawling_in_the_process() -> None:
    text = _audit_text()
    process = text.split("## Process", 1)[1]
    process = re.split(r"^## ", process, maxsplit=1, flags=re.M)[0]
    assert process.index("Check data access") < process.index("Crawl site")


def test_phase_0_runs_both_credential_checks() -> None:
    section = _phase0_section()
    assert "google_auth.py --check --json" in section
    assert "backlinks_auth.py --check --json" in section


def test_phase_0_offers_connect_chrome_assisted_and_proceed_without() -> None:
    section = _phase0_section()
    assert "**(a) Connect it now.**" in section
    assert "**(b) Use Chrome-assisted checking.**" in section
    assert "**(c) Proceed without it.**" in section


def test_phase_0_names_every_source_the_user_must_be_asked_about() -> None:
    section = _phase0_section()
    for source in ("GSC", "GA4", "CrUX/PageSpeed", "backlinks"):
        assert source in section, source


def test_phase_0_forbids_estimating_an_unavailable_source() -> None:
    section = _phase0_section()
    assert "never estimated, never scored" in section
    assert "not-assessed" in section


def test_phase_0_records_outcomes_before_step_1() -> None:
    section = _phase0_section()
    assert "data_sources" in section
    assert "before continuing to Step 1" in section


def test_phase_0_prompts_once_not_per_finding() -> None:
    section = _phase0_section()
    assert "do not\nre-prompt per finding" in section


# ─── Chrome-assisted reference ──────────────────────────────────────────────

def test_chrome_assisted_reference_exists_and_is_linked_from_the_skill() -> None:
    assert CHROME_REF.is_file()
    assert "references/chrome-assisted-data.md" in _audit_text()


def test_chrome_assisted_is_read_only_with_the_rank_math_example() -> None:
    text = CHROME_REF.read_text(encoding="utf-8")
    assert "read-only" in text.lower()
    assert "Never use it to change settings, submit forms" in text
    # The specific temptation the guardrail exists for.
    assert "Rank Math" in text
    assert "report it as a recommendation for a human to\napply" in text


def test_chrome_assisted_caps_confidence_below_high() -> None:
    text = CHROME_REF.read_text(encoding="utf-8")
    assert "`source: chrome-assisted`" in text
    assert "`confidence: Medium` **at most** -- never `High`" in text


def test_chrome_assisted_requires_naming_the_screen_read() -> None:
    text = CHROME_REF.read_text(encoding="utf-8")
    assert "specific screen or report read" in text
    assert "`description`" in text


def test_chrome_assisted_specifies_what_to_read_for_each_source() -> None:
    text = CHROME_REF.read_text(encoding="utf-8")
    assert "search.google.com/search-console" in text
    assert "Performance report" in text
    assert "URL Inspection" in text
    assert "up to **5 specific URLs**" in text
    assert "Traffic acquisition" in text
    assert "Landing page" in text


def test_chrome_assisted_forbids_a_full_query_export() -> None:
    text = CHROME_REF.read_text(encoding="utf-8")
    assert "Do not attempt a full query-by-page export this way" in text
    assert "spot-check" in text


def test_chrome_assisted_does_not_substitute_for_unscoreable_sources() -> None:
    """The fallback tier must not quietly become a source of invented numbers."""
    text = CHROME_REF.read_text(encoding="utf-8")
    tail = text.split("## What this tier cannot do", 1)[1]
    assert "lab-estimate" in tail
    assert "Backlink profiles" in tail
    assert "no numeric score" in tail


# ─── Simulated run: no credentials configured ───────────────────────────────

def test_credential_check_reports_no_scoreable_backlink_source(tmp_path: Path) -> None:
    """With an empty HOME, Phase 0 must see Moz and Bing as unavailable.

    This is the state that drives the Common-Crawl-only path, so the audit has
    to be able to detect it before crawling rather than after.
    """
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "SYSTEMROOT": ""}
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "backlinks_auth.py"), "--check", "--json"],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT),
    )
    payload = json.loads(proc.stdout)
    sources = payload["services"]

    assert sources["moz"]["available"] is False
    assert sources["bing"]["available"] is False
    # Common Crawl needs no credentials, which is exactly why it must not be scored.
    assert sources["commoncrawl"]["available"] is True


def test_chrome_assisted_findings_render_with_source_and_confidence(tmp_path: Path) -> None:
    """Simulated option (b): the resulting report must show how the data was got."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import google_report  # noqa: PLC0415

    data = {
        "summary": {"health_score": 70},
        "data_sources": {
            "google_search_console": {"available": True, "method": "chrome-assisted"},
            "backlinks": {"available": False, "method": "not-assessed"},
        },
        "categories": [
            {
                "name": "Indexation",
                "findings": [
                    {
                        "title": "Indexed page count below sitemap count",
                        "severity": "High",
                        "confidence": "Medium",
                        "business_impact": "Medium",
                        "description": (
                            "Read from GSC Pages report (Indexing -> Pages): 412 indexed "
                            "against 1,180 sitemap URLs. Spot-check, not a structured pull."
                        ),
                        "source": "chrome-assisted",
                    }
                ],
            }
        ],
    }

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )
    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    assert "Source: chrome-assisted" in html
    assert "Confidence: Medium" in html
    assert "Confidence: High" not in html
    # The specific screen read is carried into the report.
    assert "GSC Pages report" in html
    # And the methodology page labels the method rather than implying an API pull.
    assert "Chrome-assisted (UI read)" in html
