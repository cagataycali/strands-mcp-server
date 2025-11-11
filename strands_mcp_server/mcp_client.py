"""MCP Client Tool for Strands Agents.

Test and interact with MCP servers from within a Strands Agent. This tool provides
a complete MCP client implementation that can connect to any MCP server (including
servers created with the mcp_server tool) and use their exposed tools.

Key Features:
- **Multiple Transports**: HTTP (streamable), stdio, SSE
- **Connection Management**: Connect, disconnect, list connections
- **Tool Discovery**: List available tools from connected servers
- **Tool Execution**: Call tools on remote servers
- **Session Persistence**: Maintain connections across multiple operations

Example:
    ```python
    from strands import Agent
    from tools.mcp_client import mcp_client
    from tools.mcp_server import mcp_server

    agent = Agent(tools=[mcp_client, mcp_server])

    # Start a server
    agent("start mcp server on port 8000")

    # Connect to it
    agent("connect to mcp server at http://localhost:8000/mcp as test-server")

    # List its tools
    agent("list tools from test-server")

    # Call a tool
    agent("call calculator tool on test-server with expression: 2 + 2")
    ```

Architecture:
    ```
    ┌─────────────────────────────────────┐
    │      Strands Agent (Client)         │
    │  ┌──────────────────────────────┐   │
    │  │     mcp_client tool          │   │
    │  └──────────────────────────────┘   │
    └─────────────────────────────────────┘
                    ↓
            MCP Client Connection
                    ↓
    ┌─────────────────────────────────────┐
    │      Strands Agent (Server)         │
    │  ┌──────────────────────────────┐   │
    │  │     mcp_server tool          │   │
    │  └──────────────────────────────┘   │
    └─────────────────────────────────────┘
    ```

References:
- MCP Specification: https://spec.modelcontextprotocol.io/
- MCP Client SDK: python-sdk/src/mcp/client/
"""

import logging
from typing import Any, Optional

from strands import tool

# Global state for managing MCP connections
_client_connections: dict[str, Any] = {}

logger = logging.getLogger(__name__)


