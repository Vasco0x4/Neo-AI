"""
Network protocol handler for MCP.
This protocol handles network operations.
"""

import logging
import shlex
from typing import Dict, Any
from ..registry import ProtocolHandler
import sys
import os

# Get the parent directory to import Neo modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(parent_dir)

# Import terminal handler to execute network commands
from .terminal_protocol import handler as terminal_handler

logger = logging.getLogger("mcp_protocol.network")

class NetworkProtocolHandler(ProtocolHandler):
    """Handler for network protocol commands."""

    def __init__(self):
        """Initialize the network protocol handler."""
        super().__init__("network")

        # Define the network commands
        self.network_commands = {
            "connections": "netstat -tuln || ss -tuln",
            "routes": "ip route show || route -n",
            "interfaces": "ip link show || ifconfig",
            "active": "netstat -anp || ss -anp",
            "dns": "cat /etc/resolv.conf",
            "arp": "arp -a || ip neigh",
            "sockets": "netstat -l || ss -l",
            "bandwidth": "iftop -t -s 1 2>/dev/null || echo 'iftop command not found'",
            "hosts": "cat /etc/hosts",
            "ports": "lsof -i -P -n | grep LISTEN || netstat -tuln | grep LISTEN",
            "nat": "iptables -t nat -L 2>/dev/null || echo 'iptables command not found or requires sudo'",
            "firewall": "iptables -L 2>/dev/null || firewall-cmd --list-all 2>/dev/null || echo 'No firewall info available without sudo'",
            "listening": "lsof -i -P -n | grep LISTEN || netstat -tuln | grep LISTEN || ss -tuln | grep LISTEN"
        }

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle network protocol commands (network operations).

        Args:
            command: The network command
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
            # Handle special commands
            if command.startswith("ping:"):
                logger.debug(f"Processing network ping command: {command}")
                host = command[5:].strip()
                host = shlex.quote(host)
                terminal_result = terminal_handler.handle(
                    f"ping -c 4 {host}", require_approval, auto_approve
                )
                terminal_result["network_operation"] = "ping"
                return terminal_result

            elif command.startswith("trace:"):
                logger.debug(f"Processing network trace command: {command}")
                host = command[6:].strip()
                host = shlex.quote(host)
                terminal_result = terminal_handler.handle(
                    f"traceroute {host} 2>/dev/null || tracepath {host}",
                    require_approval, auto_approve
                )
                terminal_result["network_operation"] = "trace"
                return terminal_result

            elif command.startswith("scan:"):
                logger.debug(f"Processing network scan command: {command}")
                target = command[5:].strip()
                target = shlex.quote(target)
                terminal_result = terminal_handler.handle(
                    f"nmap -F {target} 2>/dev/null",
                    require_approval, auto_approve
                )
                terminal_result["network_operation"] = "scan"
                return terminal_result

            elif command.startswith("lookup:"):
                logger.debug(f"Processing network lookup command: {command}")
                host = command[7:].strip()
                host = shlex.quote(host)
                terminal_result = terminal_handler.handle(
                    f"host {host} || nslookup {host} || dig {host}",
                    require_approval, auto_approve
                )
                terminal_result["network_operation"] = "lookup"
                return terminal_result

            elif command.startswith("whois:"):
                logger.debug(f"Processing network whois command: {command}")
                domain = command[6:].strip()
                domain = shlex.quote(domain)
                terminal_result = terminal_handler.handle(
                    f"whois {domain} 2>/dev/null || echo 'whois command not installed'",
                    require_approval, auto_approve
                )
                terminal_result["network_operation"] = "whois"
                return terminal_result

            # Handle standard commands
            elif command in self.network_commands:
                logger.debug(f"Processing network command: {command}")
                network_command = self.network_commands[command]
                terminal_result = terminal_handler.handle(
                    network_command, require_approval, auto_approve
                )
                terminal_result["network_operation"] = command
                return terminal_result

            else:
                valid_commands = ", ".join(sorted(self.network_commands.keys()))
                special_commands = "ping:host, trace:host, scan:target, lookup:host, whois:domain"
                result["output"] = f"Unknown network command. Valid options: {valid_commands}, {special_commands}"
                logger.warning(f"Unknown network command: {command}")

        except Exception as e:
            logger.error(f"Error processing network command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = NetworkProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)