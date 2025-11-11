#!/usr/bin/env python3
"""CLI entrypoint for strands-mcp-server.

This provides a command-line interface for running an MCP server in stdio mode,
making it easy to integrate with Claude Desktop, Kiro, and other MCP clients.

Two modes:
1. Local mode: Exposes tools from ./tools/ directory (Strands hot reload)
2. Proxy mode: Acts like npx mcp-remote - bridges stdio to upstream HTTP server

Usage:
    # Local mode: Load tools from ./tools/ directory
    strands-mcp-server

    # Proxy mode: Bridge to upstream HTTP MCP server
    strands-mcp-server --upstream-url http://localhost:8000/mcp

    # With custom working directory
    strands-mcp-server --cwd /path/to/project

    # With system prompt
    strands-mcp-server --system-prompt "You are a helpful assistant"

    # Without agent invocation
    strands-mcp-server --no-agent-invocation

Claude Desktop Config (Local):
    {
      "mcpServers": {
        "strands-tools": {
          "command": "strands-mcp-server",
          "args": ["--cwd", "/absolute/path/to/your/project"]
        }
      }
    }

Claude Desktop Config (Proxy):
    {
      "mcpServers": {
        "strands-proxy": {
          "command": "strands-mcp-server",
          "args": ["--upstream-url", "http://localhost:8000/mcp"]
        }
      }
    }
"""

import argparse
import asyncio
import logging
import sys
import os
from strands import Agent
from strands_mcp_server.mcp_server import mcp_server
from strands_mcp_server.mcp_client import mcp_client

# Configure logging to stderr (stdio mode requirement)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # MCP stdio servers MUST use stderr for logging
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main CLI entrypoint for strands-mcp-server."""
    parser = argparse.ArgumentParser(
        description="Strands MCP Server - Expose Strands Agent tools via MCP stdio protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Load tools from ./tools/ directory (with hot reload)
  strands-mcp-server
  
  # Proxy mode: Bridge to upstream HTTP MCP server (like npx mcp-remote)
  strands-mcp-server --upstream-url http://localhost:8000/mcp
  
  # With custom working directory
  strands-mcp-server --cwd /path/to/project
  
  # With system prompt
  strands-mcp-server --system-prompt "You are a research assistant"
  
  # Without agent invocation capability
  strands-mcp-server --no-agent-invocation
  
  # Debug mode
  strands-mcp-server --debug

Claude Desktop Config (Local Tools):
  {
    "mcpServers": {
      "strands-tools": {
        "command": "strands-mcp-server",
        "args": ["--cwd", "/absolute/path/to/your/project"]
      }
    }
  }

Claude Desktop Config (Proxy Mode):
  {
    "mcpServers": {
      "strands-proxy": {
        "command": "strands-mcp-server",
        "args": ["--upstream-url", "http://localhost:8000/mcp"]
      }
    }
  }
        """,
    )

    parser.add_argument(
        "--system-prompt",
        type=str,
        help="System prompt for the agent",
        default="You are a helpful AI assistant with access to various tools.",
    )

    parser.add_argument(
        "--no-agent-invocation",
        action="store_true",
        help="Disable agent invocation capability (tools only)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--upstream-url",
        type=str,
        help="Upstream MCP server URL to proxy (e.g., http://localhost:8000/mcp)",
    )

    parser.add_argument(
        "--upstream-transport",
        type=str,
        choices=["http", "sse", "streamable_http"],
        default="streamable_http",
        help="Transport type for upstream connection (default: streamable_http)",
    )

    parser.add_argument(
        "--cwd",
        type=str,
        help="Working directory for tool loading (default: current directory)",
    )

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    try:
        logger.info("Starting Strands MCP Server in stdio mode")

        # Change working directory if specified
        if args.cwd:
            logger.info(f"Changing working directory to: {args.cwd}")
            os.chdir(args.cwd)
            logger.info(f"CWD now: {os.getcwd()}")

        # Check if we're proxying to an upstream server
        if args.upstream_url:
            logger.info(f"Proxy mode: Connecting to upstream MCP server at {args.upstream_url}")
            asyncio.run(run_proxy_mode(args))
        else:
            # Local mode: Create agent with package tools + hot reload
            cwd = os.getcwd()
            tools_dir = os.path.join(cwd, "tools")
            logger.info(f"Local mode: Loading tools from directory")
            logger.info(f"  CWD: {cwd}")
            logger.info(f"  Tools dir: {tools_dir}")
            logger.info(f"  Tools dir exists: {os.path.exists(tools_dir)}")

            if os.path.exists(tools_dir):
                tools_files = [f for f in os.listdir(tools_dir) if f.endswith(".py") and not f.startswith("_")]
                logger.info(f"  Found {len(tools_files)} .py files: {tools_files}")

            logger.debug("Strands native hot reload enabled for ./tools/")

            # Create agent with package tools + hot reload from ./tools/
            agent = Agent(
                name="strands-mcp-cli",
                tools=[mcp_server, mcp_client],
                load_tools_from_directory=True,  # Strands handles ./tools/ automatically
                system_prompt=args.system_prompt,
            )

            tool_count = len(agent.tool_registry.get_all_tools_config())
            all_tool_names = list(agent.tool_registry.registry.keys())
            logger.info(f"Agent created with {tool_count} tools: {all_tool_names}")
            logger.debug("  • mcp_server (from package)")
            logger.debug("  • mcp_client (from package)")
            logger.debug("  • Plus any tools in ./tools/ (hot reload enabled)")

            # Start MCP server in stdio mode using mcp_server tool
            # This BLOCKS the current thread - perfect for CLI!
            logger.info("Starting MCP server in stdio mode (foreground, blocking)...")
            agent.tool.mcp_server(
                action="start",
                transport="stdio",
                expose_agent=not args.no_agent_invocation,
                agent=agent,
            )

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)


