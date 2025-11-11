"""Unit tests for mcp_server tool."""

import pytest
from strands import Agent
from strands_tools import calculator, shell

from strands_mcp_server import mcp_server


@pytest.fixture
def server_agent():
    """Create agent with mcp_server and some tools."""
    return Agent(
        name="server-agent",
        tools=[calculator, shell, mcp_server],
    )


class TestMCPServerBasics:
    """Basic mcp_server functionality tests."""

    def test_invalid_action(self, server_agent):
        """Test handling of invalid action."""
        result = server_agent.tool.mcp_server(
            action="invalid_action",
            agent=server_agent,
        )

        assert result["status"] == "error"
        assert "Unknown action" in result["content"][0]["text"]

    def test_status_no_servers(self, server_agent):
        """Test status when no servers running."""
        result = server_agent.tool.mcp_server(action="status")

        assert result["status"] == "success"
        # Could be either "No MCP servers" or show existing servers from other tests

    def test_list_servers(self, server_agent):
        """Test listing servers."""
        result = server_agent.tool.mcp_server(action="list")

        assert result["status"] == "success"

    def test_stop_nonexistent_server(self, server_agent):
        """Test stopping non-existent server."""
        result = server_agent.tool.mcp_server(
            action="stop",
            server_id="nonexistent",
        )

        assert result["status"] == "error"
        assert "not running" in result["content"][0]["text"]


class TestMCPServerConfig:
    """Test MCP server configuration options."""

    def test_start_with_custom_port(self, server_agent, test_port):
        """Test starting server on custom port."""
        from tests.conftest import wait_for_port_free, get_free_port

        custom_port = get_free_port()

        result = server_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=custom_port,
            server_id="custom-port-test",
            agent=server_agent,
        )

        assert result["status"] == "success"
        assert str(custom_port) in result["content"][0]["text"]

        # Cleanup
        server_agent.tool.mcp_server(action="stop", server_id="custom-port-test")
        wait_for_port_free(custom_port, timeout=5)

    def test_start_without_agent_invocation(self, server_agent, test_port):
        """Test starting server without invoke_agent tool."""
        result = server_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port + 101,
            expose_agent=False,
            server_id="no-invoke-test",
            agent=server_agent,
        )

        assert result["status"] == "success"
        # Should not mention invoke_agent

        # Cleanup
        server_agent.tool.mcp_server(action="stop", server_id="no-invoke-test")

    def test_start_duplicate_server(self, server_agent, test_port):
        """Test starting server with duplicate ID."""
        # Start first server
        result1 = server_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port + 102,
            server_id="duplicate-test",
            agent=server_agent,
        )

        assert result1["status"] == "success"

        # Try to start another with same ID
        result2 = server_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port + 103,
            server_id="duplicate-test",
            agent=server_agent,
        )

        assert result2["status"] == "error"
        assert "already running" in result2["content"][0]["text"]

        # Cleanup
        server_agent.tool.mcp_server(action="stop", server_id="duplicate-test")
