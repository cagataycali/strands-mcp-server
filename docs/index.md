---
layout: default
title: Home
nav_order: 1
---

# strands-mcp-server

**Bidirectional MCP integration for Strands Agents.**

Expose your Strands Agent as an MCP server or connect to any MCP server as a client.

[![PyPI](https://img.shields.io/pypi/v/strands-mcp-server.svg)](https://pypi.org/project/strands-mcp-server/)

---

## What is this?

`strands-mcp-server` provides two Python tools and a CLI for integrating [Strands Agents](https://strandsagents.com) with the [Model Context Protocol](https://modelcontextprotocol.io/):

- **`mcp_server`** - Expose your agent's tools as an MCP server
- **`mcp_client`** - Connect to and use remote MCP servers
- **CLI** - stdio server for Claude Desktop/Kiro integration

---

## Installation

```bash
pipx install strands-mcp-server
```

---

## Quick Example

### Server: Expose Your Agent

```python
from strands import Agent
from strands_tools import calculator, shell
from strands_mcp_server import mcp_server

agent = Agent(tools=[calculator, shell, mcp_server])
agent("start mcp server on port 8000")
```

### Client: Connect to Servers

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])
agent.tool.mcp_client(
    action="connect",
    connection_id="remote",
    transport="http",
    server_url="http://localhost:8000/mcp"
)
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Bidirectional** | Act as server or client |
| **Multiple transports** | HTTP, stdio, SSE |
| **Claude Desktop** | Direct integration via CLI |
| **Stateless mode** | Production-ready, multi-node |
| **Model switching** | Change models per invocation |
| **Hot reload** | Auto-load tools from `./tools/` |
| **Full agent access** | `invoke_agent` tool included |

---

## Documentation

- [Getting Started](getting-started.html) - Quick start guide
- [API Reference](api-reference.html) - Tool documentation
- [CLI Usage](cli.html) - Command-line interface
- [Examples](examples.html) - Code samples
- [Claude Desktop](claude-desktop.html) - Integration guide

---

## Use Cases

### 1. Agent-to-Agent Communication

Multiple specialized agents sharing tools via MCP:

```python
# Data agent exposes analysis tools
data_agent = Agent(tools=[calculator, file_read, mcp_server])
data_agent.tool.mcp_server(action="start", port=8001, agent=data_agent)

# Coordinator uses remote tools
coordinator = Agent(tools=[mcp_client])
coordinator("connect to http://localhost:8001/mcp as data")
coordinator("use data agent to analyze numbers.csv")
```

### 2. Claude Desktop Integration

Expose your agent's tools directly to Claude Desktop:

```bash
uvx strands-mcp-server --cwd /path/to/project
```

### 3. Production Deployment

Multi-node stateless servers with load balancing:

```python
agent.tool.mcp_server(
    action="start",
    stateless=True,  # No session state
    agent=agent
)
```

---

## Links

- **GitHub**: [strands-mcp-server](https://github.com/cagataycali/strands-mcp-server)
- **PyPI**: [strands-mcp-server](https://pypi.org/project/strands-mcp-server/)
- **Strands Agents**: [strandsagents.com](https://strandsagents.com)
- **MCP Spec**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

---

## License

Apache 2.0
