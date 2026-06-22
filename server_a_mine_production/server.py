"""MCP Server A: Mine Production & Reserves Intelligence.

Provides tools for querying lithium mine production data, reserves,
regional listings, and production trends.

Usage:
    python -m server_a_mine_production.server
"""

from mcp.server.fastmcp import FastMCP

from .data_loader import (
    get_mine_by_name as _get_mine_by_name,
    get_production_trend as _get_production_trend,
    list_mines_by_region as _list_mines_by_region,
    search_mines as _search_mines,
)

mcp = FastMCP("mine-production")


@mcp.tool()
def get_mine_overview(mine_name: str) -> dict:
    """Get detailed profile of a lithium mine including production, reserves,
    operator information, and mine type.

    Args:
        mine_name: Name of the mine (e.g. "Pilgangoora", "Wodgina", "Greenbushes")

    Returns:
        dict with keys: mine_name, region, country, operator, owners, status,
        annual_production_tonnes, reserves_tonnes, resources_tonnes, mine_type,
        products, description, source
    """
    mine = _get_mine_by_name(mine_name)
    if not mine:
        return {
            "error": f"Mine not found: {mine_name}",
            "suggestion": "Try search_mines or list_mines_by_region to discover available mines.",
        }
    return mine


@mcp.tool()
def list_mines_by_region(region: str) -> list[dict]:
    """List all lithium mines in a mining region.

    Args:
        region: Mining region name (e.g. "Pilbara", "Goldfields", "Greenbushes")

    Returns:
        List of mine summaries with mine_name, operator, status, production, products
    """
    return _list_mines_by_region(region)


@mcp.tool()
def get_production_trend(mine_name: str, years: int = 3) -> list[dict]:
    """Get annual production trend (tonnes) for a named mine.

    Args:
        mine_name: Name of the mine (e.g. "Pilgangoora")
        years: Number of years of history to return (default 3)

    Returns:
        List of {year, production_tonnes, mine_name, source} dicts
    """
    return _get_production_trend(mine_name, years)


@mcp.tool()
def search_mines(commodity: str = "lithium", country: str = "Australia") -> list[dict]:
    """Search for mines by commodity type and country.

    Args:
        commodity: Commodity to search for (default "lithium")
        country: Country filter (default "Australia")

    Returns:
        Summary list of matching mines
    """
    return _search_mines(commodity, country)


if __name__ == "__main__":
    mcp.run()
