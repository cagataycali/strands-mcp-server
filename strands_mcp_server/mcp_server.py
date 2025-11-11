"""MCP Server Tool for Strands Agents.

Transforms a Strands Agent into an MCP (Model Context Protocol) server, exposing agent
tools and capabilities to any MCP-compatible client (Claude Desktop, other agents, etc.).

This implementation follows MCP Python SDK patterns and Strands best practices:
- Uses StreamableHTTPSessionManager for production-ready session handling
- Supports both stateless (multi-node) and stateful (single-node) modes
- Implements proper lifecycle management with background threads
- Comprehensive error handling and logging
- Context-aware tool execution via agent parameter injection

Key Features:
- **Stateless HTTP Mode**: Multi-node ready, horizontally scalable
- **Stateful HTTP Mode**: Session persistence across requests
- **stdio Mode**: Direct stdio communication for Claude Desktop
- **Tool Filtering**: Expose only specific tools
- **Agent Invocation**: Optional full agent conversation capability
- **Auto-cleanup**: Proper resource management via context managers

Example:
    ```python
    from strands import Agent
    from strands_tools import shell, calculator, file_read
    from tools.mcp_server import mcp_server

    agent = Agent(tools=[shell, calculator, file_read, mcp_server])

    # Via agent invocation (recommended - proper context injection)
    agent("start mcp server on port 8000")

    # Stateless mode for production (multi-node ready)
    agent("start stateless mcp server on port 8000")

    # With specific tools only
    agent("start mcp server with tools: calculator, file_read")

    # Without agent invocation (tools only)
    agent("start mcp server without agent invocation")

    # Check status
    agent("mcp server status")
    ```

References:
- MCP Specification: https://spec.modelcontextprotocol.io/
- Strands MCP Client: sdk-python/src/strands/tools/mcp/mcp_client.py
- MCP Server: python-sdk/src/mcp/server/lowlevel/server.py
- StreamableHTTPSessionManager: python-sdk/src/mcp/server/streamable_http_manager.py
"""

import contextlib
import logging
import threading
import time
import traceback
from collections.abc import AsyncIterator
from typing import Any, Optional

from strands import Agent, tool
from strands.types.tools import ToolContext

logger = logging.getLogger(__name__)

# MCP imports with error handling
MCP_IMPORT_ERROR = ""
try:
    import uvicorn
    from mcp import types
    from mcp.server.lowlevel import Server
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Mount
    from starlette.types import Receive, Scope, Send

    HAS_MCP = True
except ImportError as e:
    HAS_MCP = False
    MCP_IMPORT_ERROR = str(e)


# Global state to track MCP servers
_server_state = {
    "servers": {},  # Map of server_id -> server_info
    "default_server": None,  # ID of the default server
}


