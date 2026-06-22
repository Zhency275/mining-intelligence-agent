"""Mining Intelligence Agent — CLI Entry Point.

Usage:
    python -m agent_client.main
    python -m agent_client.main --query "请给我一份关于 Pilbara 锂矿的简报"
    python -m agent_client.main --query "Pilbara lithium mining investment outlook"
    python -m agent_client.main --interactive

Environment:
    ANTHROPIC_API_KEY — Required. Your Anthropic API key.
"""

import argparse
import asyncio
import os
import sys

# Fix Unicode output on Windows (GBK console)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import sys
from pathlib import Path

# Load .env if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from .agent import MiningIntelligenceAgent, MODEL


DEFAULT_QUERIES = [
    "请给我一份关于 Pilbara 锂矿的简报",
    "请分析一下近期锂矿价格走势和投资前景",
    "Pilbara lithium mining investment outlook and production analysis",
]


def check_api_key() -> str:
    """Verify API key is available."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("\nOptions:")
        print("  1. Create a .env file in the project root with: ANTHROPIC_API_KEY=sk-ant-...")
        print("  2. Set the environment variable: export ANTHROPIC_API_KEY=sk-ant-...")
        print("  3. Pass it directly: python -m agent_client.main --api-key sk-ant-...")
        sys.exit(1)
    return key


async def run_interactive(api_key: str, model: str, verbose: bool):
    """Run agent in interactive mode — user types queries and gets reports."""
    print("\n" + "=" * 60)
    print("  Mining Intelligence Agent — Interactive Mode")
    print("  Type 'quit' or 'exit' to leave.")
    print("  Type 'demo' to run a preset query.")
    print("=" * 60)

    agent = MiningIntelligenceAgent(
        api_key=api_key,
        model=model,
        verbose=verbose,
    )

    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if query.lower() == "demo":
            query = DEFAULT_QUERIES[0]

        print(f"\n[Agent] Analyzing: {query[:80]}...")
        try:
            report = await agent.run(query)
            print("\n" + "=" * 60)
            print(report)
            agent.save_report(report, query)
        except Exception as e:
            print(f"\n[ERROR] {e}")
            print("Restarting agent for next query...")
            # Re-initialize agent for next query
            agent = MiningIntelligenceAgent(
                api_key=api_key,
                model=model,
                verbose=verbose,
            )


async def main():
    parser = argparse.ArgumentParser(
        description="Mining Intelligence Agent — MCP-based mining analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agent_client.main
  python -m agent_client.main --query "Pilbara 锂矿投资前景"
  python -m agent_client.main --interactive
  python -m agent_client.main --query "分析锂矿价格走势" --save
        """,
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Natural language query about mining/minerals",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode (type queries one by one)",
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        default=True,
        help="Save report to file (default: True)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save report to file",
    )
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        help="Anthropic API key",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=MODEL,
        help=f"Model to use (default: {MODEL})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress",
    )
    parser.add_argument(
        "--list-servers",
        action="store_true",
        help="List MCP server configuration and exit",
    )

    args = parser.parse_args()

    # List servers mode
    if args.list_servers:
        from .mcp_client_manager import MCPClientManager
        manager = MCPClientManager()
        print("MCP Server Configuration:")
        for server in manager.servers:
            print(f"  {server.name}: python -m {server.module}")
        return

    # Get API key
    api_key = args.api_key or check_api_key()

    # Interactive mode
    if args.interactive:
        await run_interactive(api_key, args.model, args.verbose)
        return

    # Single query mode
    query = args.query
    if not query:
        # Default query
        query = DEFAULT_QUERIES[0]
        print(f"[Agent] No query provided. Using default: {query}")

    agent = MiningIntelligenceAgent(
        api_key=api_key,
        model=args.model,
        verbose=args.verbose,
    )

    report = await agent.run(query)
    print("\n" + report)

    if not args.no_save:
        agent.save_report(report, query)


if __name__ == "__main__":
    asyncio.run(main())
