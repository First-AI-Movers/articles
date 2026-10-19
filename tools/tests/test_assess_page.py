#!/usr/bin/env python3
"""Tests for the seven-question workflow assessment page (#508 §5).

The page makes three public promises that are cheap to break by accident and
expensive to break in public: it runs entirely in the browser, it mirrors the
published article rather than a method invented here, and it never claims more
than a provisional recommendation.

These are asserted against the source files rather than a rendered site, so the
suite stays offline and fails in `test` rather than only in the browser e2e run.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "templates" / "assess.html.j2"
SCRIPT = REPO_ROOT / "static" / "assess.js"
BASE_TEMPLATE = REPO_ROOT / "templates" / "base.html.j2"
REBUILD = REPO_ROOT / "tools" / "rebuild_local.py"
ARTICLE = (
    REPO_ROOT / "articles"
    / "2026-09-27-before-you-automate-a-workflow-7-questions"
    / "article.md"
)

VERDICTS = ("BUILD", "REPAIR_FIRST", "DEFER", "STOP")

# Call shapes that would send data off the device or persist it. Matched against
# the script with comments and strings removed, so prose describing the absence
# (which the file deliberately contains) can never satisfy or defeat the check.
FORBIDDEN_CALLS = (
    "fetch",
    "XMLHttpRequest",
    "sendBeacon",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "WebSocket",
    "EventSource",
    "document.cookie",
    "importScripts",
)

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"(?<![:/])//[^\n]*")
_STRING = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"")


def _code_only(text: str) -> str:
    """`text` with comments and string literals removed."""
    text = _BLOCK_COMMENT.sub(" ", text)
    text = _LINE_COMMENT.sub(" ", text)
    return _STRING.sub("''", text)


@pytest.fixture(scope="module")
def script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def template() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def test_the_assessment_makes_no_network_or_storage_call(script):
    """The page promises every answer stays in the browser. Hold it to that.

    This is the assertion that matters most on a public page: a visitor is told
    their workflow description never leaves the device, and the only thing
    keeping that true is that the file contains no call which could send it.
    """
    code = _code_only(script)
    offenders = sorted({name for name in FORBIDDEN_CALLS if name in code})
    assert not offenders, (
        f"static/assess.js now references {offenders}. The /assess/ page tells "
        f"visitors their answers never leave the browser and that nothing is "
        f"stored. Either remove the call or change the page's stated promise "
        f"first — the text and the code must not disagree."
    )


def test_the_form_declares_no_submission_target(template):
    """A form with an action would post the answers somewhere on submit."""
    form = re.search(r"<form[^>]*id=\"assess-form\"[^>]*>", template)
    assert form, "the assessment form is missing"
    assert "action=" not in form.group(0), (
        "the assessment form declares an action, which would submit answers off-device"
    )
    assert "method=" not in form.group(0), "the assessment form declares a submit method"


def test_all_seven_questions_are_present_in_order(template):
    """Seven questions, numbered 1..7, each as its own fieldset."""
    numbers = re.findall(r"<fieldset[^>]*data-q=\"(\d)\"", template)
    assert numbers == [str(n) for n in range(1, 8)], (
        f"expected fieldsets data-q=1..7 in order, found {numbers}"
    )


def test_the_six_scored_questions_each_offer_three_options(template):
    """Questions 1-6 are scored; question 7 is where the human records the verdict."""
    for n in range(1, 7):
        options = re.findall(rf"<input type=\"radio\" name=\"q{n}\" value=\"([a-z_]+)\"", template)
        assert len(options) == 3, f"question {n} offers {len(options)} options, expected 3"
        assert len(set(options)) == 3, f"question {n} has duplicate option values: {options}"


def test_every_option_value_is_handled_by_the_verdict_rules(template, script):
    """An option the script never reads would silently do nothing when selected."""
    code = _code_only(script)
    for n in range(1, 7):
        for value in re.findall(rf"name=\"q{n}\" value=\"([a-z_]+)\"", template):
            assert f"{value}:" in code or f"'{value}'" in script, (
                f"option q{n}={value!r} is offered by the form but never read by assess.js"
            )


def test_the_four_article_verdicts_and_an_abstention_exist(script):
    """The article's four verdicts, plus the honest 'not enough answered' case."""
    for verdict in VERDICTS:
        assert f"{verdict}:" in script or f"'{verdict}'" in script, (
            f"verdict {verdict} is missing from assess.js"
        )
    assert "INSUFFICIENT_EVIDENCE" in script, (
        "the page must be able to abstain rather than force a verdict (#508 §5)"
    )