async def run_proxy_mode(args) -> None:
    """Run MCP server in proxy mode - bridge stdio to upstream HTTP server.

    This acts like npx mcp-remote:
    - Accepts stdio connections from Claude Desktop/Kiro
    - Forwards requests to upstream MCP server via HTTP
    - Returns upstream responses back through stdio

    Args:
        args: CLI arguments with upstream_url and upstream_transport
    """
    try:
        from mcp import types, ClientSession
        from mcp.server.lowlevel import Server
        from mcp.server.stdio import stdio_server
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError as e:
        logger.error(f"Failed to import MCP dependencies: {e}")
        logger.error("Install with: pip install mcp")
        sys.exit(1)

    logger.info(f"Connecting to upstream MCP server: {args.upstream_url}")
    logger.info(f"Transport: streamable_http")

    # Connect to upstream MCP server using SDK client
    upstream_session = None
    upstream_tools = []

    try:
        # Create client session to upstream server
        async with streamablehttp_client(args.upstream_url) as client:
            async with ClientSession(client[0], client[1]) as session:
                # Initialize and get tools
                await session.initialize()
                logger.info("✅ Connected to upstream MCP server")

                # List tools from upstream
                response = await session.list_tools()
                upstream_tools = response.tools
                logger.info(f"✅ Discovered {len(upstream_tools)} upstream tools")
                for tool in upstream_tools:
                    logger.debug(
                        f"  • {tool.name}: {tool.description[:50] if tool.description else 'No description'}..."
                    )

                # Create MCP server for stdio
                server = Server("strands-mcp-proxy")

                # Register list_tools handler
                @server.list_tools()
                async def list_tools() -> list[types.Tool]:
                    """Return list of upstream tools."""
                    logger.debug(f"list_tools called, returning {len(upstream_tools)} upstream tools")
                    return upstream_tools

                # Register call_tool handler
                @server.call_tool()
                async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
                    """Proxy tool calls to upstream server."""
                    try:
                        logger.debug(f"Proxying tool call: {name} with args: {arguments}")

                        # Call tool on upstream server
                        result = await session.call_tool(name, arguments)

                        logger.debug(f"Upstream result received")

                        # Convert result to MCP TextContent
                        return result.content

                    except Exception as e:
                        logger.exception(f"Error proxying tool '{name}'")
                        return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]

                # Run stdio server (blocks until terminated)
                logger.info("🚀 MCP proxy ready - listening on stdin/stdout")
                logger.info(f"   Forwarding to: {args.upstream_url}")

                async with stdio_server() as streams:
                    await server.run(streams[0], streams[1], server.create_initialization_options())

    except Exception as e:
        logger.exception(f"Failed to connect to upstream MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
