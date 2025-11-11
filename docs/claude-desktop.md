---
layout: default
title: Claude Desktop
nav_order: 6
---

# Claude Desktop Integration

---

## Config File

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

---

## Local Mode

Expose `./tools/` directory:

```json
{
  "mcpServers": {
    "my-agent": {
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

## Proxy Mode

Bridge to HTTP server:

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

## Auto-Approve Tools

```json
{
  "mcpServers": {
    "my-agent": {
      "command": "uvx",
      "args": ["strands-mcp-server", "--cwd", "/path/to/project"],
      "autoApprove": ["calculator", "file_read"]
    }
  }
}
```

---

## Multiple Servers

```json
{
  "mcpServers": {
    "data-agent": {
      "command": "uvx",
      "args": ["strands-mcp-server", "--cwd", "/path/to/data-agent"]
    },
    "web-agent": {
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

## Troubleshooting

**Check logs:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Debug mode:**
```json
{
  "mcpServers": {
    "my-agent": {
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

**Test connection:**
```bash
uvx strands-mcp-server --cwd /path/to/project --debug
```

**Restart Claude Desktop** after config changes.