def test_the_verdicts_match_the_published_article(script):
    """The method is the published one, not a variant invented in this repo."""
    assert ARTICLE.exists(), "the source article is missing; the page cites it as its method"
    article = ARTICLE.read_text(encoding="utf-8")
    for verdict in VERDICTS:
        # The article escapes the underscore for Markdown: REPAIR\_FIRST.
        assert verdict.replace("_", r"\_") in article or verdict in article, (
            f"verdict {verdict} does not appear in the source article"
        )


def test_the_recommendation_is_presented_as_provisional(template):
    """#508 §5: the recommendation is explicitly provisional, never advice."""
    lowered = template.lower()
    assert "provisional" in lowered, "the page must mark its recommendation provisional"
    assert "not advice" in lowered or "not a" in lowered, (
        "the page must disclaim advice/audit/certification status"
    )


# Affirmative claim shapes only. The page is REQUIRED to contain the words
# "certification" and "savings" in its disclaimers ("not advice, an audit, or any
# form of certification"), so a bare substring check would forbid the very text
# #508 asks for. These patterns match the claim, never its denial.
CLAIM_PATTERNS = (
    r"\b(?:is|are|fully)\s+certified\b",
    r"\bwe\s+guarantee\b",
    r"\bguarantees?\s+(?:that|you|your|a)\b",
    r"\bensures?\s+compliance\b",
    r"\b(?:is|are)\s+compliant\s+with\b",
    r"\bcertified\s+(?:under|by|against)\b",
)

# A measured-savings claim: a number next to a saving/reduction word.
SAVINGS_PATTERNS = (
    r"\d+\s*%[^.]{0,40}\b(?:sav|reduc|faster|cheaper)",
    r"\b(?:sav|reduc)[a-z]*[^.]{0,40}\d+\s*(?:%|hours?|minutes?|days?|€|\$)",
)


def test_no_certification_or_compliance_claim_is_made(template):
    """#508 §5: no regulatory or compliance certification claim.

    Denials are expected and required; only affirmative claims are forbidden.
    """
    lowered = template.lower()
    for pattern in CLAIM_PATTERNS:
        match = re.search(pattern, lowered)
        assert match is None, (
            f"the assessment page appears to claim {match.group(0)!r}; it is a "
            f"structured aid to judgement, not an audit or a certification"
        )


def test_no_measured_savings_claim_is_made(template):
    """#508 §5: do not invent measured savings. The baseline is the reader's to measure."""
    lowered = template.lower()
    for pattern in SAVINGS_PATTERNS:
        match = re.search(pattern, lowered)
        assert match is None, (
            f"the assessment page appears to quantify a saving ({match.group(0)!r}). "
            f"The article is explicit that the baseline must be measured by the reader; "
            f"this page cannot measure it."
        )


def test_the_page_states_that_nothing_leaves_the_device(template):
    """The promise the network guard above protects must actually be made to the visitor."""
    lowered = template.lower()
    assert "browser" in lowered, "the page must say the assessment runs in the browser"
    assert "stores nothing" in lowered or "no network" in lowered, (
        "the page must state plainly that it stores nothing and makes no network request"
    )


def test_the_page_is_wired_into_the_site_build_and_navigation():
    """A page nobody builds or links to is not delivered."""
    rebuild = REBUILD.read_text(encoding="utf-8")
    assert '_render("assess.html.j2", "assess/index.html")' in rebuild, (
        "tools/rebuild_local.py does not render the assessment page"
    )
    base = BASE_TEMPLATE.read_text(encoding="utf-8")
    assert "assess/" in base, "the primary navigation does not link to the assessment"


def test_the_page_links_back_to_the_article_it_implements(template):
    """A visitor must be able to reach the reasoning behind the questions."""
    assert "before-you-automate-a-workflow-7-questions" in template, (
        "the page must link to the article whose method it applies"
    )
