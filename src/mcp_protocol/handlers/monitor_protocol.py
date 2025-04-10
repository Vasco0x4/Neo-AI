"""
Monitor protocol handler for MCP.
This protocol handles system monitoring operations.
"""

import logging
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys
import os

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Import terminal handler to execute monitor commands
from .terminal_protocol import handler as terminal_handler

logger = logging.getLogger("mcp_protocol.monitor")


class MonitorProtocolHandler(ProtocolHandler):
    """Handler for monitor protocol commands."""

    def __init__(self):
        """Initialize the monitor protocol handler."""
        super().__init__("monitor")

        # Define the monitor commands
        self.monitor_commands = {
            "cpu": "top -bn1 | head -15",
            "memory": "free -h",
            "disk": "df -h",
            "load": "uptime",
            "io": "iostat 2>/dev/null || echo 'iostat not installed'",
            "processes": "ps aux --sort=-%cpu | head -n 10",
            "network": "ifconfig || ip addr",
            "temperature": "sensors 2>/dev/null || echo 'sensors not installed'",
            "users": "w",
            "swap": "swapon -s || echo 'No swap information available'",
            "space": "du -sh /* 2>/dev/null | sort -hr | head -10",
            "inodes": "df -i",
            "services": "systemctl list-units --state=running --type=service 2>/dev/null || service --status-all 2>/dev/null | grep ' + '",
            "memory-hogs": "ps aux --sort=-%mem | head -10",
            "cpu-hogs": "ps aux --sort=-%cpu | head -10",
            "open-files": "lsof | wc -l",
            "connections": "netstat -ant | wc -l || ss -ant | wc -l"
        }

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle monitor protocol commands (system monitoring).

        Args:
            command: The monitor command
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
            if command in self.monitor_commands:
                logger.debug(f"Processing monitor command: {command}")
                monitor_command = self.monitor_commands[command]

                # Execute the monitor command using terminal protocol
                terminal_result = terminal_handler.handle(
                    monitor_command, require_approval, auto_approve
                )

                # Add monitoring type to result
                terminal_result["monitoring_type"] = command
                return terminal_result

            elif command.startswith("log:"):
                # Monitor specific log file - format: log:logfile[:lines]
                logger.debug(f"Processing log monitor command: {command}")
                params = command[4:].strip().split(":", 1)
                logfile = params[0]
                lines = "20"  # Default number of lines

                if len(params) > 1:
                    lines = params[1]

                # Check if the file exists and is a log file
                if not os.path.exists(logfile):
                    result["output"] = f"Log file not found: {logfile}"
                    logger.warning(f"Log file not found: {logfile}")
                    return result

                # Execute tail command on the log file
                tail_command = f"tail -n {lines} {logfile}"

                terminal_result = terminal_handler.handle(
                    tail_command, require_approval, auto_approve
                )

                terminal_result["monitoring_type"] = "log"
                return terminal_result

            elif command.startswith("custom:"):
                # Custom monitoring - format: custom:command
                logger.debug(f"Processing custom monitor command: {command}")
                custom_command = command[7:].strip()

                # Execute the custom command using terminal protocol
                terminal_result = terminal_handler.handle(
                    custom_command, True, False  # Always require approval for custom commands
                )

                # Add monitoring type to result
                terminal_result["monitoring_type"] = "custom"
                return terminal_result

            else:
                valid_commands = ", ".join(sorted(self.monitor_commands.keys()))
                special_commands = "log:logfile[:lines], custom:command"
                result["output"] = f"Unknown monitor command. Valid options: {valid_commands}, {special_commands}"
                logger.warning(f"Unknown monitor command: {command}")

        except Exception as e:
            logger.error(f"Error processing monitor command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = MonitorProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)