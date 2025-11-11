"""Strands MCP Server - Bidirectional MCP integration for Strands Agents.

This package provides complete Model Context Protocol (MCP) integration for Strands Agents,
enabling both server and client capabilities. Transform your agents into MCP servers that
expose tools to Claude Desktop and other MCP clients, or connect your agents to remote MCP
servers to use their tools.

Architecture:
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                    Strands Agent                            │
    │  ┌──────────────────┐           ┌──────────────────┐       │
    │  │   mcp_server     │           │   mcp_client     │       │
    │  │  (expose tools)  │           │ (consume tools)  │       │
    │  └──────────────────┘           └──────────────────┘       │
    └─────────────────────────────────────────────────────────────┘
              ↓                                  ↓
       MCP Protocol                       MCP Protocol
              ↓                                  ↓
    ┌─────────────────┐              ┌─────────────────┐
    │  MCP Clients    │              │  MCP Servers    │
    │ • Claude Desktop│              │ • Other Agents  │
    │ • Other Agents  │              │ • Remote APIs   │
    │ • Custom Clients│              │ • MCP Services  │
    └─────────────────┘              └─────────────────┘
    ```

Components:

1. **mcp_server** - Turn agent into MCP server
   - Exposes agent tools as MCP tools
   - Optional full agent invocation capability
   - Multiple transport modes (HTTP, stdio)
   - Stateless and stateful session management
   - Production-ready with StreamableHTTPSessionManager

2. **mcp_client** - Connect to remote MCP servers
   - Discover and call remote MCP tools
   - Multiple transport support (HTTP, stdio, SSE)
   - Connection management and persistence
   - Session handling with ClientSession

3. **CLI** - Command-line MCP server
   - stdio mode for Claude Desktop/Kiro integration
   - Local mode: Expose tools from ./tools/ directory
   - Proxy mode: Bridge stdio to upstream HTTP server
   - Hot reload support via Strands native tool loading

Key Features:

**Server Capabilities:**
- **Stateless HTTP**: Multi-node ready, horizontally scalable
- **Stateful HTTP**: Session persistence for single-node
- **stdio Mode**: Direct stdin/stdout for CLI integration
- **Tool Filtering**: Expose specific tools only
- **Agent Invocation**: Full conversational access
- **CORS Support**: Browser-based client compatibility

**Client Capabilities:**
- **Multi-transport**: HTTP, stdio, SSE connections
- **Tool Discovery**: List available remote tools
- **Tool Execution**: Call remote tools with arguments
- **Connection Management**: Persistent session tracking
- **Error Handling**: Comprehensive error recovery

**Production Features:**
- StreamableHTTPSessionManager for production-grade HTTP
- Background thread execution for non-blocking servers
- Proper ASGI lifecycle management
- Comprehensive logging and error tracking
- Daemon thread cleanup

Usage Examples:

**1. As Server (Expose Agent):**
```python
from strands import Agent
from strands_tools import calculator, shell, file_read
from strands_mcp_server import mcp_server

agent = Agent(tools=[calculator, shell, file_read, mcp_server])

# Start HTTP server (background)
agent("start mcp server on port 8000")

# Stateless mode for production (multi-node)
agent("start stateless mcp server on port 8000")

# With specific tools only
agent.tool.mcp_server(
    action="start",
    tools=["calculator", "file_read"],
    agent=agent
)

# stdio mode (foreground, blocking - for CLI)
agent.tool.mcp_server(
    action="start",
    transport="stdio",
    agent=agent
)
```

**2. As Client (Connect to Remote Servers):**
```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# Connect to HTTP server
agent.tool.mcp_client(
    action="connect",
    connection_id="remote-agent",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# List remote tools
agent.tool.mcp_client(
    action="list_tools",
    connection_id="remote-agent"
)

# Call remote tool
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote-agent",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

**3. CLI for Claude Desktop:**
```bash
# Local mode: Load tools from ./tools/ directory
strands-mcp-server --cwd /path/to/project

# Proxy mode: Bridge stdio to upstream HTTP server
strands-mcp-server --upstream-url http://localhost:8000/mcp

# With custom system prompt
strands-mcp-server --system-prompt "You are a helpful assistant"

# Debug mode
strands-mcp-server --debug
```

**Claude Desktop Config (Local):**
```json
{
  "mcpServers": {
    "strands-tools": {
      "command": "strands-mcp-server",
      "args": ["--cwd", "/absolute/path/to/project"]
    }
  }
}
```

**Claude Desktop Config (Proxy):**
```json
{
  "mcpServers": {
    "strands-proxy": {
      "command": "strands-mcp-server",
      "args": ["--upstream-url", "http://localhost:8000/mcp"]
    }
  }
}
```

**Agent-to-Agent Communication:**
```python
# Server agent
data_agent = Agent(tools=[file_read, calculator, mcp_server])
data_agent.tool.mcp_server(action="start", port=8001, agent=data_agent)

# Client agent
coordinator = Agent(tools=[mcp_client])
coordinator.tool.mcp_client(
    action="connect",
    connection_id="data",
    transport="http",
    server_url="http://localhost:8001/mcp"
)

# Use remote tools
coordinator("use data agent's calculator to compute 42 * 89")
```

Transport Modes:

**HTTP Transport (Background):**
- Runs in daemon thread (non-blocking)
- StreamableHTTPSessionManager
- CORS middleware enabled
- Uvicorn + Starlette ASGI
- Port-based connection

**stdio Transport (Foreground):**
- Blocks current thread
- Direct stdin/stdout communication
- Required for Claude Desktop
- Logging to stderr only
- Process-based connection

**Stateless vs Stateful:**
- **Stateless**: Fresh session per request, multi-node ready, horizontally scalable
- **Stateful**: Session persistence, single-node, connection state maintained

References:
- MCP Specification: https://spec.modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Strands Agents: https://strandsagents.com
- Project Repository: https://github.com/cagataycali/strands-mcp-server
"""

from strands_mcp_server.mcp_client import mcp_client
from strands_mcp_server.mcp_server import mcp_server

__version__ = "0.1.0"
__all__ = ["mcp_server", "mcp_client"]
