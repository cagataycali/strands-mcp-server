---
layout: default
title: Getting Started
nav_order: 2
---

# Getting Started

---

## Install

```bash
pip install strands-mcp-server
```

---

## Server Mode

Expose your agent's tools:

```python
from strands import Agent
from strands_mcp_server import mcp_server

agent = Agent(tools=[mcp_server])
agent("start mcp server on port 8000")
# Running at http://localhost:8000/mcp
```

---

## Client Mode

Connect to remote servers:

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# Connect
agent.tool.mcp_client(
    action="connect",
    connection_id="remote",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# Call tool
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

---

## CLI Mode

For Claude Desktop:

```bash
uvx strands-mcp-server --cwd /path/to/project
```

**Config:**
```json
{
  "mcpServers": {
    "my-agent": {
      "command": "uvx",
      "args": ["strands-mcp-server", "--cwd", "/path/to/project"]
    }
  }
}
```

---

## Troubleshooting

**Port in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Connection refused:**
```bash
curl http://localhost:8000/mcp
```

**Tools not loading:**
```bash
uvx strands-mcp-server --cwd /absolute/path --debug
tail -f ~/Library/Logs/Claude/mcp*.log
```
