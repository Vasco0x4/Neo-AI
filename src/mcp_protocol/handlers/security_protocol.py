"""
Security protocol handler for MCP.
This protocol handles security-related operations.
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

# Import terminal handler to execute security commands
from .terminal_protocol import handler as terminal_handler

logger = logging.getLogger("mcp_protocol.security")


class SecurityProtocolHandler(ProtocolHandler):
    """Handler for security protocol commands."""

    def __init__(self):
        """Initialize the security protocol handler."""
        super().__init__("security")

        # Define the security commands
        self.security_commands = {
            "users": "cat /etc/passwd | grep -v '/nologin' | grep -v '/false'",
            "groups": "cat /etc/group",
            "ports": "netstat -tuln || ss -tuln",
            "sudo": "sudo -l",
            "listening": "lsof -i -P -n | grep LISTEN || netstat -tuln | grep LISTEN || ss -tuln | grep LISTEN",
            "accounts": "lastlog | grep -v 'Never logged in'",
            "logins": "last -n 20",
            "history": "history | tail -n 20",
            "suid": "find / -perm -4000 -ls 2>/dev/null | head -20",
            "sgid": "find / -perm -2000 -ls 2>/dev/null | head -20",
            "processes": "ps aux --forest",
            "kernelmodules": "lsmod",
            "capabilities": "getcap -r / 2>/dev/null || echo 'getcap command not found'",
            "cronjobs": "crontab -l 2>/dev/null; ls -la /etc/cron*/ 2>/dev/null",
            "ssh-config": "cat /etc/ssh/sshd_config 2>/dev/null | grep -v '^#' | grep -v '^$'",
            "failed-logins": "grep 'Failed password' /var/log/auth.log 2>/dev/null || journalctl -u sshd 2>/dev/null | grep 'Failed password'"
        }

    def handle(self, command: str, require_approval: bool, auto_approve: bool) -> Dict[str, Any]:
        """
        Handle security protocol commands (security operations).

        Args:
            command: The security command
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
            if command in self.security_commands:
                logger.debug(f"Processing security command: {command}")
                security_command = self.security_commands[command]

                # Execute the security command using terminal protocol
                terminal_result = terminal_handler.handle(
                    security_command, require_approval, auto_approve
                )

                # Add security operation type to result
                terminal_result["security_operation"] = command
                return terminal_result

            elif command.startswith("check:"):
                # Custom security check - format: check:file or directory
                logger.debug(f"Processing custom security check: {command}")
                target = command[6:].strip()
                target = shlex.quote(target)

                # Check permissions, owner, and other security attributes
                check_command = f"ls -la {target} 2>/dev/null && find {target} -type f -perm -o+w -ls 2>/dev/null | head -10"

                terminal_result = terminal_handler.handle(
                    check_command, require_approval, auto_approve
                )

                terminal_result["security_operation"] = "check"
                return terminal_result

            elif command.startswith("vulnerabilities:"):
                # Check for known vulnerabilities - format: vulnerabilities:package
                logger.debug(f"Processing vulnerabilities check: {command}")
                package = command[16:].strip()
                package = shlex.quote(package)

                # Try to check using available tools
                check_command = f"apt list --installed 2>/dev/null | grep {package} || rpm -q {package} 2>/dev/null || pacman -Qi {package} 2>/dev/null"

                terminal_result = terminal_handler.handle(
                    check_command, require_approval, auto_approve
                )

                terminal_result["security_operation"] = "vulnerabilities"
                return terminal_result

            else:
                valid_commands = ", ".join(sorted(self.security_commands.keys()))
                special_commands = "check:file/dir, vulnerabilities:package"
                result["output"] = f"Unknown security command. Valid options: {valid_commands}, {special_commands}"
                logger.warning(f"Unknown security command: {command}")

        except Exception as e:
            logger.error(f"Error processing security command: {str(e)}")
            result["error"] = str(e)

        return result


# Create singleton instance
handler = SecurityProtocolHandler()


def register():
    """Register this protocol handler."""
    from .. import mcp
    mcp.registry.register_handler(handler)