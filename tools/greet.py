"""Example tool for testing strands-mcp-server CLI."""

from strands import tool


@tool
def greet(name: str, style: str = "friendly") -> str:
    """Greet someone with different styles.

    Args:
        name: The name of the person to greet
        style: Greeting style - "friendly", "formal", or "enthusiastic"

    Returns:
        str: A greeting message
    """
    styles = {
        "friendly": f"Hey {name}! Great to see you! 👋",
        "formal": f"Good day, {name}. It is a pleasure to meet you.",
        "enthusiastic": f"🎉 {name}!!! SO excited to see you! 🚀✨",
    }

    return styles.get(style, styles["friendly"])
