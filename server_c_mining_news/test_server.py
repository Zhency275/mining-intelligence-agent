"""Tests for MCP Server C: Mining News."""

import json
import pytest

from .data_loader import (
    get_investment_indicators,
    get_topic_summary,
    list_recent_headlines,
    search_news,
)


class TestNewsDataLoader:

    def test_search_news_lithium(self):
        results = search_news("lithium", limit=10)
        assert len(results) >= 1
        assert len(results) <= 10
        for r in results:
            assert "title" in r
            assert "date" in r
            assert "source" in r
            assert "sentiment" in r

    def test_search_news_pilbara(self):
        results = search_news("Pilbara", limit=5)
        assert len(results) >= 1
        # All results should relate to Pilbara
        for r in results:
            assert "pilbara" in (
                r["title"].lower() + r.get("snippet", "").lower()
            ) or "pilbara" in r.get("snippet", "").lower()

    def test_search_news_limit(self):
        results = search_news("lithium", limit=3)
        assert len(results) <= 3

    def test_search_news_no_results(self):
        results = search_news("zzz_nonexistent_topic_xyz", limit=10)
        assert isinstance(results, list)

    def test_get_topic_summary_pilbara(self):
        summary = get_topic_summary("Pilbara")
        assert "error" not in summary
        assert summary["article_count"] >= 1
        assert "overall_sentiment" in summary
        assert "key_events" in summary
        assert len(summary["key_events"]) >= 1

    def test_get_topic_summary_lithium(self):
        summary = get_topic_summary("lithium")
        assert summary["article_count"] >= 1

    def test_get_investment_indicators(self):
        indicators = get_investment_indicators("Pilbara")
        assert "error" not in indicators
        assert "sentiment_score" in indicators
        assert 1 <= indicators["sentiment_score"] <= 10
        assert "key_catalysts" in indicators
        assert len(indicators["key_catalysts"]) >= 1
        assert "key_risks" in indicators
        assert len(indicators["key_risks"]) >= 1
        assert "recommendation_summary" in indicators

    def test_get_investment_indicators_case_insensitive(self):
        indicators = get_investment_indicators("pilbara")
        assert "error" not in indicators  # Should match case-insensitively

    def test_get_investment_indicators_unknown_region(self):
        result = get_investment_indicators("Antarctica")
        assert "error" in result

    def test_list_recent_headlines(self):
        headlines = list_recent_headlines("Pilbara", days=7)
        assert isinstance(headlines, list)
        for h in headlines:
            assert "title" in h
            assert "date" in h

    def test_data_files_loadable(self):
        import pathlib
        data_dir = pathlib.Path(__file__).resolve().parent.parent / "shared_data" / "news"
        json_files = list(data_dir.glob("*.json"))
        assert len(json_files) >= 2

        for f in json_files:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            assert data is not None
