#!/usr/bin/env python3
"""Tests for the "Try the demos" / "How it works" page (#508 §6).

The page is a public description of what the three demos do. Its value is that
it is accurate, so the tests pin the claims that are cheap to break: it is built
and linked, it reaches all three experiences, it says no model is called, it
dates its measurements, it never claims certification or savings, it names no
internal host, and every repository file it cites as evidence exists.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "templates" / "demos.html.j2"
BASE_TEMPLATE = REPO_ROOT / "templates" / "base.html.j2"
REBUILD = REPO_ROOT / "tools" / "rebuild_local.py"
REPO_BLOB = "https://github.com/First-AI-Movers/articles/blob/main/"


@pytest.fixture(scope="module")
def page() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def test_the_page_is_built_and_in_the_primary_navigation():
    assert '_render("demos.html.j2", "demos/index.html")' in REBUILD.read_text(encoding="utf-8")
    assert 'href="{{ rel_root }}demos/"' in BASE_TEMPLATE.read_text(encoding="utf-8")


def test_the_page_reaches_all_three_experiences(page):
    assert 'href="{{ rel_root }}ask/"' in page
    assert 'href="{{ rel_root }}assess/"' in page
    assert "https://articles-api.firstaimovers.com/mcp" in page


def test_the_page_says_no_model_is_called(page):
    assert "no ai model is called" in page.lower()


def test_measurements_are_dated_and_labelled_as_single_runs(page):
    assert "Measured on 13 November 2026" in page
    assert "single runs" in page


def test_the_page_offers_plain_services_and_contact_links(page):
    assert 'href="https://www.firstaimovers.com/services"' in page
    assert 'href="https://www.firstaimovers.com/contact"' in page


@pytest.mark.parametrize(
    "claim",
    [r"\bcertif(ied|ication) (by|for)\b", r"\bguarantee", r"\bcompliant\b", r"\bsav(e|es|ings) \d", r"\d+\s?% (faster|cheaper|saving)"],
)
def test_no_certification_guarantee_or_savings_claim(page, claim):
    assert not re.search(claim, page, re.IGNORECASE), f"unsupported claim matched {claim!r}"


def test_no_internal_host_or_machine_path_is_named(page):
    for leak in ("at-dev", "Dev01", "/home/", "localhost", "127.0.0.1"):
        assert leak not in page, f"internal detail {leak!r} on a public page"


def test_every_cited_repository_file_exists(page):
    cited = re.findall(re.escape(REPO_BLOB) + r'([^"#]+)', page)
    assert cited, "the page cites no evidence files"
    missing = [path for path in cited if not (REPO_ROOT / path).is_file()]
    assert missing == [], f"the page cites files that do not exist: {missing}"
