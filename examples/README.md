# Examples

This directory contains example scripts demonstrating how to use `strands-mcp-server`.

## 📁 Files

| File | Description |
|------|-------------|
| **mcp_server.py** | Start an MCP server exposing agent tools |
| **mcp_test.py** | Connect to MCP server using mcp_client tool |

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
cd examples
python mcp_server.py
```

**What it does:**
- Creates agent with calculator and shell tools
- Starts MCP server on port 8000
- Exposes tools via http://localhost:8000/mcp
- Provides interactive agent prompt

**Output:**
```
🚀 Starting MCP Server Demo
============================================================

📡 Starting MCP server on port 8000...

✅ MCP server 'demo-server' started on port 8000

📊 Mode: stateful (session persistence)
🔧 Exposed 3 tools:
  • calculator
  • shell
  • invoke_agent (full agent invocation) ✨

🔗 Connect at: http://localhost:8000/mcp
============================================================
✅ Server running! You can now:
  • Connect at: http://localhost:8000/mcp
  • Use with Claude Desktop (via npx mcp-remote)
  • Call tools remotely from other agents
============================================================

💬 Agent is also available interactively!
Try: 'show server status' or 'calculate 42 * 89'

# 
```

### 2. Test with MCP Client (New Terminal)

```bash
cd examples
python mcp_test.py
```

**What it does:**
- Connects to the MCP server
- Lists available tools
- Calls calculator tool remotely
- Invokes full agent conversation
- Demonstrates complete MCP workflow

**Output:**
```
🚀 MCP Client Test Demo
============================================================

🔧 Method 1: Using mcp_client tool
------------------------------------------------------------

📡 Connecting to MCP server at http://localhost:8000/mcp...
✅ Connected to MCP server: demo-server

📋 Listing available tools from server...
📊 Available tools from demo-server:
  • calculator - Calculator powered by SymPy
  • shell - Interactive shell with PTY support
  • invoke_agent - Full agent invocation ✨

🧮 Calling remote calculator tool...
Result: 887112

🤖 Invoking full agent remotely...
[Agent response with calculator usage]

👋 Disconnecting...
✅ Disconnected from MCP server: demo-server
```

## 🎓 Usage Patterns

### Pattern 1: Basic MCP Server

```python
from strands import Agent
from strands_tools import calculator, file_read
from strands_mcp_server import mcp_server

agent = Agent(tools=[calculator, file_read, mcp_server])
agent("start mcp server on port 8000")
```

### Pattern 2: MCP Client Connection

```python
from strands import Agent
from strands_mcp_server import mcp_client

agent = Agent(tools=[mcp_client])
agent("connect to http://localhost:8000/mcp as my-server")
agent("list tools from my-server")
agent("use calculator on my-server to compute 42 * 89")
```

### Pattern 3: Agent-to-Agent Communication

```python
# Server Agent
from strands import Agent
from strands_tools import calculator, shell
from strands_mcp_server import mcp_server

server_agent = Agent(tools=[calculator, shell, mcp_server])
server_agent("start mcp server")

# Client Agent (different process/machine)
from strands import Agent
from strands_mcp_server import mcp_client

client_agent = Agent(tools=[mcp_client])
client_agent("connect to http://server-host:8000/mcp as remote")
client_agent("invoke full agent on remote: analyze system logs")
```

## 🔌 Claude Desktop Integration

Update `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-strands-agent": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--allow-http"
      ]
    }
  }
}
```

Then restart Claude Desktop - your agent's tools will be available!

## 🛠️ Advanced Examples

### Expose Only Specific Tools

```python
agent.tool.mcp_server(
    action="start",
    port=8000,
    tools=["calculator", "file_read"],  # Only these tools
    expose_agent=False  # Disable full agent invocation
)
```

### Multiple Servers

```python
# Public server (limited tools)
agent.tool.mcp_server(
    action="start",
    server_id="public",
    port=8000,
    tools=["calculator", "current_time"]
)

# Admin server (all tools)
agent.tool.mcp_server(
    action="start",
    server_id="admin",
    port=8001
)
```

### Stateless Mode (Multi-Node)

```python
# For load-balanced deployments
agent.tool.mcp_server(
    action="start",
    port=8000,
    stateless=True  # No session state
)
```

## 📊 Monitoring

Check server status:

```python
agent.tool.mcp_server(action="status")
```

List all running servers:

```python
agent.tool.mcp_server(action="list")
```

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Server not responding:**
```bash
# Check if server is running
curl http://localhost:8000/mcp
```

**Import errors:**
```bash
# Reinstall package
pip install -e .
```
