"""
Core implementation of the Machine Communication Protocol (MCP).
This module provides the main protocol parser and executor.
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from .registry import ProtocolRegistry

logger = logging.getLogger("mcp_protocol")


class MCPProtocol:
    """
    Main class for handling Machine Communication Protocol (MCP) tags and execution.
    Uses a registry to manage protocol handlers.
    """

    def __init__(self):
        """Initialize the MCP protocol handler."""
        # Registry for protocol handlers
        self.registry = ProtocolRegistry()

        # Main pattern for extracting MCP tags
        self.mcp_pattern = re.compile(r'<mcp:(\w+)>(.*?)</mcp:\1>', re.DOTALL)

        # Legacy patterns for backward compatibility
        self.legacy_patterns = [
            re.compile(r'<system>(.*?)</system>', re.DOTALL),
            re.compile(r'<s>(.*?)</s>', re.DOTALL)
        ]

    def parse_mcp_tags(self, text: str) -> List[Tuple[str, str]]:
        """
        Parse all MCP protocol tags in the provided text.

        Args:
            text: The text to parse for MCP tags

        Returns:
            List of tuples containing (protocol_name, command_content)
        """
        mcp_tags = []

        # Extract MCP tags
        mcp_matches = self.mcp_pattern.findall(text)
        for protocol, content in mcp_matches:
            mcp_tags.append((protocol.lower(), content.strip()))

        # Extract legacy tags (for backward compatibility)
        for pattern in self.legacy_patterns:
            legacy_matches = pattern.findall(text)
            for content in legacy_matches:
                # Map legacy tags to the terminal protocol
                mcp_tags.append(("terminal", content.strip()))

        return mcp_tags

    def process_response(self, response: str,
                         require_approval: bool = True,
                         auto_approve: bool = False) -> Dict[str, Any]:
        """
        Process a response text containing MCP tags.

        Args:
            response: Text containing MCP protocol tags
            require_approval: Whether commands require user approval
            auto_approve: Whether to auto-approve all commands

        Returns:
            Dictionary with execution results for each protocol
        """
        results = {}

        try:
            # Extract all MCP tags
            mcp_tags = self.parse_mcp_tags(response)

            for protocol, content in mcp_tags:
                logger.debug(f"Processing {protocol} protocol with content: {content[:50]}...")

                if self.registry.has_handler(protocol):
                    # Get the handler for this protocol
                    handler = self.registry.get_handler(protocol)

                    # Execute the handler with the content
                    result = handler.handle(content, require_approval, auto_approve)
                    results[protocol] = result

                    logger.debug(f"Protocol {protocol} execution completed")
                else:
                    logger.warning(f"Unknown protocol '{protocol}'. Ignoring command: {content}")
                    results[protocol] = {"error": f"Unknown protocol '{protocol}'"}

        except Exception as e:
            logger.error(f"Error processing MCP tags: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            results["error"] = str(e)

        return results