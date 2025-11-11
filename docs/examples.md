---
layout: default
title: Examples
nav_order: 5
---

# Examples

---

## Basic Server

```python
from strands import Agent
from strands_mcp_server import mcp_server

agent = Agent(tools=[mcp_server])
agent("start mcp server on port 8000")
```

---

## Basic Client

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

## Agent-to-Agent

```python
from strands import Agent
from strands_mcp_server import mcp_server, mcp_client

# Server agent
server = Agent(tools=[mcp_server])
server.tool.mcp_server(action="start", port=8001, agent=server)

# Client agent
client = Agent(tools=[mcp_client])
client.tool.mcp_client(
    action="connect",
    connection_id="server",
    transport="http",
    server_url="http://localhost:8001/mcp"
)

# Use remote tools
client("use server's calculator to compute 999 * 888")
```

---

## Tool Filtering

```python
agent.tool.mcp_server(
    action="start",
    tools=["calculator", "file_read"],  # Only these
    expose_agent=False,  # No invoke_agent
    agent=agent
)
```

---

## Stateless Production

```python
agent.tool.mcp_server(
    action="start",
    stateless=True,  # Multi-node ready
    agent=agent
)
```

---

## Full Agent Invocation

```python
agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={"prompt": "Read data.csv and calculate averages"}
)
```

---

## Multiple Transports

```python
# HTTP
agent.tool.mcp_client(
    action="connect",
    connection_id="http",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# stdio
agent.tool.mcp_client(
    action="connect",
    connection_id="local",
    transport="stdio",
    command="python",
    args=["server.py"]
)
```

---

## Error Handling

```python
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "2 + 2"}
)

if result["status"] == "success":
    print(result["content"][0]["text"])
else:
    print(f"Error: {result['content'][0]['text']}")
```
