"""MCP Server B: Commodity Price & Market Intelligence.

Provides tools for querying battery mineral prices, historical trends,
price forecasts, and listing tracked materials.

Usage:
    python -m server_b_commodity_price.server
"""

from mcp.server.fastmcp import FastMCP

from .data_loader import (
    get_current_price as _get_current_price,
    get_price_forecast as _get_price_forecast,
    get_price_history as _get_price_history,
    list_materials as _list_materials,
)

mcp = FastMCP("commodity-price")


@mcp.tool()
def get_current_price(material: str) -> dict:
    """Get current spot price for a battery material.

    Args:
        material: Material identifier. Options:
            - "spodumene_6pct" (or "sc6", "spodumene")
            - "lithium_carbonate" (or "carbonate")
            - "lithium_hydroxide" (or "hydroxide")

    Returns:
        dict with material, price, unit, date, change_pct_mom (month-over-month %), source
    """
    return _get_current_price(material)


@mcp.tool()
def get_price_history(material: str, months: int = 12) -> list[dict]:
    """Get monthly price history for a battery material.

    Args:
        material: Material identifier ("spodumene_6pct", "lithium_carbonate", "lithium_hydroxide")
        months: Number of months of history (default 12)

    Returns:
        List of {date, price} data points
    """
    return _get_price_history(material, months)


@mcp.tool()
def get_price_forecast(material: str) -> dict:
    """Get 6-12 month price forecast from analyst consensus.

    Args:
        material: Material identifier ("spodumene_6pct", "lithium_carbonate", "lithium_hydroxide")

    Returns:
        dict with forecast_6m, forecast_12m, source, sentiment
    """
    return _get_price_forecast(material)


@mcp.tool()
def list_materials() -> list[dict]:
    """List all tracked battery materials and their current prices.

    Returns:
        List of {material_name, description, unit, current_price, last_updated}
    """
    return _list_materials()


if __name__ == "__main__":
    mcp.run()
