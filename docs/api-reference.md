---
layout: default
title: API Reference
nav_order: 3
---

# API Reference

Complete documentation for `mcp_server` and `mcp_client` tools.

---

## mcp_server

Expose your Strands Agent as an MCP server.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | **required** | `start`, `stop`, `status`, or `list` |
| `server_id` | str | `"default"` | Unique identifier for this server |
| `transport` | str | `"http"` | `http` (background) or `stdio` (foreground) |
| `port` | int | `8000` | Port for HTTP server |
| `tools` | list[str] | `None` | Tool names to expose (None = all) |
| `expose_agent` | bool | `True` | Add `invoke_agent` tool |
| `stateless` | bool | `False` | No session state (multi-node ready) |
| `agent` | Agent | **required** | Parent agent (auto-injected) |

### Actions

#### start

Start an MCP server.

```python
# Natural language
agent("start mcp server on port 8000")

# Direct call - HTTP mode (background)
agent.tool.mcp_server(
    action="start",
    port=8000,
    agent=agent
)

# stdio mode (foreground - blocks)
agent.tool.mcp_server(
    action="start",
    transport="stdio",
    agent=agent
)
```

#### status

Get server status.

```python
agent.tool.mcp_server(action="status", agent=agent)
```

**Returns:**

```python
{
    "status": "success",
    "content": [{
        "text": "Server 'default' running on port 8000\n"
                "Transport: http (background)\n"
                "Mode: stateful\n"
                "Tools: 5 exposed\n"
                "  • calculator\n"
                "  • shell\n"
                "  • file_read\n"
                "  • mcp_server\n"
                "  • invoke_agent"
    }]
}
```

#### list

List all running servers.

```python
agent.tool.mcp_server(action="list", agent=agent)
```

#### stop

Stop a server.

```python
agent.tool.mcp_server(
    action="stop",
    server_id="default",
    agent=agent
)
```

### Transport Modes

#### HTTP (Background)

Runs in background thread, non-blocking.

```python
agent.tool.mcp_server(
    action="start",
    transport="http",  # Default
    port=8000,
    agent=agent
)
# Returns immediately, server runs in background
```

**Use for:**
- Production servers
- Multi-node deployments
- Interactive agent loops

#### stdio (Foreground)

Blocks current thread, processes stdin/stdout.

```python
agent.tool.mcp_server(
    action="start",
    transport="stdio",
    agent=agent
)
# Blocks until terminated
```

**Use for:**
- CLI entrypoints
- Claude Desktop integration
- Process isolation

### Tool Filtering

Expose only specific tools:

```python
agent.tool.mcp_server(
    action="start",
    tools=["calculator", "file_read"],  # Only these
    expose_agent=False,  # No invoke_agent
    agent=agent
)
```

### Stateless Mode

For production with load balancing:

```python
agent.tool.mcp_server(
    action="start",
    stateless=True,  # Fresh session per request
    agent=agent
)
```

**Benefits:**
- No sticky sessions needed
- Safe for load balancers
- Horizontal scaling

---

## mcp_client

Connect to and use remote MCP servers.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | str | `connect`, `disconnect`, `list_tools`, `call_tool`, `list_connections` |
| `connection_id` | str | Identifier for this connection |
| `transport` | str | `http`, `stdio`, or `sse` |
| `server_url` | str | URL for http/sse transport |
| `command` | str | Command for stdio transport |
| `args` | list[str] | Arguments for stdio command |
| `tool_name` | str | Tool to call (for `call_tool` action) |
| `tool_args` | dict | Tool arguments (for `call_tool` action) |

### Actions

#### connect

Establish connection to MCP server.

**HTTP:**

```python
agent.tool.mcp_client(
    action="connect",
    connection_id="remote",
    transport="http",
    server_url="http://localhost:8000/mcp"
)
```

**stdio (subprocess):**

```python
agent.tool.mcp_client(
    action="connect",
    connection_id="local",
    transport="stdio",
    command="python",
    args=["server.py"]
)
```

**SSE:**

```python
agent.tool.mcp_client(
    action="connect",
    connection_id="sse-server",
    transport="sse",
    server_url="http://localhost:8000/sse"
)
```

#### list_tools

List tools from connected server.

```python
result = agent.tool.mcp_client(
    action="list_tools",
    connection_id="remote"
)
```

**Returns:**

```python
{
    "status": "success",
    "content": [{
        "text": "Available tools from remote:\n"
                "  • calculator - Math operations\n"
                "  • shell - Execute commands\n"
                "  • invoke_agent - Full agent access"
    }]
}
```

#### call_tool

Call a remote tool.

```python
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)
```

**Returns:**

```python
{
    "status": "success",
    "content": [{
        "text": "Result: 3738"
    }]
}
```

#### list_connections

Show all active connections.

```python
agent.tool.mcp_client(action="list_connections")
```

#### disconnect

Close connection.

```python
agent.tool.mcp_client(
    action="disconnect",
    connection_id="remote"
)
```

---

## invoke_agent Tool

When `expose_agent=True` (default), servers expose an `invoke_agent` tool for full conversational access.

### Basic Usage

```python
# Via mcp_client
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={"prompt": "Calculate 2 + 2"}
)
```

### Model Provider Switching

Switch to different model providers:

```python
# Anthropic
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={
        "prompt": "Complex analysis",
        "model_provider": "anthropic",
        "model_settings": {
            "model_id": "claude-sonnet-4-20250514",
            "params": {"temperature": 0.3}
        }
    }
)

# Ollama (local)
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={
        "prompt": "Quick calculation",
        "model_provider": "ollama",
        "model_settings": {
            "model_id": "qwen3:4b",
            "host": "http://localhost:11434"
        }
    }
)
```

### System Prompt Override

```python
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={
        "prompt": "Explain quantum computing",
        "system_prompt": "You are a physics teacher. Explain concepts simply."
    }
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | str | ✅ | Query for agent |
| `model_provider` | str | ❌ | Model provider: bedrock, anthropic, ollama, openai, github, env |
| `model_settings` | dict | ❌ | Model config: `{"model_id": "...", "params": {...}}` |
| `system_prompt` | str | ❌ | Override agent's system prompt |

### Supported Providers

- **bedrock** - Amazon Bedrock
- **anthropic** - Anthropic API
- **ollama** - Local Ollama
- **openai** - OpenAI API
- **github** - GitHub Models
- **env** - Use environment variables

---

## Error Handling

All tools return a consistent format:

**Success:**

```python
{
    "status": "success",
    "content": [{"text": "Operation result"}]
}
```

**Error:**

```python
{
    "status": "error",
    "content": [{"text": "Error description"}]
}
```

---

## Next Steps

- [CLI Usage](cli.html) - Command-line interface
- [Examples](examples.html) - Code samples
- [Claude Desktop](claude-desktop.html) - Integration guide
