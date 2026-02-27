"""
Logging configuration for MCP server.

File-based logging only (no stdout pollution for streamable HTTP transport).
"""

import logging
import os
from pathlib import Path

# Determine log directory relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

MCP_LOG_FILE = LOG_DIR / "mcp_requests.log"

# Create dedicated MCP logger
mcp_logger = logging.getLogger("mcp_logger")
mcp_logger.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler only (no console output for SSE)
file_handler = logging.FileHandler(MCP_LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

# Prevent duplicate logs in root logger
if not mcp_logger.handlers:
    mcp_logger.addHandler(file_handler)

mcp_logger.propagate = False
