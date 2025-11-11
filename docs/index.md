---
layout: default
title: Home
nav_order: 1
---

# strands-mcp-server

Bidirectional MCP integration for Strands Agents.

[![PyPI](https://img.shields.io/pypi/v/strands-mcp-server.svg)](https://pypi.org/project/strands-mcp-server/)

---

## Install

```bash
pip install strands-mcp-server
```

---

## Tools

- **mcp_server** - Expose agent as MCP server
- **mcp_client** - Connect to MCP servers
- **CLI** - stdio server for Claude Desktop/Kiro/...

---

## Quick Start

**Server:**
```python
from strands import Agent
from strands_mcp_server import mcp_server

agent = Agent(tools=[..., mcp_server])
agent("start mcp server on port 8000")
```

**Client:**
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
```

**CLI:**
```bash
uvx strands-mcp-server --cwd /path/to/project
```

---

## Links

- [Getting Started](getting-started.html)
- [API Reference](api-reference.html)
- [CLI Usage](cli.html)
- [Examples](examples.html)
- [Claude Desktop](claude-desktop.html)
- [GitHub](https://github.com/cagataycali/strands-mcp-server)
- [PyPI](https://pypi.org/project/strands-mcp-server/)
