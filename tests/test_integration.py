"""Integration tests for MCP server and client tools.

Tests the full flow of starting an MCP server, connecting as a client,
and executing tools remotely.
"""

import time

import pytest
from strands import Agent
from strands_tools import calculator, shell

from strands_mcp_server import mcp_client, mcp_server


@pytest.fixture
def test_agent():
    """Create test agent with MCP server and client tools."""
    return Agent(
        name="test-agent",
        tools=[
            calculator,
            shell,
            mcp_server,
            mcp_client,
        ],
    )


@pytest.fixture
def running_server(test_agent, test_port, server_startup_delay):
    """Start MCP server and return agent."""
    # Start server
    result = test_agent.tool.mcp_server(
        action="start",
        mode="http",
        port=test_port,
        server_id="test-server",
        agent=test_agent,
    )

    assert result["status"] == "success"
    assert "started on port" in result["content"][0]["text"]

    # Wait for server to be ready
    time.sleep(server_startup_delay)

    yield test_agent

    # Cleanup: Stop server
    try:
        test_agent.tool.mcp_server(action="stop", server_id="test-server")
    except Exception:
        pass  # Server might already be stopped


class TestMCPIntegration:
    """Integration tests for MCP server and client."""

    def test_server_startup(self, test_agent, test_port):
        """Test MCP server starts successfully."""
        result = test_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port,
            server_id="startup-test",
            agent=test_agent,
        )

        assert result["status"] == "success"
        assert "startup-test" in result["content"][0]["text"]
        assert str(test_port) in result["content"][0]["text"]
        assert "invoke_agent" in result["content"][0]["text"]

        # Cleanup
        test_agent.tool.mcp_server(action="stop", server_id="startup-test")

    def test_client_connection(self, running_server, test_port):
        """Test client can connect to MCP server."""
        result = running_server.tool.mcp_client(
            action="connect",
            connection_id="test-connection",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        assert result["status"] == "success"
        assert "Connected to MCP server" in result["content"][0]["text"]
        assert "test-connection" in result["content"][0]["text"]

        # Cleanup
        running_server.tool.mcp_client(action="disconnect", connection_id="test-connection")

    def test_list_tools(self, running_server, test_port):
        """Test listing tools from MCP server."""
        # Connect first
        running_server.tool.mcp_client(
            action="connect",
            connection_id="list-tools-test",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        # List tools
        result = running_server.tool.mcp_client(
            action="list_tools",
            connection_id="list-tools-test",
        )

        assert result["status"] == "success"
        assert "calculator" in result["content"][0]["text"]
        assert "shell" in result["content"][0]["text"]
        assert "invoke_agent" in result["content"][0]["text"]

        # Cleanup
        running_server.tool.mcp_client(action="disconnect", connection_id="list-tools-test")

    def test_call_calculator_remotely(self, running_server, test_port):
        """Test calling calculator tool remotely via MCP."""
        # Connect
        running_server.tool.mcp_client(
            action="connect",
            connection_id="calc-test",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        # Call calculator
        result = running_server.tool.mcp_client(
            action="call_tool",
            connection_id="calc-test",
            tool_name="calculator",
            tool_args={"expression": "42 * 89 + 17"},
        )

        assert result["status"] == "success"
        assert "3755" in result["content"][0]["text"]

        # Cleanup
        running_server.tool.mcp_client(action="disconnect", connection_id="calc-test")

    def test_call_shell_remotely(self, running_server, test_port):
        """Test calling shell tool remotely via MCP."""
        # Connect
        running_server.tool.mcp_client(
            action="connect",
            connection_id="shell-test",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        # Call shell
        result = running_server.tool.mcp_client(
            action="call_tool",
            connection_id="shell-test",
            tool_name="shell",
            tool_args={"command": "echo 'Hello from MCP!'"},
        )

        assert result["status"] == "success"
        assert "Hello from MCP!" in result["content"][0]["text"]

        # Cleanup
        running_server.tool.mcp_client(action="disconnect", connection_id="shell-test")

    def test_invoke_agent_remotely(self, running_server, test_port):
        """Test full agent invocation via MCP invoke_agent tool."""
        # Connect
        running_server.tool.mcp_client(
            action="connect",
            connection_id="invoke-test",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        # Invoke agent
        result = running_server.tool.mcp_client(
            action="call_tool",
            connection_id="invoke-test",
            tool_name="invoke_agent",
            tool_args={"prompt": "Calculate 123 * 456 and tell me the result"},
        )

        assert result["status"] == "success"
        assert "56088" in result["content"][0]["text"] or "56,088" in result["content"][0]["text"]

        # Cleanup
        running_server.tool.mcp_client(action="disconnect", connection_id="invoke-test")

    def test_server_status(self, running_server, test_port):
        """Test server status reporting."""
        result = running_server.tool.mcp_server(action="status")

        assert result["status"] == "success"
        assert "test-server" in result["content"][0]["text"]
        assert "running" in result["content"][0]["text"]
        assert str(test_port) in result["content"][0]["text"]

    def test_list_connections(self, running_server, test_port):
        """Test listing active MCP connections."""
        # Connect
        running_server.tool.mcp_client(
            action="connect",
            connection_id="list-conn-test",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        # List connections
        result = running_server.tool.mcp_client(action="list_connections")

        assert result["status"] == "success"
        assert "list-conn-test" in result["content"][0]["text"]
        assert "http" in result["content"][0]["text"]

        # Cleanup
        running_server.tool.mcp_client(action="disconnect", connection_id="list-conn-test")

    def test_disconnect(self, running_server, test_port):
        """Test disconnecting from MCP server."""
        # Connect
        running_server.tool.mcp_client(
            action="connect",
            connection_id="disconnect-test",
            transport="http",
            server_url=f"http://localhost:{test_port}/mcp",
        )

        # Disconnect
        result = running_server.tool.mcp_client(
            action="disconnect",
            connection_id="disconnect-test",
        )

        assert result["status"] == "success"
        assert "Disconnected from" in result["content"][0]["text"]
        assert "disconnect-test" in result["content"][0]["text"]


class TestMCPServerModes:
    """Test different MCP server modes."""

    def test_stateful_mode(self, test_agent, test_port):
        """Test server in stateful mode (default)."""
        result = test_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port,
            stateless=False,
            server_id="stateful-test",
            agent=test_agent,
        )

        assert result["status"] == "success"
        assert "stateful" in result["content"][0]["text"]

        # Cleanup
        test_agent.tool.mcp_server(action="stop", server_id="stateful-test")

    def test_stateless_mode(self, test_agent, test_port):
        """Test server in stateless mode."""
        from tests.conftest import wait_for_port_free

        # Ensure port is free
        wait_for_port_free(test_port, timeout=10)

        result = test_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port,
            stateless=True,
            server_id="stateless-test",
            agent=test_agent,
        )

        assert result["status"] == "success"
        assert "stateless" in result["content"][0]["text"]

        # Cleanup
        test_agent.tool.mcp_server(action="stop", server_id="stateless-test")
        wait_for_port_free(test_port, timeout=5)

    def test_tool_filtering(self, test_agent, test_port):
        """Test exposing only specific tools."""
        result = test_agent.tool.mcp_server(
            action="start",
            mode="http",
            port=test_port,
            tools=["calculator"],
            server_id="filtered-test",
            agent=test_agent,
        )

        assert result["status"] == "success"
        assert "calculator" in result["content"][0]["text"]

        # Cleanup
        test_agent.tool.mcp_server(action="stop", server_id="filtered-test")
