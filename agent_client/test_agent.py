"""Integration tests for the Agent Client (requires ANTHROPIC_API_KEY)."""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestAgentComponents:
    """Test agent components that don't require real API calls."""

    def test_system_prompt_loads(self):
        from agent_client.system_prompt import SYSTEM_PROMPT, SYSTEM_PROMPT_COMPACT
        assert len(SYSTEM_PROMPT) > 500
        assert "mine_production" in SYSTEM_PROMPT
        assert "commodity_price" in SYSTEM_PROMPT
        assert "mining_news" in SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT_COMPACT) > 100

    def test_mcp_manager_config(self):
        from agent_client.mcp_client_manager import MCPClientManager
        manager = MCPClientManager()
        assert len(manager.servers) == 3
        server_names = [s.name for s in manager.servers]
        assert "mine_production" in server_names
        assert "commodity_price" in server_names
        assert "mining_news" in server_names

    def test_agent_init_requires_api_key(self):
        from agent_client.agent import MiningIntelligenceAgent
        import os

        # Save original env value
        saved_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            # Passing None and no env var should raise
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                MiningIntelligenceAgent(api_key=None)
            # Empty string should also raise
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                MiningIntelligenceAgent(api_key="")
        finally:
            # Restore
            if saved_key:
                os.environ["ANTHROPIC_API_KEY"] = saved_key

    def test_agent_init_with_key(self):
        from agent_client.agent import MiningIntelligenceAgent
        agent = MiningIntelligenceAgent(api_key="sk-ant-test-key")
        assert agent.model == "claude-sonnet-4-20250514"

    def test_main_cli_help(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "agent_client.main", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        assert result.returncode == 0
        assert result.stdout is not None


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY to be set for live agent test",
)
class TestAgentLive:
    """Live tests that make real API calls. Skipped without API key."""

    @pytest.mark.asyncio
    async def test_agent_run_short_query(self):
        from agent_client.agent import MiningIntelligenceAgent
        agent = MiningIntelligenceAgent(verbose=True)
        report = await agent.run(
            "Briefly: what is the current price of spodumene?"
        )
        assert len(report) > 50
        # Should contain a price number
        assert any(
            word in report.lower()
            for word in ["spodumene", "price", "usd", "tonne"]
        ), f"Report doesn't contain expected keywords: {report[:200]}"

    @pytest.mark.asyncio
    async def test_agent_run_pilbara_briefing(self):
        from agent_client.agent import MiningIntelligenceAgent
        agent = MiningIntelligenceAgent(verbose=True)
        report = await agent.run("请给我一份关于 Pilbara 锂矿的简报")
        assert len(report) > 200
        # Should mention key mines
        assert any(
            name in report
            for name in ["Pilgangoora", "Wodgina", "Pilbara"]
        ), f"Report doesn't mention key names: {report[:300]}"