@tool
def mcp_client(
    action: str,
    connection_id: Optional[str] = None,
    transport: Optional[str] = None,
    server_url: Optional[str] = None,
    command: Optional[str] = None,
    args: Optional[list[str]] = None,
    tool_name: Optional[str] = None,
    tool_args: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Test and interact with MCP servers.

    This tool provides a complete MCP client implementation for testing and using
    MCP servers from within a Strands Agent.

    Args:
        action: Action to perform - "connect", "disconnect", "list_tools", "call_tool", "list_connections"
        connection_id: Unique identifier for this connection
        transport: Transport type - "http", "stdio", or "sse"
        server_url: URL for HTTP/SSE transport (e.g., "http://localhost:8000/mcp")
        command: Command for stdio transport (e.g., "python")
        args: Arguments for stdio command (e.g., ["mcp_server_stdio.py"])
        tool_name: Name of tool to call (for call_tool action)
        tool_args: Arguments to pass to tool (for call_tool action)

    Returns:
        Result dictionary with status and content

    Examples:
        # Connect to HTTP server
        mcp_client(
            action="connect",
            connection_id="my-server",
            transport="http",
            server_url="http://localhost:8000/mcp"
        )

        # Connect to stdio server
        mcp_client(
            action="connect",
            connection_id="stdio-server",
            transport="stdio",
            command="python",
            args=["mcp_server_stdio.py"]
        )

        # List tools from connection
        mcp_client(action="list_tools", connection_id="my-server")

        # Call a tool
        mcp_client(
            action="call_tool",
            connection_id="my-server",
            tool_name="calculator",
            tool_args={"expression": "2 + 2"}
        )

        # List all connections
        mcp_client(action="list_connections")

        # Disconnect
        mcp_client(action="disconnect", connection_id="my-server")

    Notes:
        - stdio transport: Server must be launchable as subprocess
        - HTTP transport: Server must be already running
        - Connections are maintained in global state for reuse
    """
    if action == "connect":
        return _connect(connection_id, transport, server_url, command, args)
    elif action == "disconnect":
        return _disconnect(connection_id)
    elif action == "list_tools":
        return _list_tools(connection_id)
    elif action == "call_tool":
        return _call_tool(connection_id, tool_name, tool_args)
    elif action == "list_connections":
        return _list_connections()
    else:
        return {
            "status": "error",
            "content": [
                {
                    "text": f"❌ Unknown action: {action}\n\n"
                    "Available actions: connect, disconnect, list_tools, call_tool, list_connections"
                }
            ],
        }


def _connect(
    connection_id: Optional[str],
    transport: Optional[str],
    server_url: Optional[str],
    command: Optional[str],
    args: Optional[list[str]],
) -> dict[str, Any]:
    """Connect to an MCP server.

    This function establishes a connection to an MCP server using the specified
    transport type. The connection is stored in global state for reuse.

    Follows patterns from:
    - Strands MCPClient: sdk-python/src/strands/tools/mcp/mcp_client.py
    - MCP client transports: python-sdk/src/mcp/client/
    """
    try:
        if not connection_id:
            return {
                "status": "error",
                "content": [{"text": "❌ connection_id is required"}],
            }

        if not transport:
            return {
                "status": "error",
                "content": [{"text": "❌ transport is required (http, stdio, or sse)"}],
            }

        if connection_id in _client_connections:
            return {
                "status": "error",
                "content": [{"text": f"❌ Connection '{connection_id}' already exists"}],
            }

        # Import MCP client components
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp.client.streamable_http import streamablehttp_client

        if transport == "http":
            if not server_url:
                return {
                    "status": "error",
                    "content": [{"text": "❌ server_url is required for HTTP transport"}],
                }

            logger.debug(f"Connecting to HTTP server: {server_url}")

            # Create transport callable following Strands MCPClient pattern
            def transport_callable():
                return streamablehttp_client(server_url)

            connection_info = {
                "transport": "http",
                "server_url": server_url,
                "transport_callable": transport_callable,
                "session": None,  # Will be initialized on first use
            }

        elif transport == "stdio":
            if not command:
                return {
                    "status": "error",
                    "content": [{"text": "❌ command is required for stdio transport"}],
                }

            logger.debug(f"Connecting to stdio server: {command} {args or []}")

            # Create stdio server parameters
            server_params = StdioServerParameters(command=command, args=args or [], env=None)

            # Create transport callable
            def transport_callable():
                return stdio_client(server_params)

            connection_info = {
                "transport": "stdio",
                "command": command,
                "args": args,
                "transport_callable": transport_callable,
                "session": None,
            }

        elif transport == "sse":
            if not server_url:
                return {
                    "status": "error",
                    "content": [{"text": "❌ server_url is required for SSE transport"}],
                }

            logger.debug(f"Connecting to SSE server: {server_url}")

            from mcp.client.sse import sse_client

            def transport_callable():
                return sse_client(server_url)

            connection_info = {
                "transport": "sse",
                "server_url": server_url,
                "transport_callable": transport_callable,
                "session": None,
            }

        else:
            return {
                "status": "error",
                "content": [{"text": f"❌ Unknown transport: {transport}\n\nSupported: http, stdio, sse"}],
            }

        # Test the connection by listing tools
        logger.debug(f"Testing connection by listing tools...")
        tools = []
        try:
            # Create a temporary session to test and get tool count
            import asyncio

            async def test_connection():
                async with connection_info["transport_callable"]() as (
                    read_stream,
                    write_stream,
                    get_session_id,  # StreamableHTTP returns 3 values
                ):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        return result.tools

            tools = asyncio.run(test_connection())
            logger.debug(f"Successfully connected, found {len(tools)} tools")

        except Exception as e:
            logger.exception("Failed to connect to MCP server")
            return {
                "status": "error",
                "content": [{"text": f"❌ Failed to connect: {str(e)}"}],
            }

        # Store connection
        _client_connections[connection_id] = connection_info

        # Build response
        tool_list = "\n".join(f"  • {tool.name}" for tool in tools[:10])
        if len(tools) > 10:
            tool_list += f"\n  ... and {len(tools) - 10} more"

        transport_info = (
            f"URL: {server_url}" if transport in ["http", "sse"] else f"Command: {command} {' '.join(args or [])}"
        )

        message = (
            f"✅ Connected to MCP server '{connection_id}'\n\n"
            f"📊 Transport: {transport}\n"
            f"🔗 {transport_info}\n"
            f"🔧 Available tools ({len(tools)}):\n"
            f"{tool_list}"
        )

        return {"status": "success", "content": [{"text": message}]}

    except Exception as e:
        logger.exception("Error in connect action")
        return {
            "status": "error",
            "content": [{"text": f"❌ Error: {str(e)}"}],
        }


def _disconnect(connection_id: Optional[str]) -> dict[str, Any]:
    """Disconnect from an MCP server.

    Removes the connection from global state. The actual transport cleanup
    happens automatically via context managers.
    """
    try:
        if not connection_id:
            return {
                "status": "error",
                "content": [{"text": "❌ connection_id is required"}],
            }

        if connection_id not in _client_connections:
            return {
                "status": "error",
                "content": [{"text": f"❌ Connection '{connection_id}' not found"}],
            }

        # Remove connection
        del _client_connections[connection_id]
        logger.debug(f"Disconnected from '{connection_id}'")

        return {
            "status": "success",
            "content": [{"text": f"✅ Disconnected from '{connection_id}'"}],
        }

    except Exception as e:
        logger.exception("Error in disconnect action")
        return {
            "status": "error",
            "content": [{"text": f"❌ Error: {str(e)}"}],
        }


def _list_tools(connection_id: Optional[str]) -> dict[str, Any]:
    """List tools from a connected MCP server.

    This creates a temporary session to query the server for its available tools.
    """
    try:
        if not connection_id:
            return {
                "status": "error",
                "content": [{"text": "❌ connection_id is required"}],
            }

        if connection_id not in _client_connections:
            return {
                "status": "error",
                "content": [{"text": f"❌ Connection '{connection_id}' not found"}],
            }

        connection_info = _client_connections[connection_id]
        logger.debug(f"Listing tools from '{connection_id}'")

        # Create session and list tools
        import asyncio

        from mcp.client.session import ClientSession

        async def list_tools_async():
            async with connection_info["transport_callable"]() as (
                read_stream,
                write_stream,
                get_session_id,  # StreamableHTTP returns 3 values
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return result.tools

        tools = asyncio.run(list_tools_async())
        logger.debug(f"Found {len(tools)} tools")

        # Build detailed tool list
        tool_details = []
        for tool in tools:
            details = f"**{tool.name}**"
            if tool.description:
                details += f"\n  Description: {tool.description}"
            if tool.inputSchema:
                # Show required parameters
                schema = tool.inputSchema
                if "required" in schema:
                    details += f"\n  Required: {', '.join(schema['required'])}"
                if "properties" in schema:
                    details += f"\n  Parameters: {', '.join(schema['properties'].keys())}"
            tool_details.append(details)

        tools_text = "\n\n".join(tool_details)

        message = f"📋 **Tools from '{connection_id}'**\n\n" f"Found {len(tools)} tools:\n\n" f"{tools_text}"

        return {"status": "success", "content": [{"text": message}]}

    except Exception as e:
        logger.exception("Error listing tools")
        return {
            "status": "error",
            "content": [{"text": f"❌ Error: {str(e)}"}],
        }


def _call_tool(
    connection_id: Optional[str],
    tool_name: Optional[str],
    tool_args: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Call a tool on a connected MCP server.

    This establishes a session, calls the specified tool with provided arguments,
    and returns the result.
    """
    try:
        if not connection_id:
            return {
                "status": "error",
                "content": [{"text": "❌ connection_id is required"}],
            }

        if not tool_name:
            return {
                "status": "error",
                "content": [{"text": "❌ tool_name is required"}],
            }

        if connection_id not in _client_connections:
            return {
                "status": "error",
                "content": [{"text": f"❌ Connection '{connection_id}' not found"}],
            }

        connection_info = _client_connections[connection_id]
        logger.debug(f"Calling tool '{tool_name}' on '{connection_id}' with args: {tool_args}")

        # Call the tool
        import asyncio

        from mcp.client.session import ClientSession

        async def call_tool_async():
            async with connection_info["transport_callable"]() as (
                read_stream,
                write_stream,
                get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, tool_args or {})
                    return result

        result = asyncio.run(call_tool_async())
        logger.debug(f"Tool call complete, got {len(result.content)} content items")

        # Extract result content
        result_text = []
        for content in result.content:
            if hasattr(content, "text"):
                result_text.append(content.text)
            else:
                result_text.append(str(content))

        combined_result = "\n".join(result_text)

        message = f"✅ **Tool '{tool_name}' executed on '{connection_id}'**\n\n" f"Result:\n{combined_result}"

        return {"status": "success", "content": [{"text": message}]}

    except Exception as e:
        logger.exception(f"Error calling tool '{tool_name}'")
        return {
            "status": "error",
            "content": [{"text": f"❌ Error: {str(e)}"}],
        }


def _list_connections() -> dict[str, Any]:
    """List all active MCP connections.

    Shows connection details including transport type and available tools.
    """
    try:
        if not _client_connections:
            return {
                "status": "success",
                "content": [{"text": "📭 No active MCP connections"}],
            }

        lines = [f"📡 **Active MCP Connections** ({len(_client_connections)})\n"]

        for conn_id, conn_info in _client_connections.items():
            lines.append(f"\n**{conn_id}**")
            lines.append(f"  • Transport: {conn_info['transport']}")

            if conn_info["transport"] == "http":
                lines.append(f"  • URL: {conn_info['server_url']}")
            elif conn_info["transport"] == "sse":
                lines.append(f"  • URL: {conn_info['server_url']}")
            elif conn_info["transport"] == "stdio":
                cmd = f"{conn_info['command']} {' '.join(conn_info.get('args', []))}"
                lines.append(f"  • Command: {cmd}")

        message = "\n".join(lines)

        return {"status": "success", "content": [{"text": message}]}

    except Exception as e:
        logger.exception("Error listing connections")
        return {
            "status": "error",
            "content": [{"text": f"❌ Error: {str(e)}"}],
        }
