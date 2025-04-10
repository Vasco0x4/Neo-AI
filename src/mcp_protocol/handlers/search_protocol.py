"""
Search protocol handler for MCP.
This protocol handles file and content searching.
"""

import logging
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys
import os
import shlex

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Import terminal handler to execute search commands
from .terminal_protocol import handler as terminal_handler

logger = logging.getLogger("mcp_protocol.search")

class SearchProtocolHandler(ProtocolHandler):
    """Handler for search protocol commands."""

    def __init__(self):
        """Initialize the search protocol handler."""
        super().__init__("search")

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle search protocol commands (search in files/system).

        Args:
            command: The search command
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
            # Parse search command
            parts = command.split(":", 1)
            if len(parts) == 2:
                search_type, search_params = parts
                logger.debug(f"Processing search command of type '{search_type}': {search_params}")

                grep_command = ""
                if search_type == "file":
                    # Format: file:pattern filepath
                    params = search_params.split(" ", 1)
                    if len(params) == 2:
                        pattern, filepath = params
                        pattern = shlex.quote(pattern)
                        filepath = shlex.quote(filepath)
                        grep_command = f"grep -n {pattern} {filepath}"
                        logger.debug(f"Generated grep command: {grep_command}")

                elif search_type == "recursive":
                    # Format: recursive:pattern directory
                    params = search_params.split(" ", 1)
                    if len(params) == 2:
                        pattern, directory = params
                        pattern = shlex.quote(pattern)
                        directory = shlex.quote(directory)
                        grep_command = f"grep -r -n {pattern} {directory}"
                        logger.debug(f"Generated recursive grep command: {grep_command}")

                elif search_type == "content":
                    # Format: content:filetype pattern directory
                    params = search_params.split(" ", 2)
                    if len(params) == 3:
                        filetype, pattern, directory = params
                        filetype = shlex.quote(filetype)
                        pattern = shlex.quote(pattern)
                        directory = shlex.quote(directory)
                        grep_command = f"find {directory} -name '*.{filetype}' -exec grep -l {pattern} {{}} \\;"
                        logger.debug(f"Generated content search command: {grep_command}")

                elif search_type == "name":
                    # Format: name:pattern directory
                    params = search_params.split(" ", 1)
                    if len(params) == 2:
                        pattern, directory = params
                        pattern = shlex.quote(pattern)
                        directory = shlex.quote(directory)
                        grep_command = f"find {directory} -name {pattern}"
                        logger.debug(f"Generated name search command: {grep_command}")

                # Execute the grep command using terminal protocol
                if grep_command:
                    terminal_result = terminal_handler.handle(
                        grep_command, require_approval, auto_approve
                    )
                    # Add search type to result
                    terminal_result["search_type"] = search_type
                    return terminal_result
                else:
                    result["output"] = "Invalid search format. Check documentation."
                    logger.warning(f"Invalid search format: {command}")
            else:
                result["output"] = "Invalid search format. Use type:parameters"
                logger.warning(f"Invalid search format: {command}")

        except Exception as e:
            logger.error(f"Error processing search command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = SearchProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)