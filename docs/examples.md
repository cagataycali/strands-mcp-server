---
layout: default
title: Examples
nav_order: 5
---

# Examples

Practical code examples for common use cases.

---

## Basic Server

Expose your agent as an MCP server:

```python
from strands import Agent
from strands_tools import calculator, shell
from strands_mcp_server import mcp_server

# Create agent with tools
agent = Agent(
    name="demo-server",
    tools=[calculator, shell, mcp_server]
)

# Start HTTP server (background)
agent("start mcp server on port 8000")

# Server running at http://localhost:8000/mcp
print("✅ Server ready!")
```

---

## Basic Client

Connect to an MCP server:

```python
from strands import Agent
from strands_mcp_server import mcp_client

# Create client agent
agent = Agent(tools=[mcp_client])

# Connect
agent.tool.mcp_client(
    action="connect",
    connection_id="remote",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# List tools
agent.tool.mcp_client(
    action="list_tools",
    connection_id="remote"
)

# Call tool
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="calculator",
    tool_args={"expression": "42 * 89"}
)

print(result)
```

---

## Agent-to-Agent Communication

Multiple specialized agents sharing tools:

```python
from strands import Agent
from strands_tools import calculator, file_read, http_request
from strands_mcp_server import mcp_server, mcp_client

# Agent 1: Data specialist
data_agent = Agent(
    name="data-agent",
    tools=[calculator, file_read, mcp_server]
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

# Connect to specialists
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

# Use their tools
coordinator("""
1. Use web agent to fetch data from https://api.example.com
2. Use data agent to analyze the numbers
3. Summarize results
""")
```

---

## Tool Filtering

Expose only specific tools:

```python
from strands import Agent
from strands_tools import calculator, shell, file_read, file_write
from strands_mcp_server import mcp_server

agent = Agent(tools=[calculator, shell, file_read, file_write, mcp_server])

# Public server (safe tools only)
agent.tool.mcp_server(
    action="start",
    server_id="public",
    port=8000,
    tools=["calculator", "file_read"],  # Limited
    expose_agent=False,  # No full agent access
    agent=agent
)

# Admin server (all tools)
agent.tool.mcp_server(
    action="start",
    server_id="admin",
    port=8001,
    tools=None,  # All tools
    expose_agent=True,  # Full access
    agent=agent
)
```

---

## Stateless Production Server

Multi-node ready server:

```python
from strands import Agent
from strands_mcp_server import mcp_server

# Create agent
agent = Agent(
    name="production-agent",
    tools=[...],
    load_tools_from_directory=True  # Hot reload
)

# Start stateless server
agent.tool.mcp_server(
    action="start",
    port=8000,
    stateless=True,  # No session state
    agent=agent
)

# Keep running
import time
while True:
    time.sleep(60)
```

**Deploy multiple instances:**

```bash
# Instance 1
PORT=8001 python server.py

# Instance 2
PORT=8002 python server.py

# Instance 3
PORT=8003 python server.py
```

**Load balancer config (nginx):**

```nginx
upstream mcp_servers {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 8000;
    location /mcp {
        proxy_pass http://mcp_servers;
    }
}
```

---

## Full Agent Invocation

Use the `invoke_agent` tool for complex multi-tool queries:

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# Connect to remote agent
agent.tool.mcp_client(
    action="connect",
    connection_id="remote",
    transport="http",
    server_url="http://localhost:8000/mcp"
)

# Complex query requiring reasoning and multiple tools
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={
        "prompt": "Read data.csv, calculate the average of column B, and create a summary report"
    }
)

print(result)

# Conversational query
result = agent.tool.mcp_client(
    action="call_tool",
    connection_id="remote",
    tool_name="invoke_agent",
    tool_args={
        "prompt": "Explain the results of the last calculation in simple terms"
    }
)

