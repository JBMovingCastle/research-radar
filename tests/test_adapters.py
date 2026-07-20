from __future__ import annotations

import datetime as dt
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from research_radar.adapters.arxiv import ArxivAdapter
from research_radar.adapters.base import AdapterContext
from research_radar.adapters.crossref import CrossrefAdapter
from research_radar.adapters.feeds import FeedAdapter
from research_radar.adapters.openalex import OpenAlexAdapter
from research_radar.adapters.semantic_scholar import SemanticScholarRecommendationsAdapter
from research_radar.adapters.webpage import WebPageAdapter
from research_radar.http import HttpResponse


FIXTURES = Path(__file__).parent / "fixtures"


class FakeHttp:
    def __init__(self, *, json_payload=None, body: bytes = b""):
        self.json_payload = json_payload or {}
        self.body = body
        self.request_count = 0
        self.last_post = None
        self.urls = []

    def get_json(self, url, *, headers=None):
        self.request_count += 1
        self.urls.append(url)
        return self.json_payload

    def post_json(self, url, payload, *, headers=None):
        self.request_count += 1
        self.urls.append(url)
        self.last_post = payload
        return self.json_payload

    def request(self, url, **kwargs):
        self.request_count += 1
        self.urls.append(url)
        return HttpResponse(self.body, 200, {})


def context(config, http):
    return AdapterContext(config, dt.date(2026, 7, 21), dt.date(2026, 6, 21), "human_robot_collaboration", ["modular construction human robot collaboration"], http)


class AdapterTests(unittest.TestCase):
    def test_crossref_normalizes_fixture(self) -> None:
        payload = json.loads((FIXTURES / "crossref.json").read_text(encoding="utf-8"))
        config = {"sources": {"crossref": {"enabled": True}}, "selection": {"venue_mode": "prefer"}, "target_sources": []}
        result = CrossrefAdapter().collect(context(config, FakeHttp(json_payload=payload)))
        self.assertEqual(result.status, "success")
        self.assertEqual(result.items[0].doi, "10.1000/example")
        self.assertEqual(result.items[0].venue, "Automation in Construction")

    def test_crossref_uses_configured_author_orcid(self) -> None:
        config = {
            "sources": {"crossref": {"enabled": True}},
            "selection": {"venue_mode": "prefer"},
            "target_sources": [],
            "authors": [{"name": "Ada Example", "orcid": "0000-0000-0000-0001"}],
        }
        fake = FakeHttp(json_payload={"message": {"items": []}})
        CrossrefAdapter().collect(context(config, fake))
        self.assertTrue(any("query.author=Ada+Example" in url and "orcid%3A0000-0000-0000-0001" in url for url in fake.urls))

    def test_arxiv_parses_atom_fixture(self) -> None:
        body = (FIXTURES / "arxiv.xml").read_bytes()
        config = {"sources": {"arxiv": {"enabled": True, "categories": []}}}
        result = ArxivAdapter().collect(context(config, FakeHttp(body=body)))
        self.assertEqual(result.status, "success")
        self.assertEqual(result.items[0].arxiv_id, "2607.00001v1")
        self.assertTrue(result.items[0].full_text_url.endswith("2607.00001v1"))

    def test_recommendations_skip_without_positive_seed(self) -> None:
        config = {"sources": {"semantic_scholar": {"enabled": True, "recommendations_enabled": True}}, "seed_papers": {"positive": [], "negative": []}}
        result = SemanticScholarRecommendationsAdapter().collect(context(config, FakeHttp()))
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.requests, 0)

    def test_recommendations_send_positive_and_negative_seeds(self) -> None:
        config = {"sources": {"semantic_scholar": {"enabled": True, "recommendations_enabled": True}}, "seed_papers": {"positive": ["DOI:10.1/a"], "negative": ["DOI:10.1/b"]}}
        fake = FakeHttp(json_payload={"recommendedPapers": []})
        result = SemanticScholarRecommendationsAdapter().collect(context(config, fake))
        self.assertEqual(result.status, "success")
        self.assertEqual(fake.last_post["positivePaperIds"], ["DOI:10.1/a"])
        self.assertEqual(fake.last_post["negativePaperIds"], ["DOI:10.1/b"])

    def test_openalex_requires_key_when_enabled(self) -> None:
        config = {"sources": {"openalex": {"enabled": True, "api_key_env": "OPENALEX_API_KEY"}}}
        with mock.patch.dict(os.environ, {}, clear=True):
            result = OpenAlexAdapter().collect(context(config, FakeHttp()))
        self.assertEqual(result.status, "misconfigured")

    def test_openalex_uses_configured_author_id(self) -> None:
        config = {
            "sources": {"openalex": {"enabled": True, "api_key_env": "OPENALEX_API_KEY"}},
            "selection": {"venue_mode": "prefer"},
            "target_sources": [],
            "authors": [{"name": "Ada Example", "openalex_id": "A123"}],
        }
        fake = FakeHttp(json_payload={"results": []})
        with mock.patch.dict(os.environ, {"OPENALEX_API_KEY": "test-key"}, clear=True):
            result = OpenAlexAdapter().collect(context(config, fake))
        self.assertEqual(result.status, "success")
        self.assertTrue(any("authorships.author.id%3AA123" in url for url in fake.urls))

    def test_feed_and_webpage_are_independently_configurable(self) -> None:
        feed_config = {"sources": {"feeds": [{"name": "Journal", "url": "https://example.org/feed", "max_items": 5}]}}
        feed = FeedAdapter().collect(context(feed_config, FakeHttp(body=(FIXTURES / "feed.xml").read_bytes())))
        self.assertEqual(feed.status, "success")
        self.assertEqual(feed.items[0].evidence_level, "feed-summary")
        page_config = {"sources": {"web_pages": [{"name": "Agency", "url": "https://example.org/root/", "max_items": 5}]}}
        page = WebPageAdapter().collect(context(page_config, FakeHttp(body=(FIXTURES / "page.html").read_bytes())))
        self.assertEqual(page.status, "success")
        self.assertEqual(page.items[0].evidence_level, "webpage-link")
        self.assertEqual(page.items[0].url, "https://example.org/reports/modular-construction")


if __name__ == "__main__":
    unittest.main()
