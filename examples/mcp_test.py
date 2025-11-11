#!/usr/bin/env python3
"""Test client for MCP server using strands-mcp-server package.

This script demonstrates two ways to connect to an MCP server:

1. Using Strands MCPClient (low-level, direct integration)
2. Using mcp_client tool (high-level, agent-driven)

Prerequisites:
    Start the MCP server first:
    python mcp_server.py
"""

from strands import Agent
from strands_tools import calculator
from strands_mcp_server import mcp_client

print("🚀 MCP Client Test Demo\n")
print("=" * 60)

# Method 1: Using mcp_client tool (recommended)
print("\n🔧 Method 1: Using mcp_client tool")
print("-" * 60)

agent = Agent(name="test-client", tools=[calculator, mcp_client])

print("\n📡 Connecting to MCP server at http://localhost:8000/mcp...")
result = agent.tool.mcp_client(
    action="connect",
    connection_id="demo-server",
    transport="http",
    server_url="http://localhost:8000/mcp",
)
print(result["content"][0]["text"])

print("\n📋 Listing available tools from server...")
result = agent.tool.mcp_client(
    action="list_tools",
    connection_id="demo-server",
)
print(result["content"][0]["text"])

print("\n🧮 Calling remote calculator tool...")
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="demo-server",
    tool_name="calculator",
    tool_args={"expression": "999 * 888"},
)
print(result["content"][0]["text"])

print("\n🤖 Invoking full agent remotely...")
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="demo-server",
    tool_name="invoke_agent",
    tool_args={"prompt": "Calculate the square root of 1764"},
)
print(result["content"][0]["text"])

print("\n👋 Disconnecting...")
result = agent.tool.mcp_client(
    action="disconnect",
    connection_id="demo-server",
)
print(result["content"][0]["text"])

print("\n" + "=" * 60)
print("✅ Test complete!")
print("\n💡 You can also test interactively:")
print("   • Start python interpreter")
print("   • from strands import Agent")
print("   • from strands_mcp_server import mcp_client")
print("   • agent = Agent(tools=[mcp_client])")
print("   • agent('connect to http://localhost:8000/mcp as demo')")
print("=" * 60)
