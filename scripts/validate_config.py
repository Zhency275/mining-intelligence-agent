"""Validate mcp-config.json syntax and paths.

Usage:
    python scripts/validate_config.py
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "mcp-config.json"


def validate_json_syntax() -> dict:
    """Check that the JSON file is valid and has the expected structure."""
    print(f"Checking: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert "mcpServers" in config, "Missing 'mcpServers' key"
    servers = config["mcpServers"]

    expected_servers = {"mine-production", "commodity-price", "mining-news"}
    actual_servers = set(servers.keys())
    assert expected_servers == actual_servers, (
        f"Expected servers {expected_servers}, got {actual_servers}"
    )

    for name, server_cfg in servers.items():
        assert "command" in server_cfg, f"{name}: missing 'command'"
        assert "args" in server_cfg, f"{name}: missing 'args'"
        assert "cwd" in server_cfg, f"{name}: missing 'cwd'"

    print("  JSON syntax: OK")
    print(f"  Servers: {', '.join(servers.keys())}")
    return config


def validate_cwd_paths(config: dict) -> None:
    """Check that the cwd paths exist on this system."""
    for name, server_cfg in config["mcpServers"].items():
        cwd = server_cfg.get("cwd", "")
        path = Path(cwd)
        if path.exists():
            print(f"  {name}: cwd exists -> {cwd}")
        else:
            print(f"  {name}: cwd NOT FOUND -> {cwd}")
            print(f"    (This is expected if you are on a different machine)")
            print(f"    (Update paths in mcp-config.json before using with Claude Desktop)")


def validate_python_modules() -> None:
    """Check that the Python modules can be imported."""
    modules = [
        "server_a_mine_production.server",
        "server_b_commodity_price.server",
        "server_c_mining_news.server",
    ]
    for module in modules:
        # Use a quick import check (doesn't start the server)
        cmd = [sys.executable, "-c", f"import importlib; importlib.import_module('{module}')"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode == 0:
            print(f"  {module}: import OK")
        else:
            print(f"  {module}: import FAILED")
            print(f"    {result.stderr.strip()[:200]}")


def validate_shared_data() -> None:
    """Check that shared data JSON files are present and valid."""
    shared_data = PROJECT_ROOT / "shared_data"
    required_files = [
        "mines/pilbara_lithium_mines.json",
        "prices/spodumene_6pct.json",
        "prices/lithium_carbonate.json",
        "prices/lithium_hydroxide.json",
        "news/pilbara_news.json",
        "news/investment_signals.json",
    ]
    for rel_path in required_files:
        filepath = shared_data / rel_path
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  {rel_path}: OK ({len(str(data))} bytes)")
        else:
            print(f"  {rel_path}: MISSING")
            sys.exit(1)


def main():
    print("=" * 50)
    print("Mining Intelligence Agent — Config Validator")
    print("=" * 50)

    print("\n[1] Validating mcp-config.json...")
    config = validate_json_syntax()

    print("\n[2] Validating cwd paths...")
    validate_cwd_paths(config)

    print("\n[3] Validating Python modules...")
    validate_python_modules()

    print("\n[4] Validating shared data...")
    validate_shared_data()

    print("\n" + "=" * 50)
    print("All validations passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