@tool
def mcp_server(
    action: str,
    server_id: str = "default",
    transport: str = "http",
    port: int = 8000,
    tools: Optional[list[str]] = None,
    expose_agent: bool = True,
    stateless: bool = False,
    agent: Any = None,
) -> dict[str, Any]:
    """Turn the agent into an MCP server, exposing agent tools as MCP tools.

    This tool follows the MCP (Model Context Protocol) specification and implements
    production-ready server patterns using StreamableHTTPSessionManager.

    Transports:
        - **http + stateless=True**: Multi-node ready, horizontally scalable, no session state (background)
        - **http + stateless=False**: Session persistence, single-node deployments (background)
        - **stdio**: Direct stdin/stdout communication for local MCP clients (foreground, blocking)

    Args:
        action: Action to perform - "start", "stop", "status", "list"
        server_id: Unique identifier for this server instance (default: "default")
        transport: Transport type - "http" (StreamableHTTP, background) or "stdio" (foreground, blocking)
        port: Port for HTTP server (only used when transport="http", default: 8000)
        tools: Optional list of tool names to expose. If None, exposes all tools except mcp_server itself
        expose_agent: Whether to expose "invoke_agent" tool for full agent conversations (default: True)
        stateless: If True, creates fresh transport per request with no session state.
                  Enables horizontal scaling across multiple nodes (default: False)
        agent: Parent agent instance (auto-injected by Strands framework)

    Returns:
        Result dictionary with status and content

    Examples:
        # Start HTTP server (background thread)
        agent("start mcp server on port 8000")

        # Start stdio server (foreground, blocking - for CLI/Claude Desktop)
        agent.tool.mcp_server(action="start", transport="stdio", agent=agent)

        # Start stateless server (production, multi-node ready)
        agent("start stateless mcp server on port 8000")

        # Start with specific tools only
        agent("start mcp server with tools: calculator, file_read")

    Notes:
        - **stdio transport**: Runs in FOREGROUND (blocks current thread) - use for CLI entrypoints
        - **http transport**: Runs in BACKGROUND (daemon thread) - use for long-running servers
        - **stateless mode**: Recommended for production deployments with load balancing
        - **stateful mode**: Recommended for development and single-node deployments
        - Agent parameter is auto-injected by Strands - don't pass manually
    """
    try:
        # Check if MCP is installed
        if not HAS_MCP:
            return {
                "status": "error",
                "content": [
                    {
                        "text": f"❌ MCP not installed: {MCP_IMPORT_ERROR}\n\n"
                        f"Install with: pip install mcp starlette uvicorn"
                    }
                ],
            }

        # Route to appropriate handler
        if action == "start":
            return _start_mcp_server(server_id, transport, port, tools, expose_agent, stateless, agent)
        elif action == "stop":
            return _stop_mcp_server(server_id)
        elif action == "status":
            return _get_mcp_status()
        elif action == "list":
            return _list_mcp_servers()
        else:
            return {
                "status": "error",
                "content": [{"text": f"❌ Unknown action: {action}\n\nValid actions: start, stop, status, list"}],
            }

    except Exception as e:
        logger.exception("MCP server tool error")
        return {
            "status": "error",
            "content": [{"text": f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"}],
        }


def _start_mcp_server(
    server_id: str,
    transport: str,
    port: int,
    tools_filter: Optional[list[str]],
    expose_agent: bool,
    stateless: bool,
    agent: Any,
) -> dict[str, Any]:
    """Start an MCP server exposing agent tools.

    This function implements the core server startup logic following MCP SDK patterns:
    1. Validates agent and tool availability
    2. Creates MCP Server instance with tool handlers
    3. Starts server:
       - **stdio**: Runs in FOREGROUND (blocks current thread) via asyncio.run()
       - **http**: Runs in BACKGROUND (daemon thread) for non-blocking operation
    4. Returns status with connection details

    Args:
        server_id: Unique identifier for this server
        transport: "http" for StreamableHTTP (background) or "stdio" for stdin/stdout (foreground)
        port: HTTP port (only for http transport)
        tools_filter: Optional list of tool names to expose
        expose_agent: Whether to expose invoke_agent capability
        stateless: If True, creates fresh transport per request (multi-node ready)
        agent: Parent Strands agent instance

    Returns:
        Status dictionary with server details or error message
    """
    if server_id in _server_state["servers"]:
        return {
            "status": "error",
            "content": [{"text": f"❌ Server '{server_id}' is already running"}],
        }

    if not agent:
        return {
            "status": "error",
            "content": [{"text": "❌ Tool context not available"}],
        }

    # Get all agent tools
    all_tools = agent.tool_registry.get_all_tools_config()
    if not all_tools:
        return {"status": "error", "content": [{"text": "❌ No tools found in agent"}]}

    # Filter tools based on tools_filter parameter
    if tools_filter:
        # Only include specified tools
        agent_tools = {name: spec for name, spec in all_tools.items() if name in tools_filter and name != "mcp_server"}
        if not agent_tools and not expose_agent:
            return {
                "status": "error",
                "content": [{"text": f"❌ No matching tools found. Available: {list(all_tools.keys())}"}],
            }
    else:
        # Exclude mcp_server tool itself to avoid recursion
        agent_tools = {name: spec for name, spec in all_tools.items() if name != "mcp_server"}

    logger.debug(f"Creating MCP server with {len(agent_tools)} tools: {list(agent_tools.keys())}")

    try:
        # Create low-level MCP server following MCP SDK patterns
        # This uses mcp.server.lowlevel.Server which provides the @server.list_tools()
        # and @server.call_tool() decorators for registering handlers
        server = Server(f"strands-agent-{server_id}")

        # Create MCP Tool objects from agent tools
        mcp_tools = []
        for tool_name, tool_spec in agent_tools.items():
            description = tool_spec.get("description", f"Agent tool: {tool_name}")
            input_schema = {}

            if "inputSchema" in tool_spec:
                if "json" in tool_spec["inputSchema"]:
                    input_schema = tool_spec["inputSchema"]["json"]
                else:
                    input_schema = tool_spec["inputSchema"]

            mcp_tools.append(
                types.Tool(
                    name=tool_name,
                    description=description,
                    inputSchema=input_schema,
                )
            )

        # Add agent invocation tool if requested
        if expose_agent:
            agent_invoke_tool = types.Tool(
                name="invoke_agent",
                description=(
                    f"Invoke the full {agent.name} agent with a natural language prompt. "
                    "Use this for complex queries that require reasoning across multiple tools "
                    "or when you need a conversational response from the agent."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt or query to send to the agent",
                        }
                    },
                    "required": ["prompt"],
                },
            )
            mcp_tools.append(agent_invoke_tool)

        logger.debug(f"Created {len(mcp_tools)} MCP tools (agent invocation: {expose_agent})")

        # Capture transport in closure for call_tool handler
        _transport = transport

        # Register list_tools handler following MCP SDK pattern
        @server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """Return list of available MCP tools.

            This handler is called when MCP clients request the available tools.
            It returns the pre-built list of MCP Tool objects converted from
            Strands agent tools.
            """
            logger.debug(f"list_tools called, returning {len(mcp_tools)} tools")
            return mcp_tools

        # Register call_tool handler
        @server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls from MCP clients.

            This handler:
            1. Validates tool existence
            2. Handles agent invocation specially
            3. Calls agent tools with proper error handling
            4. Converts results to MCP TextContent format
            5. Forces non-interactive mode for stdio to avoid stream conflicts
            """
            try:
                logger.debug(f"call_tool: name={name}, arguments={arguments}")

                # Handle agent invocation tool
                if name == "invoke_agent" and expose_agent:
                    prompt = arguments.get("prompt")
                    if not prompt:
                        return [
                            types.TextContent(
                                type="text",
                                text="❌ Error: 'prompt' parameter is required",
                            )
                        ]

                    logger.debug(f"Invoking agent with prompt: {prompt[:100]}...")

                    # Get the parent agent's configuration
                    # Access tools directly from registry dictionary
                    tools_for_invocation = [
                        agent.tool_registry.registry[tool_name]
                        for tool_name in agent_tools.keys()
                        if tool_name in agent.tool_registry.registry
                    ]

                    # Prepare extra kwargs for observability and callbacks
                    extra_kwargs = {}
                    if hasattr(agent, "callback_handler") and agent.callback_handler:
                        extra_kwargs["callback_handler"] = agent.callback_handler

                    # Create fresh agent with same configuration but clean message history
                    # Inherits: model, tools, trace_attributes, callback_handler
                    fresh_agent = Agent(
                        name=f"{agent.name}-invocation",
                        model=agent.model,
                        messages=[],  # Empty message history (clean state)
                        tools=tools_for_invocation,
                        system_prompt=agent.system_prompt if hasattr(agent, "system_prompt") else None,
                        trace_attributes=agent.trace_attributes if hasattr(agent, "trace_attributes") else {},
                        **extra_kwargs,
                    )

                    # Call the fresh agent
                    result = fresh_agent(prompt)

                    # Extract text response from agent result
                    response_text = str(result)

                    logger.debug(f"Agent invocation complete, response length: {len(response_text)}")

                    return [types.TextContent(type="text", text=response_text)]

                # Check if tool exists in agent
                if name not in agent_tools:
                    return [types.TextContent(type="text", text=f"❌ Unknown tool: {name}")]

                # Call the agent tool
                # Note: For stdio transport, we should force non_interactive=True to avoid
                # stdin/stdout conflicts. However, most Strands tools don't have this
                # parameter yet, so we call normally and let the tool handle it.
                tool_caller = getattr(agent.tool, name.replace("-", "_"))

                # For stdio transport, try to pass non_interactive=True if the tool supports it
                # This prevents tools like shell from trying to use stdin/stdout
                if _transport == "stdio":
                    try:
                        # Try calling with non_interactive parameter
                        result = tool_caller(**arguments, non_interactive=True)
                    except TypeError:
                        # Tool doesn't support non_interactive, call normally
                        logger.debug(f"Tool '{name}' doesn't support non_interactive parameter")
                        result = tool_caller(**arguments)
                else:
                    result = tool_caller(**arguments)

                logger.debug(f"Tool '{name}' execution complete")

                # Convert result to MCP TextContent format
                mcp_content = []
                if isinstance(result, dict) and "content" in result:
                    # Strands tool result format
                    for item in result.get("content", []):
                        if isinstance(item, dict) and "text" in item:
                            mcp_content.append(types.TextContent(type="text", text=item["text"]))
                else:
                    # Direct string or other result
                    mcp_content.append(types.TextContent(type="text", text=str(result)))

                return (
                    mcp_content
                    if mcp_content
                    else [types.TextContent(type="text", text="✅ Tool executed successfully")]
                )

            except Exception as e:
                logger.exception(f"Error calling tool '{name}'")
                return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]

        # Record server state
        _server_state["servers"][server_id] = {
            "server": server,
            "transport": transport,
            "port": port,
            "stateless": stateless,
            "tools": list(agent_tools.keys()),
            "start_time": time.time(),
            "status": "starting",
            "expose_agent": expose_agent,
        }

        if _server_state["default_server"] is None:
            _server_state["default_server"] = server_id

        # For stdio transport: Run in FOREGROUND (blocks current thread)
        # This is used by CLI entrypoints that need to keep stdio server alive
        if transport == "stdio":
            logger.info(f"Starting MCP server '{server_id}' in stdio mode (foreground, blocking)")
            _server_state["servers"][server_id]["status"] = "running"

            # Run stdio server directly - BLOCKS until terminated
            import asyncio
            from mcp.server.stdio import stdio_server

            async def run_stdio() -> None:
                """Run stdio server in foreground."""
                async with stdio_server() as streams:
                    await server.run(streams[0], streams[1], server.create_initialization_options())

            # This blocks the current thread - perfect for CLI entrypoints!
            asyncio.run(run_stdio())

            # When we get here, server has stopped
            if server_id in _server_state["servers"]:
                del _server_state["servers"][server_id]

            return {
                "status": "success",
                "content": [{"text": f"✅ MCP server '{server_id}' stopped"}],
            }

        # For http transport: Run in BACKGROUND (daemon thread, non-blocking)
        # This allows the agent to continue processing other tasks
        server_thread = threading.Thread(
            target=_run_mcp_server,
            args=(server, transport, port, stateless, server_id, len(mcp_tools)),
            daemon=True,
        )

        _server_state["servers"][server_id]["thread"] = server_thread
        server_thread.start()

        # Give server time to start
        time.sleep(2)

        # Check status
        if server_id not in _server_state["servers"]:
            return {
                "status": "error",
                "content": [{"text": f"❌ Server '{server_id}' failed to start"}],
            }

        server_info = _server_state["servers"][server_id]
        if server_info["status"] == "error":
            error_msg = server_info.get("error", "Unknown error")
            return {
                "status": "error",
                "content": [{"text": f"❌ Server '{server_id}' failed: {error_msg}"}],
            }

        # Update to running
        _server_state["servers"][server_id]["status"] = "running"

        # Build status message
        tool_list = "\n".join(f"  • {tool.name}" for tool in mcp_tools[:10])
        if len(mcp_tools) > 10:
            tool_list += f"\n  ... and {len(mcp_tools) - 10} more"

        if expose_agent:
            tool_list += "\n  • invoke_agent (full agent invocation) ✨"

        mode_desc = "stateless (multi-node ready)" if stateless else "stateful (session persistence)"
        message = (
            f"✅ MCP server '{server_id}' started on port {port}\n\n"
            f"📊 Mode: {mode_desc}\n"
            f"🔧 Exposed {len(mcp_tools)} tools:\n"
            f"{tool_list}\n\n"
            f"🔗 Connect at: http://localhost:{port}/mcp"
        )

        return {"status": "success", "content": [{"text": message}]}

    except Exception as e:
        logger.exception("Error starting MCP server")

        if server_id in _server_state["servers"]:
            _server_state["servers"][server_id]["status"] = "error"
            _server_state["servers"][server_id]["error"] = str(e)

        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to start MCP server: {str(e)}"}],
        }


def _run_mcp_server(
    server: "Server", transport: str, port: int, stateless: bool, server_id: str, tool_count: int
) -> None:
    """Run MCP server in background thread with StreamableHTTPSessionManager.

    This function follows MCP SDK patterns for server execution:
    - HTTP transport: Uses StreamableHTTPSessionManager with Starlette + Uvicorn (background)
    - stdio transport: Not used here - stdio runs in foreground via _start_mcp_server()

    The server runs in a daemon background thread to avoid blocking the main agent.

    Args:
        server: MCP Server instance with registered handlers
        transport: "http" (only http supported here, stdio runs in foreground)
        port: HTTP port
        stateless: If True, creates fresh transport per request (no session state)
        server_id: Server identifier for logging and tracking
        tool_count: Number of exposed tools (for logging)
    """
    try:
        logger.debug(
            f"Starting MCP server: server_id={server_id}, transport={transport}, port={port}, stateless={stateless}"
        )

        if transport == "http":
            # HTTP mode using StreamableHTTPSessionManager
            # This follows the pattern from python-sdk/src/mcp/server/streamable_http_manager.py

            # Create session manager with configurable stateless mode
            # - stateless=True: Multi-node ready, no session persistence
            # - stateless=False: Session persistence, single-node deployments
            session_manager = StreamableHTTPSessionManager(
                app=server,
                event_store=None,  # No resumability support for now
                json_response=False,  # Use SSE streams (not pure JSON)
                stateless=stateless,  # Configurable stateless mode
            )

            async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
                """Handle streamable HTTP requests.

                This is the ASGI application handler that processes incoming HTTP
                requests and routes them through the session manager.
                """
                await session_manager.handle_request(scope, receive, send)

            @contextlib.asynccontextmanager
            async def lifespan(app: Starlette) -> AsyncIterator[None]:
                """Lifespan context manager for session manager.

                This manages the lifecycle of the StreamableHTTPSessionManager,
                ensuring proper startup and shutdown of resources.
                """
                async with session_manager.run():
                    logger.info(
                        f"MCP server '{server_id}' running with StreamableHTTPSessionManager (stateless={stateless})"
                    )
                    try:
                        yield
                    finally:
                        logger.info(f"MCP server '{server_id}' shutting down...")

            # Create ASGI application following Starlette patterns
            starlette_app = Starlette(
                debug=True,
                routes=[
                    Mount("/mcp", app=handle_streamable_http),
                ],
                lifespan=lifespan,
            )

            # Wrap with CORS middleware for cross-origin support
            # This allows browser-based MCP clients to connect
            starlette_app = CORSMiddleware(
                starlette_app,
                allow_origins=["*"],  # Allow all origins - adjust for production
                allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
                expose_headers=["Mcp-Session-Id"],  # Expose session ID header
            )

            logger.debug(f"Starting Uvicorn server on 0.0.0.0:{port}")
            uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level="info")
        else:
            logger.error(f"Unsupported transport: {transport} (only 'http' supported in background thread)")

    except Exception as e:
        logger.exception("Error in _run_mcp_server")

        if server_id in _server_state["servers"]:
            _server_state["servers"][server_id]["status"] = "error"
            _server_state["servers"][server_id]["error"] = str(e)


def _stop_mcp_server(server_id: str) -> dict[str, Any]:
    """Stop a running MCP server."""
    if server_id not in _server_state["servers"]:
        return {
            "status": "error",
            "content": [{"text": f"❌ Server '{server_id}' is not running"}],
        }

    server_info = _server_state["servers"][server_id]
    server_info["status"] = "stopping"

    # Note: Graceful shutdown is complex with threading + async
    # For now, daemon threads will be cleaned up on process exit

    del _server_state["servers"][server_id]

    if _server_state["default_server"] == server_id:
        _server_state["default_server"] = next(iter(_server_state["servers"])) if _server_state["servers"] else None

    return {
        "status": "success",
        "content": [{"text": f"✅ MCP server '{server_id}' stopped"}],
    }


def _get_mcp_status() -> dict[str, Any]:
    """Get status of all MCP servers."""
    if not _server_state["servers"]:
        return {"status": "success", "content": [{"text": "ℹ️ No MCP servers running"}]}

    lines = ["📡 **MCP Server Status**\n"]

    for server_id, server_info in _server_state["servers"].items():
        uptime = time.time() - server_info["start_time"]
        uptime_str = f"{int(uptime // 60)}m {int(uptime % 60)}s"

        default_marker = " (default)" if server_id == _server_state["default_server"] else ""
        status_emoji = {
            "running": "✅",
            "starting": "🔄",
            "stopping": "⏸️",
            "error": "❌",
        }.get(server_info["status"], "❓")

        lines.append(f"\n**{server_id}{default_marker}**")
        lines.append(f"  • Status: {status_emoji} {server_info['status']}")
        lines.append(f"  • Transport: {server_info['transport']}")

        if server_info["transport"] == "http":
            lines.append(f"  • Port: {server_info['port']}")
            lines.append(f"  • Connect: http://localhost:{server_info['port']}/mcp")
            mode_type = "stateless (multi-node)" if server_info.get("stateless", False) else "stateful (single-node)"
            lines.append(f"  • Type: {mode_type}")

        lines.append(f"  • Uptime: {uptime_str}")
        lines.append(f"  • Tools: {len(server_info['tools'])} exposed")

        if server_info.get("expose_agent"):
            lines.append(f"  • Agent Invocation: ✅ Enabled")

        if server_info["status"] == "error" and "error" in server_info:
            lines.append(f"  • Error: {server_info['error']}")

    return {"status": "success", "content": [{"text": "\n".join(lines)}]}


def _list_mcp_servers() -> dict[str, Any]:
    """List running MCP servers."""
    if not _server_state["servers"]:
        return {"status": "success", "content": [{"text": "ℹ️ No MCP servers running"}]}

    lines = ["📋 **Running MCP Servers**\n"]

    for server_id, server_info in _server_state["servers"].items():
        default_marker = " (default)" if server_id == _server_state["default_server"] else ""
        mode_info = f"port {server_info['port']}" if server_info["transport"] == "http" else "stdio"

        lines.append(
            f"• {server_id}{default_marker}: {server_info['status']}, " f"{server_info['transport']} ({mode_info})"
        )

    return {"status": "success", "content": [{"text": "\n".join(lines)}]}
