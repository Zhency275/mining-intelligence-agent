"""Mining Intelligence Agent — Hand-written ReAct Loop.

This module implements a ReAct (Reasoning + Acting) agent that:
1. Receives a natural language query about mining/minerals
2. Calls MCP tools across 3 servers to gather data
3. Synthesizes a structured Markdown report

Uses Anthropic API for the LLM with native tool-use support.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic

from .mcp_client_manager import MCPClientManager
from .system_prompt import SYSTEM_PROMPT

# Configuration
MAX_ITERATIONS = 10
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8192

# Path to reports output
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


class MiningIntelligenceAgent:
    """ReAct agent that orchestrates MCP tool calls to produce mining reports."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = MODEL,
        verbose: bool = False,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it in .env file or pass directly."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.verbose = verbose
        self.mcp_manager = MCPClientManager()
        self.messages: list[dict] = []

    async def run(self, query: str) -> str:
        """Execute the full agent pipeline and return the final report.

        Args:
            query: Natural language query (e.g. "请给我一份 Pilbara 锂矿简报")

        Returns:
            Complete Markdown report string
        """
        print(f"\n{'='*60}")
        print(f"Mining Intelligence Agent")
        print(f"Model: {self.model}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")

        # Phase 1: Start all MCP servers and discover tools
        print("[Agent] Starting MCP servers...")
        await self.mcp_manager.start_all()
        tools = self.mcp_manager.get_tools_schema()

        server_tools = self.mcp_manager.get_tool_names_by_server()
        for server, tool_names in server_tools.items():
            print(f"[Agent]   {server}: {', '.join(tool_names)}")

        # Phase 2: ReAct loop
        print("\n[Agent] Beginning analysis...\n")

        # Build initial messages
        self.messages = [
            {"role": "user", "content": query}
        ]

        final_report = ""
        for iteration in range(1, MAX_ITERATIONS + 1):
            if self.verbose:
                print(f"\n--- Iteration {iteration}/{MAX_ITERATIONS} ---")

            response = self.client.messages.create(
                model=self.model,
                system=SYSTEM_PROMPT,
                messages=self.messages,
                tools=tools,
                max_tokens=MAX_TOKENS,
            )

            # Process the response
            if response.stop_reason == "end_turn":
                # Agent is done — extract final report
                for block in response.content:
                    if block.type == "text":
                        final_report = block.text
                        print(f"[Agent] Analysis complete (iterations: {iteration})")
                        break
                break

            elif response.stop_reason == "tool_use":
                # Handle tool calls
                tool_results = []

                for block in response.content:
                    if block.type == "text" and block.text:
                        # Pass through any text content
                        pass
                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = block.id

                        if self.verbose:
                            print(f"  [TOOL] {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:120]})")

                        # Call the MCP tool
                        result_str = await self.mcp_manager.call_tool(tool_name, tool_input)
                        if self.verbose:
                            print(f"  [RESULT] {result_str[:200]}...")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_str,
                        })

                # Append assistant's tool-use message and tool results
                self.messages.append({
                    "role": "assistant",
                    "content": response.content,
                })
                self.messages.append({
                    "role": "user",
                    "content": tool_results,
                })

            else:
                # Unexpected stop reason
                print(f"[Agent] Unexpected stop reason: {response.stop_reason}")
                for block in response.content:
                    if block.type == "text":
                        final_report = block.text
                break

        # Fallback: if we hit max iterations, get whatever text we have
        if not final_report and self.messages:
            # Try to extract text from the last response
            final_report = f"# Mining Intelligence Report\n\n"
            final_report += f"*Report generation exceeded maximum iterations ({MAX_ITERATIONS}).*\n\n"
            final_report += "Partial data has been collected. Please try a more specific query.\n"

        # Phase 3: Shutdown
        print("[Agent] Shutting down MCP servers...")
        await self.mcp_manager.shutdown()

        return final_report

    def save_report(self, report: str, query: str) -> Path:
        """Save the report to the reports/ directory with a timestamped filename."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate a safe filename from query + timestamp
        import re
        safe_query = re.sub(r'[^\w\s-]', '', query[:40]).strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_query}.md"
        filepath = REPORTS_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"<!-- Mining Intelligence Agent Report -->\n")
            f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n")
            f.write(f"<!-- Query: {query} -->\n\n")
            f.write(report)

        print(f"\n[Agent] Report saved to: {filepath}")
        return filepath


async def run_query(
    query: str,
    api_key: str | None = None,
    model: str = MODEL,
    verbose: bool = False,
) -> str:
    """Convenience function: run a single query and return the report.

    Args:
        query: Natural language query
        api_key: Anthropic API key (optional, uses env var if not provided)
        model: Model to use
        verbose: Print detailed progress

    Returns:
        Markdown report string
    """
    agent = MiningIntelligenceAgent(
        api_key=api_key,
        model=model,
        verbose=verbose,
    )
    return await agent.run(query)


# Example usage when run directly
if __name__ == "__main__":
    query = "请给我一份关于 Pilbara 锂矿的简报"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    report = asyncio.run(run_query(query, verbose=True))
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print("=" * 60)
    print(report)
