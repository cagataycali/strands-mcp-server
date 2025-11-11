---
layout: default
title: CLI Usage
nav_order: 4
---

# CLI Usage

---

## Command

```bash
uvx strands-mcp-server [OPTIONS]
```

---

## Options

| Option | Description |
|--------|-------------|
| `--cwd PATH` | Working directory (local mode) |
| `--upstream-url URL` | Upstream server (proxy mode) |
| `--system-prompt TEXT` | Custom system prompt |
| `--no-agent-invocation` | Disable invoke_agent |
| `--debug` | Debug logging |

---

## Local Mode

Expose `./tools/` directory:

```bash
uvx strands-mcp-server --cwd /path/to/project
```

**Claude Desktop:**
```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uvx",
      "args": ["strands-mcp-server", "--cwd", "/path/to/project"]
    }
  }
}
```

---

## Proxy Mode

Bridge stdio ↔ HTTP:

```bash
# Terminal 1: Start agent
python agent.py  # http://localhost:8000/mcp

# Terminal 2: Start proxy
uvx strands-mcp-server --upstream-url http://localhost:8000/mcp
```

**Claude Desktop:**
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

---

## Debug Mode

```bash
uvx strands-mcp-server --cwd /path/to/project --debug
```

Check logs:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```
