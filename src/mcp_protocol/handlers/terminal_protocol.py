"""
Terminal protocol handler for MCP.
This protocol handles shell command execution.
"""

import logging
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys
import os

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Now we can import from src
from src.command_executor import execute_command_in_terminal, wait_for_command_completion
from src.approval_handler import ApprovalHandler

logger = logging.getLogger("mcp_protocol.terminal")


class TerminalProtocolHandler(ProtocolHandler):
    """Handler for terminal protocol commands."""

    def __init__(self):
        """Initialize the terminal protocol handler."""
        super().__init__("terminal")

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle terminal protocol commands (shell command execution).

        Args:
            command: The shell command to execute
            require_approval: Whether approval is required
            auto_approve: Whether to auto-approve

        Returns:
            Dictionary with execution results
        """
        result = {
            "command": command,
            "executed": False,
            "output": "",
            "approved": False
        }

        try:
            logger.debug(f"Executing terminal command: {command}")

            # Request approval if required
            approval_handler = ApprovalHandler(require_approval, auto_approve)
            approved, option = approval_handler.request_approval(command)

            result["approved"] = approved

            if not approved:
                result["output"] = "Command execution was denied."
                return result

            # Execute the approved command
            temp_file = execute_command_in_terminal(command)
            if temp_file:
                command_output = wait_for_command_completion(temp_file)
                result["output"] = command_output
                result["executed"] = True
                logger.debug("Command executed successfully")
            else:
                result["output"] = "Failed to execute command."
                logger.error("Failed to execute command")

        except Exception as e:
            logger.error(f"Error executing terminal command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = TerminalProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)