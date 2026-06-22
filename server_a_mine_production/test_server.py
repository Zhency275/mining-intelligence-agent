"""Tests for MCP Server A: Mine Production."""

import json
import pytest

from .data_loader import (
    get_mine_by_name,
    get_production_trend,
    list_mines_by_region,
    search_mines,
)


class TestMineDataLoader:
    """Test the data loader functions directly (no MCP server needed)."""

    def test_get_mine_by_name_found(self):
        """Test looking up a known mine by name."""
        mine = get_mine_by_name("Pilgangoora")
        assert mine is not None
        assert mine["mine_name"] == "Pilgangoora"
        assert mine["operator"] == "Pilbara Minerals Ltd (PLS.ASX)"
        assert "reserves_tonnes" in mine
        assert mine["reserves_tonnes"] > 0

    def test_get_mine_by_name_case_insensitive(self):
        """Test case-insensitive lookup."""
        mine = get_mine_by_name("pilgangoora")
        assert mine is not None
        assert "Pilgangoora" in mine["mine_name"]

    def test_get_mine_by_name_partial(self):
        """Test partial name match."""
        mine = get_mine_by_name("Kathleen")
        assert mine is not None
        assert "Kathleen Valley" in mine["mine_name"]

    def test_get_mine_by_name_not_found(self):
        """Test looking up a nonexistent mine."""
        mine = get_mine_by_name("NonExistentMine")
        assert mine is None

    def test_list_mines_by_region_pilbara(self):
        """Test listing mines in Pilbara region."""
        mines = list_mines_by_region("Pilbara")
        assert len(mines) >= 2  # Pilgangoora, Wodgina
        mine_names = [m["mine_name"] for m in mines]
        assert "Pilgangoora" in mine_names
        assert "Wodgina" in mine_names

    def test_list_mines_by_region_goldfields(self):
        """Test listing mines in Goldfields region."""
        mines = list_mines_by_region("Goldfields")
        assert len(mines) >= 2  # Mt Marion, Kathleen Valley
        mine_names = [m["mine_name"] for m in mines]
        assert "Mt Marion" in mine_names
        assert "Kathleen Valley" in mine_names

    def test_list_mines_summary_schema(self):
        """Test that summarized mines have the correct schema."""
        mines = list_mines_by_region("Pilbara")
        for mine in mines:
            assert "mine_name" in mine
            assert "operator" in mine
            assert "status" in mine
            assert "annual_production_tonnes" in mine
            assert "products" in mine

    def test_search_mines_lithium(self):
        """Test searching for lithium mines."""
        results = search_mines(commodity="lithium", country="Australia")
        assert len(results) >= 5
        assert all(r["country"] == "Australia" for r in results)

    def test_get_production_trend(self):
        """Test getting production trend data."""
        trend = get_production_trend("Pilgangoora", years=3)
        assert len(trend) <= 3
        assert len(trend) >= 1
        for entry in trend:
            assert "year" in entry
            assert "production_tonnes" in entry
            assert entry["production_tonnes"] > 0

    def test_get_production_trend_unknown_mine(self):
        """Test production trend for unknown mine returns empty list."""
        trend = get_production_trend("NoSuchMine")
        assert trend == []

    def test_data_files_loadable(self):
        """Test that all mine data JSON files are valid and loadable."""
        import pathlib
        data_dir = pathlib.Path(__file__).resolve().parent.parent / "shared_data" / "mines"
        json_files = list(data_dir.glob("*.json"))
        assert len(json_files) > 0, "No JSON data files found"

        for f in json_files:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            assert isinstance(data, (list, dict)), f"Invalid data format in {f.name}"
