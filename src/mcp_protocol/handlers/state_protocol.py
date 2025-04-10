"""
State protocol handler for MCP.
This protocol handles system state information.
"""

import logging
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys
import os

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Import terminal handler to execute state commands
from .terminal_protocol import handler as terminal_handler

logger = logging.getLogger("mcp_protocol.state")


class StateProtocolHandler(ProtocolHandler):
    """Handler for state protocol commands."""

    def __init__(self):
        """Initialize the state protocol handler."""
        super().__init__("state")

        # Define the state commands
        self.state_commands = {
            "system": "uname -a",
            "uptime": "uptime",
            "kernel": "uname -r",
            "distro": "lsb_release -a 2>/dev/null || cat /etc/*release 2>/dev/null",
            "hardware": "lshw -short 2>/dev/null || echo 'lshw not installed'",
            "cpu": "cat /proc/cpuinfo | grep 'model name' | head -1",
            "memory": "cat /proc/meminfo | grep 'MemTotal\\|MemFree\\|MemAvailable'",
            "storage": "lsblk",
            "hostname": "hostname",
            "network": "hostname -I || ip addr | grep 'inet ' | grep -v '127.0.0.1'",
            "time": "date",
            "timezone": "timedatectl 2>/dev/null || cat /etc/timezone 2>/dev/null || date +%Z",
            "selinux": "getenforce 2>/dev/null || echo 'SELinux not available'",
            "runlevel": "runlevel 2>/dev/null || systemctl get-default 2>/dev/null || echo 'Runlevel information not available'",
            "desktop": "echo $XDG_CURRENT_DESKTOP $GDMSESSION $DESKTOP_SESSION 2>/dev/null || echo 'No desktop environment detected'",
            "shell": "echo $SHELL",
            "current-user": "whoami",
            "locale": "locale | grep LANG="
        }

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle state protocol commands (system state information).

        Args:
            command: The state command
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
            if command in self.state_commands:
                logger.debug(f"Processing state command: {command}")
                state_command = self.state_commands[command]

                # Execute the state command using terminal protocol
                terminal_result = terminal_handler.handle(
                    state_command, require_approval, auto_approve
                )

                # Add state type to result
                terminal_result["state_type"] = command
                return terminal_result

            elif command == "all":
                # Get all basic state information
                logger.debug("Processing full system state info command")

                # Build a combined command for basic info
                combined_command = (
                    "echo 'SYSTEM:' && uname -a && "
                    "echo -e '\nKERNEL:' && uname -r && "
                    "echo -e '\nHOSTNAME:' && hostname && "
                    "echo -e '\nUPTIME:' && uptime && "
                    "echo -e '\nCURRENT USER:' && whoami && "
                    "echo -e '\nMEMORY:' && free -h && "
                    "echo -e '\nDISK:' && df -h"
                )

                terminal_result = terminal_handler.handle(
                    combined_command, require_approval, auto_approve
                )

                terminal_result["state_type"] = "all"
                return terminal_result

            elif command.startswith("file:"):
                # Get state of a specific file - format: file:filepath
                logger.debug(f"Processing file state command: {command}")
                filepath = command[5:].strip()

                # Get file information
                file_command = f"ls -la {filepath} 2>/dev/null && file {filepath} 2>/dev/null && stat {filepath} 2>/dev/null"

                terminal_result = terminal_handler.handle(
                    file_command, require_approval, auto_approve
                )

                terminal_result["state_type"] = "file"
                return terminal_result

            elif command.startswith("process:"):
                # Get state of a specific process - format: process:name or pid
                logger.debug(f"Processing process state command: {command}")
                process = command[8:].strip()

                # Try to detect if it's a PID or name
                if process.isdigit():
                    # It's a PID
                    process_command = f"ps -p {process} -o pid,ppid,cmd,%cpu,%mem,state,start,time && lsof -p {process} 2>/dev/null | head -10"
                else:
                    # It's a process name
                    process_command = f"ps -C {process} -o pid,ppid,cmd,%cpu,%mem,state,start,time || pgrep -a {process}"

                terminal_result = terminal_handler.handle(
                    process_command, require_approval, auto_approve
                )

                terminal_result["state_type"] = "process"
                return terminal_result

            elif command.startswith("service:"):
                # Get state of a specific service - format: service:name
                logger.debug(f"Processing service state command: {command}")
                service_name = command[8:].strip()

                # Try different service managers
                service_command = (
                    f"systemctl status {service_name} 2>/dev/null || "
                    f"service {service_name} status 2>/dev/null || "
                    f"echo 'Service {service_name} not found or not supported by current service manager'"
                )

                terminal_result = terminal_handler.handle(
                    service_command, require_approval, auto_approve
                )

                terminal_result["state_type"] = "service"
                return terminal_result

            else:
                valid_commands = ", ".join(sorted(self.state_commands.keys()))
                special_commands = "all, file:filepath, process:name/pid, service:name"
                result["output"] = f"Unknown state command. Valid options: {valid_commands}, {special_commands}"
                logger.warning(f"Unknown state command: {command}")

        except Exception as e:
            logger.error(f"Error processing state command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = StateProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)