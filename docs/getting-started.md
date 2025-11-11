---
layout: default
title: Getting Started
nav_order: 2
---

# Getting Started

This guide will walk you through installing and using `strands-mcp-server` to expose your Strands Agent as an MCP server or connect to remote MCP servers.

---

## Installation

```bash
pip install strands-mcp-server
```

**With uv (recommended):**

```bash
uv pip install strands-mcp-server
```

---

## Three Usage Patterns

### 1. Expose Your Agent (Server)

Turn your Strands Agent into an MCP server that others can connect to.

```python
from strands import Agent
from strands_tools import calculator, shell, file_read
from strands_mcp_server import mcp_server

# Create agent with tools
agent = Agent(
    name="my-agent",
    tools=[calculator, shell, file_read, mcp_server]
)

# Start HTTP server (background)
agent("start mcp server on port 8000")
```

**Your agent is now accessible at:** `http://localhost:8000/mcp`

**Exposed tools:**
- `calculator` - Your agent's calculator tool
- `shell` - Your agent's shell tool
- `file_read` - Your agent's file_read tool
- `invoke_agent` - Full conversational access to agent

---

### 2. Connect to Servers (Client)

Connect your agent to remote MCP servers and use their tools.

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# Connect to server
agent.tool.mcp_client(
    action="connect",
    connection_id="remote-agent",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# List available tools
agent.tool.mcp_client(
    action="list_tools",
    connection_id="remote-agent"
)

# Call remote tool
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote-agent",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
print(result)
```

---

### 3. CLI for Claude Desktop

The CLI provides a stdio MCP server for Claude Desktop and similar tools.

**Local mode** (expose `./tools/` directory):

```bash
uvx strands-mcp-server --cwd /absolute/path/to/project
```

**Proxy mode** (bridge to HTTP server):

```bash
# Terminal 1: Start your agent
python my_agent.py  # Starts HTTP server on port 8000

# Terminal 2: Start proxy
uvx strands-mcp-server --upstream-url http://localhost:8000/mcp
```

**Claude Desktop config:**

```json
{
  "mcpServers": {
    "my-agent": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/absolute/path/to/project"
      ]
    }
  }
}
```

---

## Complete Example

Let's build a complete workflow:

### Step 1: Create Server Agent

**server.py:**

```python
from strands import Agent
from strands_tools import calculator, file_read
from strands_mcp_server import mcp_server

# Create agent
agent = Agent(
    name="data-agent",
    tools=[calculator, file_read, mcp_server]
)

# Start server
agent.tool.mcp_server(
    action="start",
    port=8001,
    agent=agent
)

# Keep running
import time
while True:
    time.sleep(60)
```

Run: `python server.py`

### Step 2: Create Client Agent

**client.py:**

```python
from strands import Agent
from strands_mcp_server import mcp_client

# Create agent with MCP client
agent = Agent(
    name="coordinator",
    tools=[mcp_client]
)

# Connect to server
agent.tool.mcp_client(
    action="connect",
    connection_id="data",
    transport="http",
    server_url="http://localhost:8001/mcp"
)

# Use remote tools
agent("""
Connect to the data agent and:
1. List all available tools
2. Calculate 999 * 888
3. Read the contents of README.md
""")
```

Run: `python client.py`


## Next Steps

- [API Reference](api-reference.html) - Detailed tool documentation
- [CLI Usage](cli.html) - Command-line options
- [Examples](examples.html) - More code samples
- [Claude Desktop](claude-desktop.html) - Integration guide

---

## Troubleshooting

### Port already in use

```bash
lsof -i :8000
kill -9 <PID>
```

### Connection refused

Verify server is running:

```bash
curl http://localhost:8000/mcp
```

### Tools not loading (CLI)

Use absolute paths and debug mode:

```bash
uvx strands-mcp-server --cwd /absolute/path --debug
```

Check Claude Desktop logs:

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```
