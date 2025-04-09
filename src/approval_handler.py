"""
Enhanced approval handler for Neo AI command execution.
Provides a cleaner, more minimalist interface for command approval.
"""

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt

# Define approval style
APPROVAL_STYLE = Style.from_dict({
    'command': '#ffb347 bold',  # Orange
    'question': '#87ceeb',  # Sky Blue
    'line': '#cccccc',  # Light Gray
})


class ApprovalHandler:
    """Handle command approval requests with an improved UI."""

    def __init__(self, require_approval=True, auto_approve_all=False):
        """Initialize approval handler with settings."""
        self.require_approval = require_approval
        self.auto_approve_all = auto_approve_all

    def format_command(self, command):
        """Format command for display."""
        return f"<command>{command}</command>"

    def request_approval(self, command):
        """
        Request approval for command execution with improved UI.

        Args:
            command (str): Command to be approved

        Returns:
            bool: True if approved, False otherwise
            str: 'all' if approve all was selected
        """
        if not self.require_approval or self.auto_approve_all:
            return True, None

        # Create minimal separator
        separator = "─" * 40

        # Print the approval request
        print_formatted_text(HTML(f"\n<line>{separator}</line>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"Command: {self.format_command(command)}"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<question>Approve? (y/n/T for all)</question>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<line>{separator}</line>"), style=APPROVAL_STYLE)

        # Get user input
        user_input = prompt("").strip().lower()
        print()  # Add empty line after response

        if user_input == 'y':
            return True, None
        elif user_input == 't':
            self.auto_approve_all = True
            print_formatted_text(HTML("<s>All future commands will be approved automatically</s>"),
                                 style=APPROVAL_STYLE)
            return True, 'all'
        else:
            print_formatted_text(HTML("<e>Command execution cancelled</e>"), style=APPROVAL_STYLE)
            return False, None