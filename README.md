# strands-mcp-server

[![PyPI](https://img.shields.io/pypi/v/strands-mcp-server.svg)](https://pypi.org/project/strands-mcp-server/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Bidirectional MCP integration for Strands Agents.** Expose agents as MCP servers. Connect to any MCP server as a client.

```bash
pip install strands-mcp-server
```

---

## What This Does

This package provides two Python tools (`mcp_server` and `mcp_client`) and a CLI that connects Strands Agents to the Model Context Protocol ecosystem.

**Core functionality:**
- **mcp_server tool**: Turns a Strands Agent into an MCP server
- **mcp_client tool**: Connects to any MCP server and uses its tools
- **strands-mcp-server CLI**: stdio MCP server for Claude Desktop/Kiro integration

---

## Concepts

### The Model Context Protocol (MCP)

MCP is a protocol that allows AI applications to expose and consume "tools" (functions) over a standard interface. Think of it as an API specification for AI tool sharing.

**Key concepts:**
- **MCP Server**: Exposes tools that clients can call
- **MCP Client**: Connects to servers and calls their tools
- **Transport**: How messages are sent (HTTP, stdio, SSE)
- **Tools**: Functions with typed parameters and descriptions

### How This Package Works

```
┌─────────────────────────────┐
│    Your Strands Agent       │
│  tools: [calculator, ...]   │
└─────────────────────────────┘
            ↓
    ┌───────────────┐
    │  mcp_server   │  ← Tool that exposes agent
    └───────────────┘
            ↓
    MCP Protocol (HTTP/stdio)
            ↓
┌─────────────────────────────┐
│   MCP Clients               │
│  • Claude Desktop           │
│  • Other agents             │
│  • Custom clients           │
└─────────────────────────────┘
```

**Reverse direction:**

```
┌─────────────────────────────┐
│    Your Strands Agent       │
└─────────────────────────────┘
            ↓
    ┌───────────────┐
    │  mcp_client   │  ← Tool that connects to servers
    └───────────────┘
            ↓
    MCP Protocol (HTTP/stdio/SSE)
            ↓
┌─────────────────────────────┐
│   Remote MCP Server         │
│   (another agent or service)│
└─────────────────────────────┘
```

---

## Usage

### 1. As a Server (Expose Your Agent)

Use the `mcp_server` tool to expose your agent's tools to MCP clients.

```python
from strands import Agent
from strands_tools import calculator, shell, file_read
from strands_mcp_server import mcp_server

agent = Agent(
    name="my-agent",
    tools=[calculator, shell, file_read, mcp_server]
)

# Start HTTP server (runs in background thread)
agent("start mcp server on port 8000")

# Server is now running at http://localhost:8000/mcp
# Clients can connect and use calculator, shell, file_read tools
```

**What happens:**
1. Agent's tools are converted to MCP tool definitions
2. HTTP server starts on port 8000 with MCP protocol handlers
3. Clients send JSON-RPC requests to list/call tools
4. Server executes tools using agent's tool registry
5. Results returned in MCP format

**Transport modes:**

| Transport | Execution | Use Case |
|-----------|-----------|----------|
| `http` | Background thread (non-blocking) | Production servers, multi-node |
| `stdio` | Foreground (blocks current thread) | CLI entrypoints, Claude Desktop |

```python
# HTTP: Returns immediately, server runs in background
agent.tool.mcp_server(action="start", transport="http", port=8000, agent=agent)

# stdio: Blocks until terminated (for CLI tools)
agent.tool.mcp_server(action="start", transport="stdio", agent=agent)
```

**Stateless mode:**

For production deployments with load balancing, use stateless mode. Each request creates a fresh session with no state persistence.

```python
agent.tool.mcp_server(
    action="start",
    transport="http",
    port=8000,
    stateless=True,  # Enable stateless mode
    agent=agent
)
```

### 2. As a Client (Connect to Other Servers)

Use the `mcp_client` tool to connect your agent to remote MCP servers.

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# Connect to a server
agent.tool.mcp_client(
    action="connect",
    connection_id="remote-agent",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# List available tools
result = agent.tool.mcp_client(
    action="list_tools",
    connection_id="remote-agent"
)

# Call a remote tool
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote-agent",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

**What happens:**
1. Client establishes connection to remote server
2. Retrieves tool definitions from server
3. Calls tools by sending JSON-RPC requests
4. Server executes tool and returns result
5. Client receives and returns formatted result

**Supported transports:**

```python
# HTTP (most common)
agent.tool.mcp_client(
    action="connect",
    connection_id="server1",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# stdio (launch subprocess)
agent.tool.mcp_client(
    action="connect",
    connection_id="local",
    transport="stdio",
    command="python",
    args=["server.py"]
)

# SSE (server-sent events)
agent.tool.mcp_client(
    action="connect",
    connection_id="sse-server",
    transport="sse",
    server_url="http://localhost:8000/sse"
)
```

### 3. CLI for Claude Desktop/Kiro

The `strands-mcp-server` command provides a stdio MCP server for integration with Claude Desktop and similar tools.

**Two modes of operation:**

#### Local Mode

Exposes tools from a `./tools/` directory. Strands handles hot reloading automatically.

```bash
# Project structure:
# my-project/
#   tools/
#     weather.py  (with @tool decorator)
#     database.py (with @tool decorator)

strands-mcp-server --cwd /path/to/my-project
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "my-project": {
      "command": "strands-mcp-server",
      "args": ["--cwd", "/absolute/path/to/my-project"]
    }
  }
}
```

**What happens:**
1. CLI creates agent with `load_tools_from_directory=True`
2. Strands loads all `@tool` decorated functions from `./tools/`
3. Starts MCP server in stdio mode (reads stdin, writes stdout)
4. Claude Desktop communicates via stdio using MCP protocol
5. Tools execute in agent context, results returned to Claude

#### Proxy Mode

Acts as a bridge between stdio (Claude Desktop) and an HTTP MCP server.

```bash
# Terminal 1: Start your agent with HTTP server
python my_agent.py  # Uses mcp_server tool on port 8000

# Terminal 2: Not needed - Claude connects directly via config
```

**Claude Desktop config:**

```json
{
  "mcpServers": {
    "remote-agent": {
      "command": "strands-mcp-server",
      "args": ["--upstream-url", "http://localhost:8000/mcp"]
    }
  }
}
```

**What happens:**
1. CLI connects to upstream HTTP server as MCP client
2. Retrieves tool list from upstream
3. Creates stdio MCP server for Claude Desktop
4. Forwards all tool calls from Claude to upstream server
5. Returns upstream results back to Claude via stdio

**Why this exists:** Claude Desktop only speaks stdio MCP. If your agent runs an HTTP MCP server, the CLI bridges the protocols.

---

## API Reference

### mcp_server Tool

**Purpose:** Expose Strands Agent as MCP server.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | required | `start`, `stop`, `status`, or `list` |
| `server_id` | str | `"default"` | Unique identifier for this server |
| `transport` | str | `"http"` | `http` (background) or `stdio` (foreground) |
| `port` | int | `8000` | Port for HTTP server |
| `tools` | list[str] | `None` | Tool names to expose (None = all) |
| `expose_agent` | bool | `True` | Add `invoke_agent` tool for full conversations |
| `stateless` | bool | `False` | No session state (for multi-node) |
| `agent` | Agent | required | Parent agent (auto-injected) |

**Examples:**

```python
# Start HTTP server
agent("start mcp server on port 8000")

# Start with only specific tools
agent.tool.mcp_server(
    action="start",
    tools=["calculator", "file_read"],
    agent=agent
)

# Production stateless mode
agent.tool.mcp_server(
    action="start",
    stateless=True,
    agent=agent
)

# Get status
agent.tool.mcp_server(action="status", agent=agent)
```

### mcp_client Tool

**Purpose:** Connect to and use remote MCP servers.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | required | `connect`, `disconnect`, `list_tools`, `call_tool`, `list_connections` |
| `connection_id` | str | None | Identifier for this connection |
| `transport` | str | None | `http`, `stdio`, or `sse` |
| `server_url` | str | None | URL for http/sse transport |
| `command` | str | None | Command for stdio transport |
| `args` | list[str] | None | Arguments for stdio command |
| `tool_name` | str | None | Tool to call (for `call_tool` action) |
| `tool_args` | dict | None | Tool arguments (for `call_tool` action) |

**Examples:**

```python
# Connect
agent.tool.mcp_client(
    action="connect",
    connection_id="server1",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# List tools
agent.tool.mcp_client(
    action="list_tools",
    connection_id="server1"
)

# Call tool
agent.tool.mcp_client(
    action="call_tool",
    connection_id="server1",
    tool_name="calculator",
    tool_args={"expression": "2 + 2"}
)

# Disconnect
agent.tool.mcp_client(
    action="disconnect",
    connection_id="server1"
)
```

### CLI Options

```bash
strands-mcp-server [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--cwd PATH` | Working directory (for local mode) |
| `--upstream-url URL` | Upstream server URL (for proxy mode) |
| `--system-prompt TEXT` | Custom system prompt |
| `--no-agent-invocation` | Disable `invoke_agent` tool |
| `--debug` | Enable debug logging |

---

## Agent-to-Agent Communication

A common pattern: multiple specialized agents sharing tools via MCP.

```python
from strands import Agent
from strands_tools import calculator, http_request, file_read
from strands_mcp_server import mcp_server, mcp_client

# Agent 1: Data specialist
data_agent = Agent(
    name="data-agent",
    tools=[file_read, calculator, mcp_server]
)
data_agent.tool.mcp_server(
    action="start",
    port=8001,
    agent=data_agent
)

# Agent 2: Web specialist
web_agent = Agent(
    name="web-agent",
    tools=[http_request, mcp_server]
)
web_agent.tool.mcp_server(
    action="start",
    port=8002,
    agent=web_agent
)

# Coordinator agent
coordinator = Agent(
    name="coordinator",
    tools=[mcp_client]
)

# Connect to both specialists
coordinator.tool.mcp_client(
    action="connect",
    connection_id="data",
    transport="http",
    server_url="http://localhost:8001/mcp"
)

coordinator.tool.mcp_client(
    action="connect",
    connection_id="web",
    transport="http",
    server_url="http://localhost:8002/mcp"
)

# Use their specialized tools
coordinator("""
1. Use web agent to fetch data from https://api.example.com/data
2. Use data agent to analyze the numbers
3. Summarize the results
""")
```

**Why this works:**
- Each agent exposes its tools via MCP
- Coordinator doesn't need to have all tools
- Tools execute in their native agent context
- Clean separation of concerns

---

## Production Deployment

### Stateless Mode

For production with load balancing:

```python
agent.tool.mcp_server(
    action="start",
    transport="http",
    port=8000,
    stateless=True,  # No session state
    agent=agent
)
```

**What stateless means:**
- Each request gets a fresh transport/session
- No state persists between requests
- Can distribute requests across multiple nodes
- Load balancer doesn't need sticky sessions

**Example production server:**

```python
# production_server.py
from strands import Agent
from strands_mcp_server import mcp_server

agent = Agent(
    name="production-agent",
    tools=[...],
    load_tools_from_directory=True
)

agent.tool.mcp_server(
    action="start",
    transport="http",
    port=8000,
    stateless=True,
    agent=agent
)

# Keep running
import time
while True:
    time.sleep(60)
```

All instances can run identical code because of stateless mode. Load balancer can distribute requests freely.

---

## Technical Details

### Tool Conversion

Strands tools are automatically converted to MCP tool definitions:

```python
# Strands tool
{
    "name": "calculator",
    "description": "Perform calculations",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    }
}

# Becomes MCP Tool
types.Tool(
    name="calculator",
    description="Perform calculations",
    inputSchema={
        "type": "object",
        "properties": {
            "expression": {"type": "string"}
        },
        "required": ["expression"]
    }
)
```

### invoke_agent Tool

When `expose_agent=True` (default), an additional `invoke_agent` tool is added:

```python
{
    "name": "invoke_agent",
    "description": "Invoke full agent with a prompt",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"}
        },
        "required": ["prompt"]
    }
}
```

This allows clients to have full conversational access to the agent, not just individual tools.

**Implementation detail:** Creates a fresh agent instance with clean message history to avoid tool block mismatches.

### Transport Implementations

**HTTP (StreamableHTTP):**
- Uses `StreamableHTTPSessionManager` from MCP SDK
- Starlette ASGI app with Uvicorn server
- CORS middleware enabled
- Runs in daemon background thread

**stdio:**
- Uses `stdio_server()` from MCP SDK
- Reads JSON-RPC from stdin
- Writes JSON-RPC to stdout
- Blocks current thread (for CLI use)
- Logging goes to stderr (stdin/stdout reserved for protocol)

---

## Troubleshooting

### Tools not loading in CLI

**Check working directory:**
```bash
strands-mcp-server --cwd /absolute/path/to/project --debug
```

Verify `./tools/` exists relative to `--cwd` and contains `.py` files with `@tool` decorator.

### Connection refused

**Verify server is running:**
```bash
curl http://localhost:8000/mcp
```

Should return an HTTP response (not necessarily success, but should connect).

### Port already in use

**Find and kill process:**
```bash
lsof -i :8000
kill -9 <PID>
```

### stdio mode blocking

This is expected behavior. The `stdio` transport blocks the current thread and processes stdin/stdout continuously. Use `http` transport if you need non-blocking execution.

---

## Testing

```bash
pytest                          # All tests
pytest tests/test_mcp_server.py # Server tests only
pytest --cov                    # With coverage
```

Tests are covering:
- Server startup/shutdown
- Client connections
- Tool listing and calling
- Error handling
- Transport modes
- Stateless/stateful behavior

---

## Links

- **Documentation**: https://cagataycali.github.io/strands-mcp-server/
- **Source**: https://github.com/cagataycali/strands-mcp-server
- **PyPI**: https://pypi.org/project/strands-mcp-server/
- **Strands Agents**: https://strandsagents.com
- **MCP Specification**: https://modelcontextprotocol.io/

---

## License

Apache 2.0
