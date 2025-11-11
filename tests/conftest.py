"""Pytest configuration and fixtures for strands-mcp-server tests."""

import os
import socket
import time
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def bypass_tool_consent():
    """Bypass tool consent for all tests."""
    with patch.dict(os.environ, {"BYPASS_TOOL_CONSENT": "true"}):
        yield


def get_free_port() -> int:
    """Get a free port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture
def test_port():
    """Provide a unique test port for each test."""
    return get_free_port()


@pytest.fixture
def server_startup_delay():
    """Standard delay for server startup."""
    return 2.0


def wait_for_server(port: int, timeout: int = 5) -> bool:
    """Wait for server to be ready.

    Args:
        port: Port to check
        timeout: Maximum wait time in seconds

    Returns:
        True if server is ready, False otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def wait_for_port_free(port: int, timeout: int = 5) -> bool:
    """Wait for port to become free.

    Args:
        port: Port to check
        timeout: Maximum wait time in seconds

    Returns:
        True if port is free, False otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result != 0:  # Port is free
                return True
        except Exception:
            return True  # Error connecting means port is likely free
        time.sleep(0.1)
    return False
