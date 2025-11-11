"""Unit tests for mcp_client tool."""

import pytest
from strands import Agent

from strands_mcp_server import mcp_client


@pytest.fixture
def client_agent():
    """Create agent with mcp_client tool."""
    return Agent(name="client-agent", tools=[mcp_client])


class TestMCPClientBasics:
    """Basic mcp_client functionality tests."""

    def test_list_connections_empty(self, client_agent):
        """Test listing connections when none exist."""
        result = client_agent.tool.mcp_client(action="list_connections")

        assert result["status"] == "success"
        assert (
            "No active MCP connections" in result["content"][0]["text"]
            or "Active MCP Connections" in result["content"][0]["text"]
        )

    def test_invalid_action(self, client_agent):
        """Test handling of invalid action."""
        result = client_agent.tool.mcp_client(
            action="invalid_action",
            connection_id="test",
        )

        assert result["status"] == "error"
        assert "Unknown action" in result["content"][0]["text"]

    def test_disconnect_nonexistent(self, client_agent):
        """Test disconnecting from non-existent connection."""
        result = client_agent.tool.mcp_client(
            action="disconnect",
            connection_id="nonexistent",
        )

        assert result["status"] == "error"
        assert "not found" in result["content"][0]["text"]

    def test_list_tools_without_connection(self, client_agent):
        """Test listing tools without established connection."""
        result = client_agent.tool.mcp_client(
            action="list_tools",
            connection_id="nonexistent",
        )

        assert result["status"] == "error"
        assert "not found" in result["content"][0]["text"]

    def test_call_tool_without_connection(self, client_agent):
        """Test calling tool without established connection."""
        result = client_agent.tool.mcp_client(
            action="call_tool",
            connection_id="nonexistent",
            tool_name="calculator",
            tool_args={"expression": "2 + 2"},
        )

        assert result["status"] == "error"
        assert "not found" in result["content"][0]["text"]


class TestMCPClientValidation:
    """Test input validation for mcp_client."""

    def test_connect_without_connection_id(self, client_agent):
        """Test connect requires connection_id."""
        result = client_agent.tool.mcp_client(
            action="connect",
            transport="http",
            server_url="http://localhost:8000/mcp",
        )

        assert result["status"] == "error"
        assert "connection_id is required" in result["content"][0]["text"]

    def test_connect_without_transport(self, client_agent):
        """Test connect requires transport."""
        result = client_agent.tool.mcp_client(
            action="connect",
            connection_id="test",
            server_url="http://localhost:8000/mcp",
        )

        assert result["status"] == "error"
        assert "transport is required" in result["content"][0]["text"]

    def test_connect_http_without_url(self, client_agent):
        """Test HTTP transport requires server_url."""
        result = client_agent.tool.mcp_client(
            action="connect",
            connection_id="test",
            transport="http",
        )

        assert result["status"] == "error"
        assert "server_url is required" in result["content"][0]["text"]

    def test_connect_stdio_without_command(self, client_agent):
        """Test stdio transport requires command."""
        result = client_agent.tool.mcp_client(
            action="connect",
            connection_id="test",
            transport="stdio",
        )

        assert result["status"] == "error"
        assert "command is required" in result["content"][0]["text"]
