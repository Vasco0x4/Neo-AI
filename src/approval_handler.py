"""
Enhanced approval handler for Neo AI command execution.
Provides a cleaner, more minimalist interface for command approval.
"""

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt
import shutil

# Define approval style
APPROVAL_STYLE = Style.from_dict({
    'command': '#5fd7ff bold',     # Bright cyan for command
    'question': '#d7d787',         # Light yellow for question
    'border': '#767676',           # Gray for borders
    'label': '#d787af bold',       # Pink for labels
})


class ApprovalHandler:
    """Handle command approval requests with an improved UI."""

    def __init__(self, require_approval=True, auto_approve_all=False):
        """Initialize approval handler with settings."""
        self.require_approval = require_approval
        self.auto_approve_all = auto_approve_all
        # Get terminal width for formatting
        self.term_width = shutil.get_terminal_size().columns

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

        # Calculate box width based on terminal width and command length
        box_width = min(self.term_width - 2, max(50, len(command) + 10))

        # Create the top border with label
        top_border = f"<border>╭─ </border><label>Command</label><border> {'─' * (box_width - 11)}╮</border>"

        # Format command with padding
        command_line = f"<border>│</border>  {self.format_command(command)}{' ' * (box_width - len(command) - 3)}<border>│</border>"

        # Create the bottom border with question
        bottom_border = f"<border>╰─ </border><question>Execute? (y/n/t)</question><border> {'─' * (box_width - 19)}╯</border>"

        # Print the approval request
        print_formatted_text(HTML(f"\n{top_border}"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(command_line), style=APPROVAL_STYLE)
        print_formatted_text(HTML(bottom_border), style=APPROVAL_STYLE)

        # Get user input with a minimal prompt
        user_input = prompt("").strip().lower()

        # Add empty line after response for better readability
        print()

        if user_input == 'y':
            return True, None
        elif user_input == 't':
            self.auto_approve_all = True
            print_formatted_text(HTML("<label>All future commands will be approved automatically</label>"),
                                 style=APPROVAL_STYLE)
            return True, 'all'
        else:
            print_formatted_text(HTML("<question>Command execution cancelled</question>"), style=APPROVAL_STYLE)
            return False, None