#!/usr/bin/env python3
"""Example MCP server using strands-mcp-server package.

This script demonstrates how to expose a Strands Agent as an MCP server,
making agent tools available to MCP clients like Claude Desktop.

Usage:
    python mcp_server.py

    Then connect with:
    - Claude Desktop (via mcp-remote)
    - Another agent with mcp_client tool
    - Custom MCP client at http://localhost:8000/mcp
"""

from strands import Agent
from strands_tools import calculator, shell
from strands_mcp_server import mcp_server

# Create agent with tools and MCP server capability
agent = Agent(name="demo-server", tools=[calculator, shell, mcp_server])

print("🚀 Starting MCP Server Demo\n")
print("=" * 60)

# Start MCP server
print("\n📡 Starting MCP server on port 8000...")
agent.tool.mcp_server(action="start", mode="http", port=8000, agent=agent)

print("\n" + "=" * 60)
print("✅ Server running! You can now:")
print("  • Connect at: http://localhost:8000/mcp")
print("  • Call tools remotely from other agents")
print("=" * 60)

# Interactive agent loop
print("\n💬 Agent is also available interactively!")
print("Try: 'show server status' or 'calculate 42 * 89'\n")

while True:
    try:
        agent(input("\n# "))
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        break
    except EOFError:
        break
