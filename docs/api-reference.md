---
layout: default
title: API Reference
nav_order: 3
---

# API Reference

---

## mcp_server

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | required | `start`, `stop`, `status`, `list` |
| `transport` | str | `http` | `http` or `stdio` |
| `port` | int | 8000 | Port for HTTP |
| `tools` | list | None | Tools to expose (None = all) |
| `expose_agent` | bool | True | Include `invoke_agent` |
| `stateless` | bool | False | Multi-node ready |

**Examples:**
```python
# Start
agent("start mcp server")
agent.tool.mcp_server(action="start", port=8000, agent=agent)

# Status
agent.tool.mcp_server(action="status", agent=agent)

# Stop
agent.tool.mcp_server(action="stop", agent=agent)
```

---

## mcp_client

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | str | `connect`, `disconnect`, `list_tools`, `call_tool` |
| `connection_id` | str | Connection identifier |
| `transport` | str | `http`, `stdio`, `sse` |
| `server_url` | str | URL for http/sse |
| `tool_name` | str | Tool to call |
| `tool_args` | dict | Tool arguments |

**Examples:**
```python
# Connect
agent.tool.mcp_client(
    action="connect",
    connection_id="remote",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# List tools
agent.tool.mcp_client(action="list_tools", connection_id="remote")

# Call tool
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "2 + 2"}
)

# Disconnect
agent.tool.mcp_client(action="disconnect", connection_id="remote")
```

---

## invoke_agent

Full conversational access to agent (when `expose_agent=True`):

```python
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={"prompt": "Calculate 2 + 2 and explain"}
)
```

**Parameters:**
- `prompt` (str): Natural language query
