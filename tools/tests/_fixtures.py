#!/usr/bin/env python3
"""Shared test fixtures and constants."""

import json
import re
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest


# =========================================================================
# Fixtures
# =========================================================================

SAMPLE_FRONT_MATTER = """---
title: "Test Article"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
publication: "First AI Movers"
canonical_url: "https://radar.firstaimovers.com/test-article"
published_date: "2026-04-01"
license: "CC BY 4.0"
---"""

SAMPLE_ARTICLE = f"""{SAMPLE_FRONT_MATTER}
# Test Article Title

## In 2026, AI strategy is no longer optional.

Most companies still start in the wrong place.

They start with model quality, not review design.

## Model Choice Matters Less

This is the uncomfortable part of the market.

## Conclusion

Review design beats model selection every time.
"""

SAMPLE_ARTICLE_WITH_TLDR = f"""{SAMPLE_FRONT_MATTER}
# Test Article Title

## TL;DR

> Review design matters more than model choice for AI dev stacks in 2026.
> Teams that standardize how AI work gets reviewed outperform those chasing benchmarks.

## In 2026, AI strategy is no longer optional.

Rest of article here.
"""

SAMPLE_ARTICLE_WITH_KEY_TAKEAWAY = f"""{SAMPLE_FRONT_MATTER}
# Test Article Title

## Key Takeaway

Focus on governance before scaling AI agents.

## Introduction

Rest of article here.
"""

SAMPLE_INDEX = {
    "last_updated": "2026-04-05",
    "total_articles": 3,
    "author": "Dr. Hernani Costa",
    "publication": "First AI Movers",
    "canonical_base": "https://radar.firstaimovers.com",
    "license": "CC BY 4.0",
    "articles": [
        {
            "folder": "2026-04-04-test-article-one",
            "slug": "test-article-one",
            "title": "Test Article One",
            "published_date": "2026-04-04",
            "tags": ["AI strategy", "EU AI Act"],
            "funnel_stage": "top",
            "canonical_url": "https://radar.firstaimovers.com/test-one",
        },
        {
            "folder": "2026-03-15-test-article-two",
            "slug": "test-article-two",
            "title": "Test Article Two",
            "published_date": "2026-03-15",
            "tags": ["AI governance", "MCP"],
            "funnel_stage": "middle",
            "canonical_url": "https://radar.firstaimovers.com/test-two",
        },
        {
            "folder": "2025-06-01-test-article-three",
            "slug": "test-article-three",
            "title": "Test Article Three",
            "published_date": "2025-06-01",
            "tags": ["AI strategy"],
            "funnel_stage": "bottom",
            "canonical_url": "https://insights.firstaimovers.com/test-three",
        },
    ],
}

SAMPLE_README = """<!-- machine-readable metadata for LLM indexing
{
  "@context": "https://schema.org",
  "@type": "CreativeWorkSeries",
  "name": "First AI Movers — Article Archive",
  "description": "The canonical, open-access article archive of First AI Movers: 648 original articles on AI strategy, EU AI Act compliance, AI governance, agentic systems, and responsible AI adoption for European SMEs. Written by Dr. Hernani Costa, PhD.",
  "dateCreated": "2025-02-17",
  "dateModified": "2026-04-05"
}
-->

# First AI Movers — Article Archive

[![Articles](https://img.shields.io/badge/Articles-648-orange.svg)](#what-is-in-this-archive)

> The canonical, open-access text archive of every article published by [First AI Movers](https://firstaimovers.com) — 648 original articles on AI strategy, EU AI Act compliance, AI governance, and responsible AI adoption for European businesses.

## What Is in This Archive?

This repository contains the full-text, machine-readable versions of 648 original articles spanning February 2025–April 2026.

    └── ... (648 article folders)

**Quick stats:**
- **648** articles indexed
- **3,147** unique topic tags
- **3 funnel stages:** top (221 articles), middle (423), bottom (4)
- **Date range:** February 17, 2025 – April 4, 2026
"""

SAMPLE_LLMS_TXT = """> The canonical, open-access text archive of all First AI Movers articles by Dr. Hernani Costa. 648 original articles on AI strategy. Published February 2025–April 2026.
"""


# =========================================================================
# Tests: rebuild_index.py logic
# =========================================================================
