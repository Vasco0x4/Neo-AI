"""
Memory protocol handler for MCP.
This protocol handles storing and retrieving information.
"""

import logging
from typing import Dict, Any
from ..registry import ProtocolHandler

logger = logging.getLogger("mcp_protocol.memory")


class MemoryProtocolHandler(ProtocolHandler):
    """Handler for memory protocol commands."""

    def __init__(self):
        """Initialize the memory protocol handler."""
        super().__init__("memory")
        # In-memory storage for values
        self.memory_store: Dict[str, Any] = {}

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle memory protocol commands (store/retrieve data).

        Args:
            command: The memory command (save:key=value or get:key)
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
            # Save operation
            if command.startswith("save:"):
                logger.debug(f"Processing memory save command: {command}")
                # Extract key=value pair
                kv_part = command[5:].strip()
                if "=" in kv_part:
                    key, value = kv_part.split("=", 1)
                    self.memory_store[key.strip()] = value.strip()
                    result["output"] = f"Saved '{key.strip()}' to memory."
                    result["executed"] = True
                    logger.debug(f"Saved key '{key.strip()}' with value '{value.strip()}'")
                else:
                    result["output"] = "Invalid save format. Use save:key=value"
                    logger.warning(f"Invalid save format: {command}")

            # Get operation
            elif command.startswith("get:"):
                logger.debug(f"Processing memory get command: {command}")
                key = command[4:].strip()
                if key in self.memory_store:
                    result["output"] = self.memory_store[key]
                    result["executed"] = True
                    logger.debug(f"Retrieved key '{key}' with value '{self.memory_store[key]}'")
                else:
                    result["output"] = f"Key '{key}' not found in memory."
                    logger.warning(f"Key '{key}' not found in memory store")

            # List operation
            elif command == "list":
                logger.debug("Processing memory list command")
                if self.memory_store:
                    result["output"] = "\n".join([f"{k}: {v}" for k, v in self.memory_store.items()])
                    logger.debug(f"Listed {len(self.memory_store)} items from memory")
                else:
                    result["output"] = "Memory is empty."
                    logger.debug("Memory store is empty")
                result["executed"] = True

            # Clear operation
            elif command == "clear":
                logger.debug("Processing memory clear command")
                keys_count = len(self.memory_store)
                self.memory_store.clear()
                result["output"] = f"Memory cleared ({keys_count} items removed)."
                result["executed"] = True
                logger.debug(f"Cleared {keys_count} items from memory")

            else:
                result["output"] = "Unknown memory command. Use save:, get:, list, or clear."
                logger.warning(f"Unknown memory command: {command}")

        except Exception as e:
            logger.error(f"Error processing memory command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = MemoryProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)