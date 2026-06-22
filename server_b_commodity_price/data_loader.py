"""Data loader for Commodity Price Server.

Reads curated price data from shared_data/prices/ JSON files.
"""

import json
from pathlib import Path
from typing import Optional

_SHARED_DATA_DIR = Path(__file__).resolve().parent.parent / "shared_data" / "prices"

_prices_cache: dict[str, dict] = {}


def _load_material(material: str) -> Optional[dict]:
    """Load price data for a specific material. Results cached in memory."""
    if material in _prices_cache:
        return _prices_cache[material]

    # Normalize material name to filename
    filename_map = {
        "spodumene_6pct": "spodumene_6pct.json",
        "spodumene": "spodumene_6pct.json",
        "sc6": "spodumene_6pct.json",
        "lithium_carbonate": "lithium_carbonate.json",
        "carbonate": "lithium_carbonate.json",
        "li2co3": "lithium_carbonate.json",
        "lithium_hydroxide": "lithium_hydroxide.json",
        "hydroxide": "lithium_hydroxide.json",
        "lioh": "lithium_hydroxide.json",
    }

    filename = filename_map.get(material.lower(), f"{material}.json")
    filepath = _SHARED_DATA_DIR / filename

    if not filepath.exists():
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    _prices_cache[material] = data
    return data


def get_current_price(material: str) -> dict:
    """Get the most recent price point for a material."""
    data = _load_material(material)
    if not data:
        return {"error": f"Material not found: {material}", "available_materials": list_materials_names()}

    latest = data["data"][-1]
    # Calculate month-over-month change
    if len(data["data"]) >= 2:
        prev = data["data"][-2]
        change_pct = round((latest["price"] - prev["price"]) / prev["price"] * 100, 2)
    else:
        change_pct = 0.0

    return {
        "material": data["material"],
        "description": data.get("description", ""),
        "price": latest["price"],
        "unit": data["unit"],
        "date": latest["date"],
        "change_pct_mom": change_pct,
        "source": data.get("source", "curated_sample"),
    }


def get_price_history(material: str, months: int = 12) -> list[dict]:
    """Get monthly price history for a material."""
    data = _load_material(material)
    if not data:
        return []

    return data["data"][-months:]


def get_price_forecast(material: str) -> dict:
    """Get 6-12 month price forecast from analyst consensus."""
    data = _load_material(material)
    if not data or "forecast" not in data:
        return {"error": f"No forecast available for {material}"}

    forecast = data["forecast"]
    return {
        "material": data["material"],
        "unit": data["unit"],
        "forecast_6m": forecast.get("6m_consensus_usd") or forecast.get("6m_consensus_cny"),
        "forecast_12m": forecast.get("12m_consensus_usd") or forecast.get("12m_consensus_cny"),
        "source": forecast.get("source", "curated_analyst_consensus"),
        "sentiment": forecast.get("analyst_sentiment", "neutral"),
    }


def list_materials() -> list[dict]:
    """List all tracked battery materials with latest prices."""
    materials = []
    for json_file in _SHARED_DATA_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        latest = data["data"][-1]
        materials.append({
            "material_name": data["material"],
            "description": data.get("description", ""),
            "unit": data["unit"],
            "current_price": latest["price"],
            "last_updated": latest["date"],
        })
    return materials


def list_materials_names() -> list[str]:
    """List available material identifier strings."""
    return [
        "spodumene_6pct (or 'sc6', 'spodumene')",
        "lithium_carbonate (or 'carbonate')",
        "lithium_hydroxide (or 'hydroxide')",
    ]
