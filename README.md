# strands-mcp-server

[![PyPI](https://img.shields.io/pypi/v/strands-mcp-server.svg)](https://pypi.org/project/strands-mcp-server/)

Bidirectional MCP integration for Strands Agents.

```bash
pip install strands-mcp-server
```

---

## Overview

- **mcp_server** - Expose agent as MCP server
- **mcp_client** - Connect to MCP servers
- **CLI** - stdio for Claude Desktop

```mermaid
graph LR
    subgraph "Your Strands Agent"
        A[Tools: calculator, shell, etc.]
        B[mcp_server tool]
        C[mcp_client tool]
        A --> B
        C --> A
    end
    
    subgraph "Server Mode"
        B -->|HTTP/stdio| D[MCP Protocol]
        D --> E[Claude Desktop]
        D --> F[Other Agents]
        D --> G[Custom Clients]
    end
    
    subgraph "Client Mode"
        H[Remote MCP Servers] -->|HTTP/stdio/SSE| I[MCP Protocol]
        I --> C
    end
    
    subgraph "CLI"
        J[uvx strands-mcp-server] -->|Local Mode| D
        J -->|Proxy Mode| I
    end
    
    style A fill:#2d3748,stroke:#4a5568,color:#fff
    style B fill:#2b6cb0,stroke:#2c5282,color:#fff
    style C fill:#38a169,stroke:#2f855a,color:#fff
    style D fill:#805ad5,stroke:#6b46c1,color:#fff
    style I fill:#805ad5,stroke:#6b46c1,color:#fff
    style E fill:#d69e2e,stroke:#b7791f,color:#fff
    style F fill:#d69e2e,stroke:#b7791f,color:#fff
    style G fill:#d69e2e,stroke:#b7791f,color:#fff
    style H fill:#e53e3e,stroke:#c53030,color:#fff
    style J fill:#48bb78,stroke:#38a169,color:#fff
```

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
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

**For Agents like Claude Desktop/Kiro/...:**
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

## API

### mcp_server

| Parameter | Default | Description |
|-----------|---------|-------------|
| `action` | required | `start`, `stop`, `status`, `list` |
| `transport` | `http` | `http` or `stdio` |
| `port` | 8000 | Port |
| `tools` | None | Tools to expose (None = all) |
| `expose_agent` | True | Include `invoke_agent` |
| `stateless` | False | Multi-node ready |

### mcp_client

| Parameter | Description |
|-----------|-------------|
| `action` | `connect`, `disconnect`, `list_tools`, `call_tool` |
| `connection_id` | Connection ID |
| `transport` | `http`, `stdio`, `sse` |
| `server_url` | Server URL |
| `tool_name` | Tool to call |
| `tool_args` | Tool arguments |

### invoke_agent

Full agent access when `expose_agent=True`:

```python
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={"prompt": "Calculate 2 + 2"}
)
```

---

## CLI

```bash
uvx strands-mcp-server [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--cwd PATH` | Working directory |
| `--upstream-url URL` | Upstream server (proxy) |
| `--system-prompt TEXT` | System prompt |
| `--no-agent-invocation` | Disable invoke_agent |
| `--debug` | Debug mode |

**Examples:**
```bash
# Local
uvx strands-mcp-server --cwd /path/to/project

# Proxy
uvx strands-mcp-server --upstream-url http://localhost:8000/mcp
```

---

## Troubleshooting

```bash
# Debug
uvx strands-mcp-server --cwd /path --debug

# Check connection
curl http://localhost:8000/mcp

# Port in use
lsof -i :8000 && kill -9 <PID>

# Claude logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

---

## Links

- [Docs](https://cagataycali.github.io/strands-mcp-server/)
- [GitHub](https://github.com/cagataycali/strands-mcp-server)
- [PyPI](https://pypi.org/project/strands-mcp-server/)
- [Strands](https://strandsagents.com)
- [MCP](https://modelcontextprotocol.io/)

---

**License:** Apache 2.0
