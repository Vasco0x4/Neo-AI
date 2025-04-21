"""
Files protocol handler for MCP.
This protocol handles file operations.
"""

import os
import logging
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Now we can import from src
from src.approval_handler import ApprovalHandler

logger = logging.getLogger("mcp_protocol.files")

class FilesProtocolHandler(ProtocolHandler):
    """Handler for files protocol commands."""

    def __init__(self):
        """Initialize the files protocol handler."""
        super().__init__("files")

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle files protocol commands (read/write files).

        Args:
            command: The file operation command
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
            # Read operation
            if command.startswith("read:"):
                logger.debug(f"Processing file read command: {command}")
                filepath = command[5:].strip()

                # Request approval for file reading
                if require_approval and not auto_approve:
                    approval_handler = ApprovalHandler(require_approval, auto_approve)
                    approved, _ = approval_handler.request_approval(f"Read file: {filepath}")

                    if not approved:
                        result["output"] = "File reading was denied."
                        logger.info(f"Reading file '{filepath}' was denied by user")
                        return result

                # Read the file
                if os.path.exists(filepath) and os.path.isfile(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        result["output"] = content
                        result["executed"] = True
                        logger.debug(f"Successfully read file '{filepath}'")
                    except Exception as read_error:
                        result["output"] = f"Error reading file: {str(read_error)}"
                        logger.error(f"Error reading file '{filepath}': {str(read_error)}")
                else:
                    result["output"] = f"File not found: {filepath}"
                    logger.warning(f"File not found: '{filepath}'")

            # Write operation (requires more careful handling)
            elif command.startswith("write:"):
                logger.debug(f"Processing file write command: {command}")
                parts = command[6:].strip().split(" ", 1)
                if len(parts) == 2:
                    filepath, content = parts

                    # Request approval for file writing (always required)
                    approval_handler = ApprovalHandler(True, False)  # Always require approval for writing
                    preview_content = content[:50] + ("..." if len(content) > 50 else "")
                    approved, _ = approval_handler.request_approval(
                        f"Write to file: {filepath}\nContent: {preview_content}"
                    )

                    if not approved:
                        result["output"] = "File writing was denied."
                        logger.info(f"Writing to file '{filepath}' was denied by user")
                        return result

                    # Create directory if it doesn't exist
                    directory = os.path.dirname(filepath)
                    if directory and not os.path.exists(directory):
                        try:
                            os.makedirs(directory)
                            logger.debug(f"Created directory '{directory}'")
                        except Exception as dir_error:
                            result["output"] = f"Error creating directory: {str(dir_error)}"
                            logger.error(f"Error creating directory '{directory}': {str(dir_error)}")
                            return result

                    # Write to the file
                    try:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        result["output"] = f"Successfully wrote to file: {filepath}"
                        result["executed"] = True
                        logger.debug(f"Successfully wrote to file '{filepath}'")
                    except Exception as write_error:
                        result["output"] = f"Error writing to file: {str(write_error)}"
                        logger.error(f"Error writing to file '{filepath}': {str(write_error)}")
                else:
                    result["output"] = "Invalid write format. Use write:filepath content"
                    logger.warning(f"Invalid write format: {command}")

            # Append operation
            elif command.startswith("append:"):
                logger.debug(f"Processing file append command: {command}")
                parts = command[7:].strip().split(" ", 1)
                if len(parts) == 2:
                    filepath, content = parts

                    # Request approval for file appending
                    approval_handler = ApprovalHandler(True, False)  # Always require approval for appending
                    preview_content = content[:50] + ("..." if len(content) > 50 else "")
                    approved, _ = approval_handler.request_approval(
                        f"Append to file: {filepath}\nContent: {preview_content}"
                    )

                    if not approved:
                        result["output"] = "File appending was denied."
                        logger.info(f"Appending to file '{filepath}' was denied by user")
                        return result

                    # Append to the file
                    try:
                        with open(filepath, 'a') as f:
                            f.write(content)
                        result["output"] = f"Successfully appended to file: {filepath}"
                        result["executed"] = True
                        logger.debug(f"Successfully appended to file '{filepath}'")
                    except Exception as append_error:
                        result["output"] = f"Error appending to file: {str(append_error)}"
                        logger.error(f"Error appending to file '{filepath}': {str(append_error)}")
                else:
                    result["output"] = "Invalid append format. Use append:filepath content"
                    logger.warning(f"Invalid append format: {command}")

            # List files in directory
            elif command.startswith("list:"):
                logger.debug(f"Processing file list command: {command}")
                directory = command[5:].strip()

                if os.path.exists(directory) and os.path.isdir(directory):
                    try:
                        files = os.listdir(directory)
                        file_details = []

                        for file in files:
                            full_path = os.path.join(directory, file)
                            size = os.path.getsize(full_path)
                            file_type = "d" if os.path.isdir(full_path) else "f"
                            file_details.append(f"{file_type} {size:8d} {file}")

                        result["output"] = "\n".join(file_details)
                        result["executed"] = True
                        logger.debug(f"Listed {len(files)} files in directory '{directory}'")
                    except Exception as list_error:
                        result["output"] = f"Error listing directory: {str(list_error)}"
                        logger.error(f"Error listing directory '{directory}': {str(list_error)}")
                else:
                    result["output"] = f"Directory not found: {directory}"
                    logger.warning(f"Directory not found: '{directory}'")

            else:
                result["output"] = "Unknown files command. Use read:, write:, append:, or list:"
                logger.warning(f"Unknown files command: {command}")

        except Exception as e:
            logger.error(f"Error processing files command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = FilesProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)