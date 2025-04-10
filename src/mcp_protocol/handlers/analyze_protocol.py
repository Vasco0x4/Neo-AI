"""
Analyze protocol handler for MCP.
This protocol handles system analysis operations.
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

        # Define the analysis commands
        self.analyze_commands = {
            "disk": "df -h",
            "memory": "free -h",
            "cpu": "top -bn1 | head -15",
            "processes": "ps aux | sort -rk 3,3 | head -n 10",
            "users": "who",
            "network": "ifconfig || ip addr",
            "system": "uname -a && lsb_release -a 2>/dev/null || cat /etc/*release 2>/dev/null",
            "io": "iostat 2>/dev/null || echo 'iostat command not found'",
            "hardware": "lshw -short 2>/dev/null || echo 'lshw command not found'",
            "packages": "dpkg -l 2>/dev/null || rpm -qa 2>/dev/null || pacman -Q 2>/dev/null || echo 'Package manager not detected'",
            "services": "systemctl list-units --type=service --state=running 2>/dev/null || service --status-all 2>/dev/null || echo 'Service manager not detected'",
            "modules": "lsmod | head -20",
            "space": "du -sh /* 2>/dev/null | sort -hr",
            "temperature": "sensors 2>/dev/null || echo 'sensors command not found'",
            "logfiles": "ls -la /var/log/ | tail -20"
        }

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle analyze protocol commands (system analysis).

        Args:
            command: The analyze command
            require_approval: Whether approval is required
            auto_approve: Whether to auto-approve

        Returns:
            Dictionary with execution results
        """
        result = {
            "command": command,
            "executed": False,
            "output": ""
        }

        try:
            if command in self.analyze_commands:
                logger.debug(f"Processing analyze command: {command}")
                analysis_command = self.analyze_commands[command]

                # Execute the analysis command using terminal protocol
                terminal_result = terminal_handler.handle(
                    analysis_command, require_approval, auto_approve
                )

                # Add analysis type to result
                terminal_result["analysis_type"] = command
                return terminal_result

            elif command.startswith("custom:"):
                # Custom analysis - format: custom:command
                logger.debug(f"Processing custom analyze command: {command}")
                custom_command = command[7:].strip()

                # Execute the custom command using terminal protocol
                terminal_result = terminal_handler.handle(
                    custom_command, True, False  # Always require approval for custom commands
                )

                # Add analysis type to result
                terminal_result["analysis_type"] = "custom"
                return terminal_result

            else:
                valid_commands = ", ".join(sorted(self.analyze_commands.keys()))
                result["output"] = f"Unknown analysis command. Valid options: {valid_commands} or use custom:command"
                logger.warning(f"Unknown analysis command: {command}")

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