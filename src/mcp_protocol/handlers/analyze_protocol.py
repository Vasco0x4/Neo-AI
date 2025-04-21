"""
Simplified analyze protocol handler for MCP.
This protocol handles comprehensive system analysis operations in one command.
"""

import logging
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys
import os

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Import terminal handler to execute analysis commands
from .terminal_protocol import handler as terminal_handler

logger = logging.getLogger("mcp_protocol.analyze")


class AnalyzeProtocolHandler(ProtocolHandler):
    """Handler for analyze protocol commands."""

    def __init__(self):
        """Initialize the analyze protocol handler."""
        super().__init__("analyze")

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle analyze protocol commands - always performs a full system analysis.

        Args:
            command: The analyze command (ignored)
            require_approval: Whether approval is required
            auto_approve: Whether to auto-approve

        Returns:
            Dictionary with execution results
        """
        result = {
            "command": "full system analysis",
            "executed": False,
            "output": ""
        }

        try:
            logger.debug("Processing full system analysis command")

            # Build a comprehensive system analysis command
            analysis_command = (
                "echo '===== SYSTEM OVERVIEW ====='\n"
                "echo '• System:' && uname -a\n"
                "echo '• Kernel:' && uname -r\n"
                "echo '• Hostname:' && hostname\n"
                "echo '• Current User:' && whoami\n"
                "echo '• Uptime:' && uptime\n"
                "echo\n"
                "echo '===== RESOURCES ====='\n"
                "echo '• Memory:' && free -h\n"
                "echo '• Disk:' && df -h\n"
                "echo '• CPU Load:' && top -bn1 | head -3\n"
                "echo '• Top CPU Processes:' && ps aux --sort=-%cpu | head -5\n"
                "echo '• Top Memory Processes:' && ps aux --sort=-%mem | head -5\n"
                "echo\n"
                "echo '===== NETWORK ====='\n"
                "echo '• Network Interfaces:' && ip -br addr 2>/dev/null || ifconfig\n"
                "echo '• Listening Ports:' && ss -tuln 2>/dev/null || netstat -tuln | head -10\n"
                "echo\n"
                "echo '===== SERVICES ====='\n"
                "echo '• Running Services:' && systemctl list-units --type=service --state=running 2>/dev/null | head -5 || service --status-all 2>/dev/null | grep ' + ' | head -5\n"
            )

            # Execute the analysis command using terminal protocol
            terminal_result = terminal_handler.handle(
                analysis_command, require_approval, auto_approve
            )

            terminal_result["analysis_type"] = "full"
            return terminal_result

        except Exception as e:
            logger.error(f"Error processing analyze command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = AnalyzeProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)