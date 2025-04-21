"""
Protocol registry for MCP.
This module manages the registration and retrieval of protocol handlers.
"""

import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("mcp_protocol")


class ProtocolHandler:
    """Base class for protocol handlers."""

    def __init__(self, name: str):
        """
        Initialize a protocol handler.

        Args:
            name: Name of the protocol
        """
        self.name = name

    def handle(self, content: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle a protocol command.

        Args:
            content: Command content
            require_approval: Whether approval is required
            auto_approve: Whether to auto-approve

        Returns:
            Dictionary with execution results
        """
        raise NotImplementedError("Protocol handlers must implement handle method")


class ProtocolRegistry:
    """Registry for MCP protocol handlers."""

    def __init__(self):
        """Initialize the protocol registry."""
        self.handlers: Dict[str, ProtocolHandler] = {}

    def register_handler(self, handler: ProtocolHandler) -> None:
        """
        Register a protocol handler.

        Args:
            handler: Protocol handler to register
        """
        name = handler.name

        if name in self.handlers:
            logger.warning(f"Overriding existing protocol handler for '{name}'")

        self.handlers[name] = handler
        logger.info(f"Registered protocol handler for '{name}'")

    def get_handler(self, protocol_name: str) -> ProtocolHandler:
        """
        Get a protocol handler by name.

        Args:
            protocol_name: Name of the protocol

        Returns:
            Protocol handler for the specified protocol

        Raises:
            KeyError: If no handler is found for the protocol
        """
        if protocol_name not in self.handlers:
            raise KeyError(f"No handler found for protocol '{protocol_name}'")

        return self.handlers[protocol_name]

    def has_handler(self, protocol_name: str) -> bool:
        """
        Check if a handler exists for a protocol.

        Args:
            protocol_name: Name of the protocol

        Returns:
            True if a handler exists, False otherwise
        """
        return protocol_name in self.handlers