"""Tests for MCP Server B: Commodity Price."""

import json
import pytest

from .data_loader import (
    get_current_price,
    get_price_forecast,
    get_price_history,
    list_materials,
)


class TestPriceDataLoader:

    def test_get_current_price_spodumene(self):
        result = get_current_price("spodumene_6pct")
        assert "error" not in result
        assert result["material"] == "spodumene_6pct"
        assert result["price"] > 500
        assert result["unit"] == "USD_per_tonne_CIF_China"
        assert "date" in result
        assert "change_pct_mom" in result

    def test_get_current_price_alias(self):
        """Test that aliases work."""
        result = get_current_price("spodumene")
        assert "error" not in result
        assert result["price"] > 500

    def test_get_current_price_carbonate(self):
        result = get_current_price("lithium_carbonate")
        assert "error" not in result
        assert result["unit"] == "CNY_per_tonne"
        assert result["price"] > 50000

    def test_get_current_price_hydroxide(self):
        result = get_current_price("lithium_hydroxide")
        assert "error" not in result
        assert result["price"] > 50000

    def test_get_current_price_unknown(self):
        result = get_current_price("nonexistent_material")
        assert "error" in result

    def test_get_price_history(self):
        history = get_price_history("spodumene_6pct", months=6)
        assert len(history) <= 6
        assert len(history) >= 1
        for entry in history:
            assert "date" in entry
            assert "price" in entry
            assert entry["price"] > 0

    def test_get_price_history_default_months(self):
        history = get_price_history("spodumene_6pct")
        assert len(history) <= 12

    def test_get_price_forecast(self):
        forecast = get_price_forecast("spodumene_6pct")
        assert "error" not in forecast
        assert "forecast_6m" in forecast
        assert "forecast_12m" in forecast
        assert forecast["forecast_12m"] > forecast["forecast_6m"]  # upward trend expected

    def test_list_materials(self):
        materials = list_materials()
        assert len(materials) >= 3
        names = [m["material_name"] for m in materials]
        assert "spodumene_6pct" in names
        assert "lithium_carbonate" in names
        assert "lithium_hydroxide" in names
        for m in materials:
            assert "current_price" in m
            assert "unit" in m

    def test_data_files_loadable(self):
        import pathlib
        data_dir = pathlib.Path(__file__).resolve().parent.parent / "shared_data" / "prices"
        json_files = list(data_dir.glob("*.json"))
        assert len(json_files) >= 3

        for f in json_files:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            assert "material" in data
            assert "data" in data
            assert len(data["data"]) > 0
