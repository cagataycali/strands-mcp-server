# strands-mcp-server

[![PyPI](https://img.shields.io/pypi/v/strands-mcp-server.svg)](https://pypi.org/project/strands-mcp-server/)

**Bidirectional MCP integration for Strands Agents.** Expose agents as MCP servers or connect to any MCP server.

```bash
pip install strands-mcp-server
```

---

## Overview

Two Python tools + CLI for Model Context Protocol (MCP):
- **mcp_server**: Expose your agent's tools as MCP server
- **mcp_client**: Connect to and use remote MCP servers  
- **CLI**: stdio server for Claude Desktop/Kiro

```mermaid
graph TD
    A[Your Strands Agent<br/>tools: calculator, shell, file_read] --> B[mcp_server tool]
    B --> C[MCP Protocol<br/>HTTP/stdio]
    C --> D[MCP Clients]
    D --> E[Claude Desktop]
    D --> F[Other Agents]
    D --> G[Custom Clients]
    
    style A fill:#2d3748,stroke:#4a5568,color:#fff
    style B fill:#2b6cb0,stroke:#2c5282,color:#fff
    style C fill:#38a169,stroke:#2f855a,color:#fff
    style D fill:#805ad5,stroke:#6b46c1,color:#fff
    style E fill:#d69e2e,stroke:#b7791f,color:#fff
    style F fill:#d69e2e,stroke:#b7791f,color:#fff
    style G fill:#d69e2e,stroke:#b7791f,color:#fff
```

---

## Quick Start

### 1. Expose Your Agent (Server)

```python
from strands import Agent
from strands_tools import calculator, shell
from strands_mcp_server import mcp_server

agent = Agent(tools=[calculator, shell, mcp_server])
agent("start mcp server on port 8000")
# Server running at http://localhost:8000/mcp
```

**Stateless mode (production):**
```python
agent.tool.mcp_server(action="start", stateless=True, agent=agent)
```

### 2. Connect to Servers (Client)

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# Connect
agent.tool.mcp_client(
    action="connect",
    connection_id="server1",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# Call remote tool
agent.tool.mcp_client(
    action="call_tool",
    connection_id="server1",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

### 3. Claude Desktop Integration

**Local mode** (expose `./tools/` directory):
```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/absolute/path/to/project"
      ]
    }
  }
}
```

**Proxy mode** (bridge to HTTP server):
```json
{
  "mcpServers": {
    "my-agent": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--upstream-url", "http://localhost:8000/mcp"
      ],
      "autoApprove": ["tool_name"]
    }
  }
}
```

---

## API Reference

### mcp_server

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | required | `start`, `stop`, `status`, `list` |
| `transport` | str | `http` | `http` (background) or `stdio` (foreground) |
| `port` | int | 8000 | HTTP port |
| `tools` | list[str] | None | Tools to expose (None = all) |
| `expose_agent` | bool | True | Enable `invoke_agent` tool |
| `stateless` | bool | False | Multi-node ready (no session state) |

**Examples:**
```python
# Basic
agent("start mcp server")

# Specific tools only
agent.tool.mcp_server(action="start", tools=["calculator"], agent=agent)

# Production
agent.tool.mcp_server(action="start", stateless=True, agent=agent)
```

### mcp_client

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | str | `connect`, `disconnect`, `list_tools`, `call_tool`, `list_connections` |
| `connection_id` | str | Connection identifier |
| `transport` | str | `http`, `stdio`, `sse` |
| `server_url` | str | URL (http/sse) |
| `tool_name` | str | Tool to call |
| `tool_args` | dict | Tool arguments |

**Transports:**
```python
# HTTP
agent.tool.mcp_client(
    action="connect", connection_id="s1",
    transport="http", server_url="http://localhost:8000/mcp"
)

# stdio (subprocess)
agent.tool.mcp_client(
    action="connect", connection_id="s2",
    transport="stdio", command="python", args=["server.py"]
)

# SSE
agent.tool.mcp_client(
    action="connect", connection_id="s3",
    transport="sse", server_url="http://localhost:8000/sse"
)
```

### invoke_agent Tool

When `expose_agent=True`, clients get full agent access with model switching:

```python
# Basic
invoke_agent(prompt="Calculate 2 + 2")

# Switch model provider
invoke_agent(
    prompt="Complex calculation",
    model_provider="anthropic",
    model_settings={"model_id": "claude-sonnet-4-20250514"}
)

# Custom system prompt
invoke_agent(
    prompt="Explain concept",
    system_prompt="You are a teacher."
)
```

**Parameters:**
- `prompt` (required): Query for agent
- `model_provider`: bedrock, anthropic, ollama, openai, github, env
- `model_settings`: `{"model_id": "...", "params": {...}}`
- `system_prompt`: Override agent's system prompt

---

## CLI

```bash
uvx strands-mcp-server [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--cwd PATH` | Working directory (local mode) |
| `--upstream-url URL` | Upstream server (proxy mode) |
| `--system-prompt TEXT` | Custom system prompt |
| `--no-agent-invocation` | Disable invoke_agent |
| `--debug` | Debug logging |

**Local mode:** Exposes `./tools/` directory with hot reload
**Proxy mode:** Bridges stdio ↔ HTTP server

**Examples:**
```bash
# Local mode
uvx strands-mcp-server --cwd /path/to/project

# Proxy mode
uvx strands-mcp-server --upstream-url http://localhost:8000/mcp

# With debug logging
uvx strands-mcp-server --cwd /path/to/project --debug
```

## Troubleshooting

**Tools not loading:**
```bash
uvx strands-mcp-server --cwd /absolute/path --debug
```

**Connection refused:**
```bash
curl http://localhost:8000/mcp
```

**Port in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Check Claude Desktop logs:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

---

## Testing

```bash
pytest              # All tests
pytest --cov        # With coverage
```

---

## Links

- **Docs**: https://cagataycali.github.io/strands-mcp-server/
- **Source**: https://github.com/cagataycali/strands-mcp-server
- **PyPI**: https://pypi.org/project/strands-mcp-server/
- **Strands**: https://strandsagents.com
- **MCP Spec**: https://modelcontextprotocol.io/

---

## License

Apache 2.0
