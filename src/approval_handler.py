"""
Enhanced approval handler for Neo AI command execution.
Uses a simple bash-style prompt UI for command approval.
"""

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt

# Define approval style
APPROVAL_STYLE = Style.from_dict({
    'prompt': '#5fd7ff bold',      # Bright cyan for Neo prompt
    'command': '#ffffff',          # White for command text
    'arrow': '#d787af bold',       # Pink for the arrow
    'question': '#d7d787',         # Light yellow for question
    'success': '#98fb98',          # Pale Green for success
    'error': '#ff6b6b',            # Soft Red for error
})


class ApprovalHandler:
    """Handle command approval requests with a bash-style prompt UI."""

    def __init__(self, require_approval=True, auto_approve_all=False):
        """Initialize approval handler with settings."""
        self.require_approval = require_approval
        self.auto_approve_all = auto_approve_all

    def request_approval(self, command):
        """
        Request approval for command execution with bash-style prompt UI.

        Args:
            command (str): Command to be approved

        Returns:
            bool: True if approved, False otherwise
            str: Always None as we've removed the 'approve all' option
        """
        if not self.require_approval or self.auto_approve_all:
            return True, None

        # Print the command in bash-style format
        print_formatted_text(HTML(f"\n<prompt>neo ></prompt> <command>{command}</command>"), style=APPROVAL_STYLE)

        # Print the approval prompt with an arrow
        print_formatted_text(HTML("  <arrow>↳</arrow> <question>Execute this command? [Enter/n]:</question>"), style=APPROVAL_STYLE)

        # Get user input
        user_input = prompt("").strip().lower()

        # Handle approval/rejection
        if user_input == 'n' or user_input == 'no':
            print_formatted_text(HTML("  <error>✗</error>"), style=APPROVAL_STYLE)
            return False, None
        else:
            print_formatted_text(HTML("  <success>✓</success>"), style=APPROVAL_STYLE)
            return True, None