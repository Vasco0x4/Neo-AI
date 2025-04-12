"""
Machine Communication Protocol (MCP) for Neo AI.
This module initializes the MCP protocol framework.
"""

import logging
from .core import MCPProtocol
from .registry import ProtocolRegistry

# Import only the required protocol handlers
from .handlers import (
    terminal_protocol,
    files_protocol,
    analyze_protocol,
    network_protocol,
    security_protocol
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp_protocol")

# Create the global MCP protocol instance
mcp = MCPProtocol()


# Register all protocol handlers
def register_all_protocols():
    """Register all available protocol handlers."""
    protocols = [
        terminal_protocol,
        files_protocol,
        analyze_protocol,
        network_protocol,
        security_protocol
    ]

    for protocol in protocols:
        protocol.register()


# Initialize protocol registry
register_all_protocols()

# Export the MCP instance
__all__ = ['mcp']