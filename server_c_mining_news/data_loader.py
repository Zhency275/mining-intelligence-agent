"""Data loader for Mining News Server.

Reads curated news data from shared_data/news/ JSON files.
"""

import json
from pathlib import Path
from typing import Optional

_SHARED_DATA_DIR = Path(__file__).resolve().parent.parent / "shared_data" / "news"

_news_cache: Optional[list[dict]] = None
_signals_cache: Optional[dict] = None


def _load_news() -> list[dict]:
    """Load all news articles from JSON files. Results cached in memory."""
    global _news_cache
    if _news_cache is not None:
        return _news_cache

    articles = []
    for json_file in _SHARED_DATA_DIR.glob("*.json"):
        if json_file.name == "investment_signals.json":
            continue
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                articles.extend(data)

    # Sort by date descending
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)
    _news_cache = articles
    return articles


def _load_investment_signals() -> dict:
    """Load investment signals data."""
    global _signals_cache
    if _signals_cache is not None:
        return _signals_cache

    filepath = _SHARED_DATA_DIR / "investment_signals.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            _signals_cache = json.load(f)
    else:
        _signals_cache = {}
    return _signals_cache


def search_news(query: str, limit: int = 10) -> list[dict]:
    """Search news articles by keyword query (case-insensitive)."""
    query_lower = query.lower()
    results = []
    for article in _load_news():
        searchable = (
            article.get("title", "")
            + " "
            + article.get("snippet", "")
            + " "
            + " ".join(article.get("topics", []))
        ).lower()
        if query_lower in searchable:
            results.append({
                "title": article["title"],
                "date": article["date"],
                "source": article["source"],
                "url": article.get("url", ""),
                "snippet": article.get("snippet", ""),
                "sentiment": article.get("sentiment", "neutral"),
            })
            if len(results) >= limit:
                break
    return results


def get_topic_summary(topic: str) -> dict:
    """Get aggregated news summary and sentiment for a specific topic."""
    topic_lower = topic.lower()
    articles = []
    sentiments = {"positive": 0, "negative": 0, "neutral": 0}

    for article in _load_news():
        if topic_lower in article.get("title", "").lower() or topic_lower in " ".join(article.get("topics", [])).lower():
            articles.append(article)
            sentiments[article.get("sentiment", "neutral")] += 1

    if not articles:
        return {"topic": topic, "message": f"No articles found for topic: {topic}"}

    # Determine overall sentiment
    total = sum(sentiments.values())
    if sentiments["positive"] > sentiments["negative"]:
        overall_sentiment = "positive"
    elif sentiments["negative"] > sentiments["positive"]:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"

    # Generate a simple summary
    key_events = [
        {"title": a["title"], "date": a["date"], "sentiment": a["sentiment"]}
        for a in sorted(articles, key=lambda x: x["date"], reverse=True)[:10]
    ]

    return {
        "topic": topic,
        "article_count": len(articles),
        "overall_sentiment": overall_sentiment,
        "sentiment_distribution": sentiments,
        "key_events": key_events,
        "last_updated": articles[0]["date"] if articles else "unknown",
        "source": "curated_news_sample",
    }


def get_investment_indicators(region: str = "Pilbara") -> dict:
    """Get investment-level intelligence for a mining region."""
    signals = _load_investment_signals()
    summary_key = None

    # Try case-insensitive match
    for key in signals:
        if region.lower() in key.lower():
            summary_key = key
            break

    if not summary_key:
        return {"error": f"No investment data for region: {region}", "available_regions": list(signals.keys())}

    return signals[summary_key]


def list_recent_headlines(region: str, days: int = 7) -> list[dict]:
    """List recent headlines filtered by region and days back."""
    region_lower = region.lower()
    results = []
    for article in _load_news():
        searchable = article.get("title", "") + " " + " ".join(article.get("topics", []))
        if region_lower in searchable.lower():
            results.append({
                "title": article["title"],
                "date": article["date"],
                "source": article["source"],
                "sentiment": article.get("sentiment", "neutral"),
            })
            if len(results) >= 20:
                break
    return results[:20]
