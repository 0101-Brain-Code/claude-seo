"""Full audit report generation from non-Google audit data."""

from __future__ import annotations

import os
import runpy
import sys
import builtins
from pathlib import Path
from unittest.mock import patch


_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import google_report  # noqa: E402


def test_module_import_is_safe_without_native_report_dependencies() -> None:
    real_import = builtins.__import__

    def unavailable(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"matplotlib", "weasyprint"}:
            raise ImportError(f"{name} unavailable")
        return real_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=unavailable):
        namespace = runpy.run_path(str(Path(google_report.__file__)))

    assert namespace["plt"] is None
    assert namespace["HTML"] is None


def test_html_report_without_chart_data_does_not_require_native_report_dependencies(
    tmp_path: Path,
) -> None:
    with patch.object(google_report, "plt", None), \
         patch.object(google_report, "np", None), \
         patch.object(google_report, "HTML", None), \
         patch.object(google_report, "_CHART_IMPORT_ERROR", ImportError("missing")):
        result = google_report.generate_report(
            "full",
            {"summary": {"health_score": 80}},
            "example.com",
            tmp_path,
            output_format="html",
        )

    assert result["error"] is None
    assert Path(result["files"][0]).is_file()


def test_chart_report_returns_dependency_error_at_runtime(tmp_path: Path) -> None:
    with patch.object(google_report, "plt", None), \
         patch.object(google_report, "np", None), \
         patch.object(google_report, "_CHART_IMPORT_ERROR", ImportError("missing")):
        result = google_report.generate_report(
            "cwv-audit",
            {"lighthouse_scores": {"performance": 90}},
            "example.com",
            tmp_path,
            output_format="html",
        )

    assert result["files"] == []
    assert "matplotlib and numpy are required" in result["error"]


def test_pdf_report_returns_dependency_error_at_runtime(tmp_path: Path) -> None:
    with patch.object(google_report, "HTML", None), \
         patch.object(google_report, "_PDF_IMPORT_ERROR", ImportError("missing")):
        result = google_report.generate_report(
            "full",
            {"summary": {"health_score": 80}},
            "example.com",
            tmp_path,
            output_format="pdf",
        )

    assert result["files"] == []
    assert "weasyprint is required" in result["error"]


def test_full_audit_html_includes_summary_categories_and_roadmap(tmp_path: Path) -> None:
    data = {
        "summary": {
            "health_score": 82,
            "business_type": "SaaS",
            "top_findings": [
                {"title": "Canonical mismatch", "severity": "Critical"},
                "Thin service pages",
            ],
            "quick_wins": ["Add missing meta descriptions"],
        },
        "categories": [
            {
                "name": "Technical SEO",
                "score": 74,
                "what_works": ["HTTPS is enabled", "Robots.txt is reachable"],
                "findings": [
                    {
                        "title": "Canonical mismatch",
                        "severity": "Critical",
                        "description": "Homepage canonical points to a staging URL.",
                        "recommendation": "Set canonical to the production HTTPS URL.",
                    }
                ],
            },
            {
                "name": "Content Quality",
                "score": 68,
                "what_works": ["Clear product positioning"],
                "findings": [
                    {
                        "title": "Thin comparison pages",
                        "severity": "High",
                        "description": "Several pages have fewer than 300 words.",
                    }
                ],
            },
        ],
        "action_plan": {
            "phases": [
                {
                    "name": "Phase 1: Indexing Fixes",
                    "timeframe": "Week 1",
                    "items": ["Fix canonical mismatch", "Resubmit sitemap"],
                },
                {
                    "name": "Phase 2: Content Expansion",
                    "timeframe": "Weeks 2-3",
                    "items": ["Expand comparison page copy"],
                },
            ]
        },
    }

    result = google_report.generate_report(
        "full",
        data,
        "example.com",
        tmp_path,
        output_format="html",
    )

    assert result["error"] is None
    html_path = Path(result["files"][0])
    html = html_path.read_text(encoding="utf-8")
    assert "Executive Summary" in html
    assert "SaaS" in html
    assert "Technical SEO" in html
    assert "What Works" in html
    assert "Canonical mismatch" in html
    assert "Action Plan" in html
    assert "Phase 1: Indexing Fixes" in html
    assert "Content Quality" in html