print(result)
```

---

## Multiple Transports

Connect to servers via different transports:

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

# HTTP server
agent.tool.mcp_client(
    action="connect",
    connection_id="http-server",
    transport="http",
    server_url="http://remote.example.com:8000/mcp"
)

# stdio subprocess
agent.tool.mcp_client(
    action="connect",
    connection_id="local-server",
    transport="stdio",
    command="python",
    args=["local_server.py"]
)

# SSE server
agent.tool.mcp_client(
    action="connect",
    connection_id="sse-server",
    transport="sse",
    server_url="http://example.com:8000/sse"
)

# Use all servers
agent("""
1. List tools from all three servers
2. Compare their capabilities
3. Choose best server for each task
""")
```

---

## Health Checks & Monitoring

Monitor server health:

```python
from strands import Agent
from strands_mcp_server import mcp_server

agent = Agent(tools=[...], mcp_server)

# Start server
agent.tool.mcp_server(action="start", agent=agent)

# Check status
status = agent.tool.mcp_server(action="status", agent=agent)
print(status)

# List all servers
servers = agent.tool.mcp_server(action="list", agent=agent)
print(servers)

# Stop specific server
agent.tool.mcp_server(
    action="stop",
    server_id="default",
    agent=agent
)
```

---

## Error Handling

Robust error handling:

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])

try:
    # Connect
    result = agent.tool.mcp_client(
        action="connect",
        connection_id="remote",
        transport="http",
        server_url="http://localhost:8000/mcp"
    )
    
    if result["status"] == "error":
        print(f"Connection failed: {result['content'][0]['text']}")
        exit(1)
    
    # Call tool
    result = agent.tool.mcp_client(
        action="call_tool",
        connection_id="remote",
        tool_name="calculator",
        tool_args={"expression": "2 + 2"}
    )
    
    if result["status"] == "success":
        print(f"Result: {result['content'][0]['text']}")
    else:
        print(f"Tool call failed: {result['content'][0]['text']}")
        
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    # Clean disconnect
    agent.tool.mcp_client(
        action="disconnect",
        connection_id="remote"
    )
```

---

## Complete Workflow Example

Full-featured application:

```python
#!/usr/bin/env python3
"""Complete MCP workflow example"""

from strands import Agent
from strands_tools import calculator, file_read, http_request
from strands_mcp_server import mcp_server, mcp_client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Create specialist agents
def create_data_agent():
    agent = Agent(
        name="data-agent",
        tools=[calculator, file_read, mcp_server]
    )
    agent.tool.mcp_server(
        action="start",
        port=8001,
        stateless=True,
        agent=agent
    )
    logger.info("✅ Data agent running on port 8001")
    return agent

def create_web_agent():
    agent = Agent(
        name="web-agent",
        tools=[http_request, mcp_server]
    )
    agent.tool.mcp_server(
        action="start",
        port=8002,
        stateless=True,
        agent=agent
    )
    logger.info("✅ Web agent running on port 8002")
    return agent

# 2. Create coordinator
def create_coordinator():
    agent = Agent(
        name="coordinator",
        tools=[mcp_client]
    )
    
    # Connect to specialists
    for name, port in [("data", 8001), ("web", 8002)]:
        result = agent.tool.mcp_client(
            action="connect",
            connection_id=name,
            transport="http",
            server_url=f"http://localhost:{port}/mcp"
        )
        logger.info(f"✅ Connected to {name} agent")
    
    return agent

# 3. Run workflow
if __name__ == "__main__":
    # Start specialist agents
    data_agent = create_data_agent()
    web_agent = create_web_agent()
    
    # Create coordinator
    coordinator = create_coordinator()
    
    # Execute task
    task = """
    1. Use web agent to fetch https://api.example.com/data
    2. Use data agent to calculate statistics
    3. Summarize findings
    """
    
    result = coordinator(task)
    print(result)
    
    logger.info("✅ Workflow complete!")
```

---

## Next Steps

- [CLI Usage](cli.html) - Command-line interface
- [Claude Desktop](claude-desktop.html) - Integration guide
- [API Reference](api-reference.html) - Full documentation
