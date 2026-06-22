"""Data loader for Mine Production Server.

Reads curated mine data from shared_data/mines/ JSON files.
"""

import json
from pathlib import Path
from typing import Optional

_SHARED_DATA_DIR = Path(__file__).resolve().parent.parent / "shared_data" / "mines"

# Cache loaded data in memory
_mines_cache: Optional[list[dict]] = None


def _load_mines() -> list[dict]:
    """Load all mine data from JSON files. Results are cached in memory."""
    global _mines_cache
    if _mines_cache is not None:
        return _mines_cache

    mines = []
    for json_file in _SHARED_DATA_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                mines.extend(data)
            else:
                mines.append(data)

    _mines_cache = mines
    return mines


def get_mine_by_name(name: str) -> Optional[dict]:
    """Look up a single mine by normalized name (case-insensitive substring match)."""
    name_lower = name.lower()
    for mine in _load_mines():
        if name_lower in mine.get("mine_name", "").lower():
            return mine
    return None


def list_mines_by_region(region: str) -> list[dict]:
    """Filter mines by region (case-insensitive substring match)."""
    region_lower = region.lower()
    results = []
    for mine in _load_mines():
        if region_lower in mine.get("region", "").lower():
            results.append(_summarize_mine(mine))
    return results


def search_mines(commodity: str = "lithium", country: str = "Australia") -> list[dict]:
    """Search mines by commodity (checks products, description, region) and country."""
    commodity_lower = commodity.lower()
    country_lower = country.lower()

    # Broad matching: map common commodities to keywords found in mine data
    commodity_keywords = {
        "lithium": ["spodumene", "lithium", "li2o"],
    }

    keywords = commodity_keywords.get(commodity_lower, [commodity_lower])

    results = []
    for mine in _load_mines():
        combined = (
            mine.get("region", "").lower() + " "
            + mine.get("description", "").lower() + " "
            + " ".join(p.lower() for p in mine.get("products", []))
        )
        if any(kw in combined for kw in keywords):
            results.append(_summarize_mine(mine))
    # Filter by country
    results = [r for r in results if country_lower in r.get("country", "").lower()]
    return results


def get_production_trend(mine_name: str, years: int = 3) -> list[dict]:
    """Get production trend data for a specific mine."""
    mine = get_mine_by_name(mine_name)
    if not mine:
        return []

    production = mine.get("annual_production_tonnes", {})
    # Sort by year, take the most recent `years` entries
    sorted_years = sorted(production.items(), key=lambda x: x[0])[-years:]

    return [
        {
            "year": y,
            "production_tonnes": v,
            "mine_name": mine["mine_name"],
            "source": mine.get("source", "curated_sample"),
        }
        for y, v in sorted_years
    ]


def _summarize_mine(mine: dict) -> dict:
    """Return a compact summary of a mine for list views."""
    return {
        "mine_name": mine["mine_name"],
        "region": mine["region"],
        "country": mine.get("country", "Australia"),
        "operator": mine["operator"],
        "status": mine["status"],
        "annual_production_tonnes": mine.get("annual_production_tonnes", {}),
        "products": mine.get("products", []),
    }
