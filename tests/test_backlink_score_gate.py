"""Backlink scoring: never emit a number for data that was not measured.

The rule already existed as prose in the skill and was violated in a real audit
anyway. These tests pin it to something checkable.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = str(REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import validate_backlink_report as vbr  # noqa: E402


# ─── Backlink score gating ───────────────────────────────────────────────────

BACKLINKS_SKILL = REPO_ROOT / "skills" / "seo-backlinks" / "SKILL.md"


def test_backlinks_skill_states_must_not_and_names_the_validator() -> None:
    text = BACKLINKS_SKILL.read_text(encoding="utf-8")
    assert "MUST NOT" in text
    assert "validate_backlink_report.py" in text
    assert "status: FAIL" in text


def test_common_crawl_only_numeric_score_fails_validation() -> None:
    result = vbr.validate_report({
        "cc_data": {"rank": 1234, "in_degree": 57},
        "scoring_factors": {"score": 42, "factors_with_data": 2, "total_factors": 7},
    })

    assert result["status"] == "FAIL"
    messages = [i["message"] for i in result["data"]["issues"]]
    assert any("Common Crawl was the only source available" in m for m in messages)


def test_common_crawl_only_without_a_score_passes() -> None:
    """Not Assessed is the correct output, and it must validate cleanly."""
    result = vbr.validate_report({
        "cc_data": {"rank": 1234, "in_degree": 57},
        "scoring_factors": {"score": None, "factors_with_data": 2, "total_factors": 7},
        "findings": [
            {"title": "Backlink profile", "source": "not-assessed", "score": None},
        ],
    })

    errors = [i for i in result["data"]["issues"] if i["severity"] == "error"]
    assert errors == []


def test_not_assessed_finding_with_a_numeric_score_fails_validation() -> None:
    result = vbr.validate_report({
        "moz_data": {"domain_authority": 30},
        "findings": [
            {"title": "Referring domain quality", "source": "not-assessed", "score": 55},
        ],
    })

    assert result["status"] == "FAIL"
    messages = [i["message"] for i in result["data"]["issues"]]
    assert any("MUST NOT be scored" in m for m in messages)


def test_numeric_score_string_is_still_caught() -> None:
    """A score serialised as a string is the same misleading number."""
    result = vbr.validate_report({
        "cc_data": {"rank": 1},
        "scoring_factors": {"score": "42"},
    })
    assert result["status"] == "FAIL"


def test_score_is_allowed_once_a_scoreable_source_has_data() -> None:
    result = vbr.validate_report({
        "cc_data": {"rank": 1},
        "moz_data": {"domain_authority": 41},
        "scoring_factors": {"score": 68, "factors_with_data": 5, "total_factors": 7},
    })

    errors = [i for i in result["data"]["issues"] if i["severity"] == "error"]
    assert errors == []


def test_errored_source_does_not_count_as_available() -> None:
    """A Moz call that failed must not unlock scoring."""
    result = vbr.validate_report({
        "cc_data": {"rank": 1},
        "moz_data": {"error": "401 unauthorized"},
        "scoring_factors": {"score": 68},
    })

    assert result["status"] == "FAIL"


def test_source_score_consistency_runs_without_a_scoring_factors_block() -> None:
    """The gate must fire even when the agent omits scoring_factors entirely."""
    result = vbr.validate_report({
        "findings": [
            {"title": "Anchor text", "source": "not-assessed", "health_score": 12},
        ],
    })

    assert result["status"] == "FAIL"
    assert "source_score_consistency" in result["metadata"]["checks_run"]
