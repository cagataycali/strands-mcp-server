---
layout: default
title: CLI Usage
nav_order: 4
---

# CLI Usage

The `strands-mcp-server` command provides a stdio MCP server for integration with Claude Desktop, Kiro, and other stdio-based MCP clients.

---

## Installation

```bash
pipx install strands-mcp-server
```

---

## Usage

```bash
uvx strands-mcp-server [OPTIONS]
```

---

## Options

| Option | Type | Description |
|--------|------|-------------|
| `--cwd PATH` | str | Working directory (local mode) |
| `--upstream-url URL` | str | Upstream server URL (proxy mode) |
| `--system-prompt TEXT` | str | Custom system prompt |
| `--no-agent-invocation` | flag | Disable `invoke_agent` tool |
| `--debug` | flag | Enable debug logging |

---

## Operating Modes

### Local Mode

Exposes tools from `./tools/` directory with hot reload.

**How it works:**
1. CLI creates agent with `load_tools_from_directory=True`
2. Strands loads all `@tool` decorated functions from `./tools/`
3. Starts MCP server in stdio mode
4. Client communicates via stdin/stdout

**Example:**

```bash
uvx strands-mcp-server --cwd /path/to/project
```

**Project structure:**

```
my-project/
├── tools/
│   ├── weather.py     # @tool function
│   ├── database.py    # @tool function
│   └── search.py      # @tool function
└── README.md
```

**Tools are automatically loaded and exposed!**

### Proxy Mode

Bridges stdio (client) to HTTP (upstream server).

**How it works:**
1. CLI connects to upstream HTTP server as MCP client
2. Creates stdio MCP server for client
3. Forwards all requests to upstream
4. Returns responses via stdio

**Example:**

```bash
# Terminal 1: Start your agent with HTTP server
python my_agent.py  # Runs on port 8000

# Terminal 2: Start proxy
uvx strands-mcp-server --upstream-url http://localhost:8000/mcp
```

**Why use this:**
- Claude Desktop only speaks stdio
- Your agent runs HTTP server
- Proxy bridges the protocols

---

## Examples

### Basic Local Mode

```bash
uvx strands-mcp-server --cwd /path/to/project
```

### With Debug Logging

```bash
uvx strands-mcp-server --cwd /path/to/project --debug
```

**Debug output shows:**
- Working directory
- Tools discovered
- MCP protocol messages
- Tool execution logs

### Proxy to Remote Server

```bash
uvx strands-mcp-server --upstream-url http://localhost:8000/mcp
```

### Custom System Prompt

```bash
uvx strands-mcp-server \
  --cwd /path/to/project \
  --system-prompt "You are a specialized data analysis assistant."
```

### Disable Agent Invocation

```bash
uvx strands-mcp-server \
  --cwd /path/to/project \
  --no-agent-invocation
```

**Why disable:**
- Security: Limit to individual tools only
- Performance: Avoid full agent conversations
- Simplicity: Expose tools, not agent reasoning

---

## Tool Loading

### Automatic Discovery

CLI automatically loads tools from `./tools/` directory.

**Example tool file:**

`./tools/weather.py`:

```python
from strands import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: City name
        
    Returns:
        Weather description
    """
    # Implementation
    return f"Weather in {city}: Sunny, 72°F"
```

**Exposed as:**
- Tool name: `get_weather`
- Description: From docstring
- Parameters: From type hints

### Hot Reload

Strands automatically reloads tools when files change:

1. Edit tool file
2. Save changes
3. Tool updated immediately (no restart)

---

## Claude Desktop Integration

### Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

**Local mode:**

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

**Proxy mode:**

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

**With auto-approve:**

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": [
        "strands-mcp-server",
        "--cwd", "/absolute/path/to/project"
      ],
      "autoApprove": ["calculator", "file_read"]
    }
  }
}
```

### Testing Connection

1. **Save config**
2. **Restart Claude Desktop**
3. **Check logs:**

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Successful connection shows:**
```
Connected to MCP server: my-tools
Available tools: calculator, file_read, search
```

---

## Kiro Integration

Similar configuration in `~/.kiro/settings/mcp.json`:

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

---

## Troubleshooting

### Tools not loading

**Check working directory:**

```bash
uvx strands-mcp-server --cwd /absolute/path --debug
```

**Debug output shows:**
```
Working directory: /absolute/path
Tools directory: /absolute/path/tools
Found 3 .py files: ['weather.py', 'database.py', 'search.py']
Loaded 3 tools: ['get_weather', 'query_database', 'web_search']
```

**Common issues:**
- Relative path (use absolute)
- Missing `./tools/` directory
- No `@tool` decorated functions
- Python syntax errors in tool files

### Connection refused

**Verify server running (proxy mode):**

```bash
curl http://localhost:8000/mcp
```

Should return HTTP response (not necessarily 200).

### Claude Desktop not connecting

**Check logs:**

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Common issues:**
- Wrong path in config
- Server not running (proxy mode)
- Port already in use
- Permission errors

**Fix permissions:**

```bash
chmod +x $(which strands-mcp-server)
```

### Debug mode

Enable debug logging:

```bash
uvx strands-mcp-server --cwd /path/to/project --debug 2>&1 | tee debug.log
```

**Debug shows:**
- Tool discovery process
- MCP protocol messages
- Tool execution traces
- Error stack traces

---

## Environment Variables

CLI respects standard Strands environment variables:

| Variable | Description |
|----------|-------------|
| `STRANDS_PROVIDER` | Default model provider |
| `STRANDS_MODEL_ID` | Default model ID |
| `STRANDS_MAX_TOKENS` | Max tokens to generate |
| `STRANDS_TEMPERATURE` | Sampling temperature |

**Example:**

```bash
export STRANDS_PROVIDER=anthropic
export STRANDS_MODEL_ID=claude-sonnet-4-20250514

uvx strands-mcp-server --cwd /path/to/project
```

---

## Next Steps

- [Examples](examples.html) - Code samples
- [Claude Desktop](claude-desktop.html) - Detailed integration guide
- [API Reference](api-reference.html) - Tool documentation