def test_full_audit_renders_confidence_and_business_impact_separately(tmp_path: Path) -> None:
    """Severity, business_impact, and confidence are distinct visual elements."""
    data = {
        "summary": {"health_score": 71},
        "categories": [
            {
                "name": "Technical SEO",
                "findings": [
                    {
                        "title": "Missing security headers",
                        "severity": "Low",
                        "confidence": "High",
                        "business_impact": "Critical",
                        "description": "No HSTS or X-Content-Type-Options header.",
                        "recommendation": "Add HSTS and X-Content-Type-Options.",
                        "source": "api",
                    },
                    {
                        "title": "Canonical mismatch",
                        "severity": "Critical",
                        "confidence": "High",
                        "business_impact": "Critical",
                        "description": "Canonical points at staging.",
                        "source": "api",
                    },
                ],
            }
        ],
    }

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    # Severity drives the colour class on the heading badge.
    assert 'class="sev-low">Low<' in html
    assert 'class="sev-critical">Critical<' in html
    # business_impact gets its own badge when it diverges from severity...
    assert "Business impact: Critical" in html
    # ...and exactly once: the second finding's impact matches its severity.
    assert html.count("Business impact:") == 1
    # confidence is rendered separately from both.
    assert "Confidence: High" in html
    assert "Source: api" in html


def test_full_audit_methodology_lists_only_available_data_sources(tmp_path: Path) -> None:
    """Only sources marked available:true appear as used, with their method label."""
    data = {
        "summary": {"health_score": 64},
        "data_sources": {
            "google_search_console": {"available": True, "method": "chrome-assisted"},
            "ga4": {"available": True, "method": "api"},
            "crux": {"available": False, "method": "not-assessed"},
            "pagespeed_insights": {"available": False, "method": "not-assessed"},
            "backlinks": {"available": False, "method": "not-assessed"},
        },
    }

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    used = html.split("Not Assessed", 1)[0]
    assert "Google Search Console" in used
    assert "Chrome-assisted (UI read)" in used
    assert "Google Analytics 4" in used
    assert "API" in used

    # Unavailable sources are never presented as consulted.
    assert "Chrome UX Report" not in used
    assert "PageSpeed Insights API" not in used

    not_assessed = html.split("Not Assessed", 1)[1]
    assert "Chrome UX Report (CrUX)" in not_assessed
    assert "PageSpeed Insights API" in not_assessed
    assert "Backlink providers" in not_assessed


def test_full_audit_without_data_sources_block_keeps_static_methodology(tmp_path: Path) -> None:
    """Reports with no data_sources block fall back to the legacy methodology page."""
    result = google_report.generate_report(
        "full", {"summary": {"health_score": 80}}, "example.com", tmp_path,
        output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")
    assert "Data Sources &amp; Methodology" in html
    assert "Chrome UX Report (CrUX)" in html


def test_exec_summary_header_says_critical_when_a_critical_finding_is_listed(
    tmp_path: Path,
) -> None:
    """A real Critical finding keeps the original 'Critical Issues Found:' label."""
    data = {
        "summary": {
            "health_score": 42,
            "top_findings": [
                {"title": "Canonical points at staging", "severity": "Critical"},
                {"title": "Meta description templated", "severity": "High"},
            ],
        },
    }

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    assert "Critical Issues Found:" in html
    assert "High-Priority Issues Found:" not in html


def test_exec_summary_header_avoids_critical_when_highest_severity_is_high(
    tmp_path: Path,
) -> None:
    """The rfidhotel.com case: all-High findings must not be labelled Critical."""
    data = {
        "summary": {
            "health_score": 68,
            "top_findings": [
                {"title": "Meta description templated", "severity": "High"},
                {"title": "product_brand taxonomy empty", "severity": "High"},
                {"title": "Thin category copy", "severity": "Medium"},
            ],
        },
    }

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    assert "Critical Issues Found:" not in html
    assert "High-Priority Issues Found:" in html


def test_exec_summary_header_ignores_critical_findings_truncated_out_of_view(
    tmp_path: Path,
) -> None:
    """The box renders only five entries; the label describes what is shown.

    A Critical finding sitting past the truncation point must not produce a
    'Critical' header above a list that never displays it.
    """
    findings = [
        {"title": f"High issue {n}", "severity": "High"} for n in range(5)
    ]
    findings.append({"title": "Hidden critical", "severity": "Critical"})
    data = {"summary": {"health_score": 55, "top_findings": findings}}

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    assert "Hidden critical" not in html
    assert "Critical Issues Found:" not in html
    assert "High-Priority Issues Found:" in html


def test_exec_summary_header_is_neutral_when_no_entry_carries_a_severity(
    tmp_path: Path,
) -> None:
    """Lighthouse/indexation entries have no severity and must not imply one."""
    data = {
        "summary": {"health_score": 77},
        "inspection": {"summary": {"fail": 3}},
    }

    result = google_report.generate_report(
        "full", data, "example.com", tmp_path, output_format="html",
    )

    assert result["error"] is None
    html = Path(result["files"][0]).read_text(encoding="utf-8")

    # The entry is rendered, so the assertions below are not vacuous.
    assert "3 URL(s)</strong> not indexed" in html
    assert "Critical Issues Found:" not in html
    assert "High-Priority Issues Found:" not in html
    assert "Issues Found:" in html
