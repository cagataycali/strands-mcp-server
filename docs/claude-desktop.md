---
layout: default
title: Claude Desktop
nav_order: 6
---

# Claude Desktop Integration

Complete guide to integrating your Strands Agent with Claude Desktop.

---

## Overview

Claude Desktop supports MCP servers via stdio protocol. The `strands-mcp-server` CLI provides two integration modes:

1. **Local mode** - Expose tools from `./tools/` directory
2. **Proxy mode** - Bridge to HTTP MCP server

---

## Prerequisites

- Claude Desktop installed
- Python 3.10+ with strands-mcp-server

```bash
pip install strands-mcp-server
```

---

## Method 1: Local Mode (Recommended)

Expose tools directly from your project directory.

### Step 1: Create Tools

Create `./tools/` directory with tool files:

**Project structure:**

```
my-project/
├── tools/
│   ├── calculator.py
│   ├── weather.py
│   └── database.py
└── README.md
```

**Example tool** (`tools/weather.py`):

```python
from strands import tool
import requests

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: City name
        
    Returns:
        Weather description
    """
    # Implementation
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()["description"]
```

### Step 2: Configure Claude Desktop

Edit config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Linux:** `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/absolute/path/to/my-project"
      ]
    }
  }
}
```

⚠️ **Use absolute paths!**

### Step 3: Restart Claude Desktop

1. Quit Claude Desktop completely (Cmd+Q on macOS)
2. Reopen Claude Desktop
3. Your tools should be available!

### Step 4: Verify Connection

Check logs:

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Successful connection:**

```
[INFO] Connected to MCP server: my-tools
[INFO] Available tools: get_weather, query_database, calculate
```

### Step 5: Use Tools in Claude

In Claude Desktop:

> "What's the weather in San Francisco?"

Claude will use your `get_weather` tool automatically!

---

## Method 2: Proxy Mode

Bridge Claude Desktop to your HTTP MCP server.

### Step 1: Start Your Agent

**server.py:**

```python
from strands import Agent
from strands_tools import calculator, shell, file_read
from strands_mcp_server import mcp_server

agent = Agent(
    name="my-agent",
    tools=[calculator, shell, file_read, mcp_server]
)

# Start HTTP server
agent.tool.mcp_server(
    action="start",
    port=8000,
    agent=agent
)

# Keep running
import time
while True:
    time.sleep(60)
```

**Run:**

```bash
python server.py
```

Server running at `http://localhost:8000/mcp`

### Step 2: Configure Claude Desktop

```json
{
  "mcpServers": {
    "my-agent": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--upstream-url", "http://localhost:8000/mcp"
      ]
    }
  }
}
```

### Step 3: Restart Claude Desktop

Your agent's tools are now available in Claude!

---

## Advanced Configuration

### Auto-Approve Tools

Skip confirmation for trusted tools:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/path/to/project"
      ],
      "autoApprove": [
        "calculator",
        "get_weather",
        "current_time"
      ]
    }
  }
}
```

### Custom System Prompt

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/path/to/project",
        "--system-prompt", "You are a specialized data analysis assistant."
      ]
    }
  }
}
```

### Disable Agent Invocation

Security: Only expose individual tools:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/path/to/project",
        "--no-agent-invocation"
      ]
    }
  }
}
```

### Debug Mode

Enable debug logging:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/path/to/project",
        "--debug"
      ]
    }
  }
}
```

---

## Multiple Servers

Run multiple MCP servers simultaneously:

```json
{
  "mcpServers": {
    "development-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/path/to/dev-tools"
      ]
    },
    "production-agent": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--upstream-url", "http://prod-server:8000/mcp"
      ]
    },
    "local-utilities": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/path/to/utilities"
      ],
      "autoApprove": ["calculator", "current_time"]
    }
  }
}
```

Claude Desktop will have access to all tools from all servers!

---

## Troubleshooting

### Tools Not Appearing

**Check logs:**

```bash
tail -f ~/Library/Logs/Claude/mcp-server-my-tools.log
```

**Common issues:**

1. **Wrong path in config**
   - Use absolute paths
   - Verify directory exists
   
2. **No tools/ directory**
   - Create `./tools/` in project root
   - Add at least one tool file

3. **Syntax errors in tools**
   - Check tool file for Python errors
   - Verify `@tool` decorator usage

**Fix:**

```bash
# Verify path
ls -la /absolute/path/to/project/tools

# Test CLI directly
uvx strands-mcp-server --cwd /path/to/project --debug
```

### Connection Errors

**Error: "Failed to connect to MCP server"**

**For proxy mode:**

1. Verify server is running:

```bash
curl http://localhost:8000/mcp
```

2. Check server logs
3. Verify port is correct in config

**For local mode:**

1. Check file permissions
2. Verify Python environment
3. Test CLI manually

### Permission Denied

**macOS/Linux:**

```bash
chmod +x $(which strands-mcp-server)
```

### Server Keeps Restarting

Check logs for errors:

```bash
tail -100 ~/Library/Logs/Claude/mcp*.log
```

Common causes:
- Missing dependencies
- Python version mismatch
- Import errors in tools
- Port conflicts (proxy mode)

### Tools Not Hot Reloading

Strands hot reload requires:
- Tools in `./tools/` directory
- `@tool` decorator used
- Valid Python syntax

**Test reload:**

1. Modify tool file
2. Save changes
3. Wait 2-3 seconds
4. Test in Claude Desktop

---

## Best Practices

### 1. Use Absolute Paths

❌ **Bad:**

```json
{
  "command": "uvx",
  "args": ["strands-mcp-server", "--cwd", "./my-project"]
}
```

✅ **Good:**

```json
{
  "command": "uvx",
  "args": ["strands-mcp-server", "--cwd", "/Users/you/my-project"]
}
```

### 2. Auto-Approve Safe Tools Only

✅ **Safe tools:**
- calculator
- current_time
- get_weather (read-only APIs)

❌ **Never auto-approve:**
- shell
- file_write
- http_request (write operations)

### 3. Use Descriptive Names

```json
{
  "mcpServers": {
    "data-analysis-tools": {...},  // ✅ Clear purpose
    "web-scrapers": {...},         // ✅ Clear purpose
    "my-tools": {...}              // ❌ Too generic
  }
}
```

### 4. Test Locally First

Before adding to Claude Desktop:

```bash
# Test CLI directly
uvx strands-mcp-server --cwd /path/to/project --debug

# Verify tools load
# Check for errors
# Confirm expected behavior
```

### 5. Monitor Logs

Keep logs open during development:

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

---

## Example Configurations

### Development Environment

```json
{
  "mcpServers": {
    "dev-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/Users/you/dev-tools",
        "--debug"
      ],
      "autoApprove": ["calculator", "current_time"]
    }
  }
}
```

### Production Agent

```json
{
  "mcpServers": {
    "production-agent": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--upstream-url", "https://agent.company.com/mcp"
      ]
    }
  }
}
```

### Mixed Setup

```json
{
  "mcpServers": {
    "local-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/Users/you/tools"
      ],
      "autoApprove": ["calculator"]
    },
    "remote-agent": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--upstream-url", "http://localhost:8000/mcp"
      ]
    }
  }
}
```

---

## Next Steps

- [Examples](examples.html) - More integration patterns
- [CLI Usage](cli.html) - Full CLI reference
- [API Reference](api-reference.html) - Tool documentation
