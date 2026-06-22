"""MCP Server C: Mining News & Investment Intelligence.

Provides tools for searching mining news, topic summaries, investment
indicators, and recent headlines.

Usage:
    python -m server_c_mining_news.server
"""

from mcp.server.fastmcp import FastMCP

from .data_loader import (
    get_investment_indicators as _get_investment_indicators,
    get_topic_summary as _get_topic_summary,
    list_recent_headlines as _list_recent_headlines,
    search_news as _search_news,
)

mcp = FastMCP("mining-news")


@mcp.tool()
def search_news(query: str, limit: int = 10) -> list[dict]:
    """Search recent mining news articles by keyword query.

    Args:
        query: Search keyword(s) (e.g. "lithium Pilbara", "spodumene price", "EV battery")
        limit: Maximum number of results (default 10)

    Returns:
        List of {title, date, source, url, snippet, sentiment} articles
    """
    return _search_news(query, limit)


@mcp.tool()
def get_topic_summary(topic: str) -> dict:
    """Get an aggregated news summary and sentiment for a mining topic.

    Args:
        topic: Topic identifier (e.g. "Pilbara", "spodumene", "lithium", "EV")

    Returns:
        dict with topic, article_count, overall_sentiment, sentiment_distribution,
        key_events, last_updated
    """
    return _get_topic_summary(topic)


@mcp.tool()
def get_investment_indicators(region: str = "Pilbara") -> dict:
    """Get investment sentiment, key catalysts, risks, and recommendation for a mining region.

    Args:
        region: Mining region name (default "Pilbara")

    Returns:
        dict with sentiment_score, key_catalysts[], key_risks[], recommendation_summary
    """
    return _get_investment_indicators(region)


@mcp.tool()
def list_recent_headlines(region: str, days: int = 7) -> list[dict]:
    """List recent mining headlines for a specific region.

    Args:
        region: Mining region name (e.g. "Pilbara", "Goldfields")
        days: Number of days back (default 7)

    Returns:
        List of {title, date, source, sentiment} headlines
    """
    return _list_recent_headlines(region, days)


if __name__ == "__main__":
    mcp.run()
