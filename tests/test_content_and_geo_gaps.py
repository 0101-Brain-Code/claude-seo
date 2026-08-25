"""Stage 4 gap fixes: schema severity, link heuristics, merge gate, crawler claims."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "agents"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


# ─── 4a. Schema type mismatches have a severity ──────────────────────────────

def test_schema_skill_assigns_severity_to_type_mismatch_and_breadcrumbs() -> None:
    text = _read("skills/seo-schema/SKILL.md")
    section = text.split("## Severity Assignment (binding)", 1)[1]
    section = re.split(r"^## ", section, maxsplit=1, flags=re.M)[0]

    rows = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] == "Finding" or set(cells[0]) <= {"-", ":"}:
            continue
        rows[cells[0]] = (cells[1], cells[2])

    mismatch = next(k for k in rows if "typed as `Article`" in k)
    breadcrumb = next(k for k in rows if "BreadcrumbList" in k)

    # Real fixes, not urgent ones: both must sit in the Medium/Low range.
    assert rows[mismatch][0] in {"Medium", "Low"}
    assert rows[breadcrumb][0] in {"Medium", "Low"}


# ─── 4b. Internal-link sufficiency is a heuristic, not a gate ────────────────

def test_content_skill_flags_orphans_without_inventing_a_link_threshold() -> None:
    text = _read("skills/seo-content/SKILL.md")
    assert "no universal minimum-link threshold" in text
    assert "0-1 inbound internal links" in text
    assert "hierarchy" in text.lower()


def test_no_skill_hardcodes_a_five_inbound_link_rule() -> None:
    """The '5 inbound links' number was invented ad hoc; it must not reappear."""
    pattern = re.compile(
        r"\b(?:at least|minimum(?: of)?|min\.?)\s+\d+\s+(?:inbound|incoming|internal)\s+links",
        re.I,
    )
    for path in SKILLS.rglob("SKILL.md"):
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), f"{path.relative_to(REPO_ROOT)} hardcodes a link count"


# ─── 4c. Metadata length is a heuristic ─────────────────────────────────────

def test_metadata_length_is_stated_as_a_truncation_heuristic() -> None:
    for rel in ("skills/seo-page/SKILL.md", "skills/seo-ecommerce/SKILL.md"):
        text = _read(rel)
        assert "not a compliance cliff" in text, rel
        assert "61-character title is not a violation" in text, rel
        assert ">80 or <20 characters" in text, rel


def test_ecommerce_checklist_no_longer_uses_hard_under_n_characters() -> None:
    text = _read("skills/seo-ecommerce/SKILL.md")
    assert "Under 60 characters" not in text
    assert "Under 155 characters" not in text


# ─── 4d. Cannibalization merge gate ─────────────────────────────────────────

def test_merge_recommendations_require_query_overlap_or_low_confidence() -> None:
    text = _read("skills/seo-content/SKILL.md")
    assert "Never recommend a URL merge or 301 on topic or URL similarity alone" in text
    # The gate keys off the Stage 2 data_sources block.
    assert "data_sources.google_search_console.available" in text
    # Without GSC the pair is still surfaced, but explicitly low-confidence.
    assert "`confidence: Low`" in text
    assert "query overlap could not be verified" in text


# ─── 4e. AI crawler claims are checked against the right bot ────────────────

def test_gptbot_is_not_described_as_the_chatgpt_search_crawler() -> None:
    text = _read("skills/seo-geo/SKILL.md")
    assert "| GPTBot | OpenAI | ChatGPT web search | yes |" not in text
    assert "OAI-SearchBot" in text
    assert "ChatGPT Search citability" in text


def test_geo_skill_separates_training_crawlers_from_search_crawlers() -> None:
    text = _read("skills/seo-geo/SKILL.md")
    assert "Check the right bot for the claim you are making" in text
    assert "does not affect inclusion in ordinary Google Search" in text
    assert "tells\n  you nothing about whether ChatGPT Search can cite the page" in text


def test_google_extended_is_never_a_google_search_readiness_signal() -> None:
    """Named claim, checked in both the skill and the agent that runs it."""
    for rel in ("skills/seo-geo/SKILL.md", "agents/seo-geo.md"):
        text = _read(rel)
        assert "Google-Extended" in text, rel
        lowered = text.lower()
        assert "not google search" in lowered or "never google search" in lowered, rel

    skill = _read("skills/seo-geo/SKILL.md")
    assert 'Never score\n  `Google-Extended` as a "Google Search readiness" signal' in skill


def test_technical_skill_checks_oai_searchbot_separately_from_gptbot() -> None:
    text = _read("skills/seo-technical/SKILL.md")
    assert "| OAI-SearchBot | OpenAI | `OAI-SearchBot` | ChatGPT Search citability |" in text
    assert "governed by `OAI-SearchBot`" in text


def test_geo_output_reports_training_and_citability_separately() -> None:
    text = _read("skills/seo-geo/SKILL.md")
    assert "must never be merged into one line" in text


# ─── 4f. Credential check runs before crawling ──────────────────────────────

def test_audit_process_checks_credentials_before_rendering_or_crawling() -> None:
    text = _read("skills/seo-audit/SKILL.md")
    process = text.split("## Process", 1)[1]
    process = re.split(r"^## ", process, maxsplit=1, flags=re.M)[0]

    check_pos = process.index("Check data access")
    render_pos = process.index("Render homepage")
    crawl_pos = process.index("Crawl site")

    assert check_pos < render_pos < crawl_pos

    # The check itself is a real command invocation, wherever the step body lives.
    assert "google_auth.py --check" in text
    assert "backlinks_auth.py --check" in text


def test_google_api_section_no_longer_owns_the_credential_check() -> None:
    """The check was documented near the bottom as 'Optional'; it is now Step 0."""
    text = _read("skills/seo-audit/SKILL.md")
    assert "## Google API Integration (Optional)" not in text
    assert "The credential check itself runs in **Step 0 of the Process**" in text
