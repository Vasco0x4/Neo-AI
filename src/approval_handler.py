from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt
import shutil
import re

# Define approval style
APPROVAL_STYLE = Style.from_dict({
    'command': '#5fd7ff bold',     # Bright cyan for command
    'question': '#d7d787',         # Light yellow for question
    'border': '#767676',           # Gray for borders
    'label': '#d787af bold',       # Pink for labels
    'sudo_warning': '#ff5f5f',     # Bright red for sudo warnings
    'dangerous': '#ff0000 bold',   # Bold red for dangerous commands
})


class ApprovalHandler:
    """Handle command approval requests with an improved UI."""

    def __init__(self, require_approval=True, auto_approve_all=False):
        """Initialize approval handler with settings."""
        self.require_approval = require_approval
        self.auto_approve_all = auto_approve_all
        # Get terminal width for formatting
        self.term_width = shutil.get_terminal_size().columns

        # List of dangerous command patterns that require extra confirmation
        self.dangerous_patterns = [
            r'sudo\s+(rm|dd|mkfs|fdisk|parted|shred)\s+',
            r'sudo\s+.*(remove|delete|format|wipe|reset).*',
            r'sudo\s+(halt|reboot|poweroff|shutdown)\s+',
            r'sudo\s+chown\s+-R\s+',
            r'sudo\s+chmod\s+-R\s+',
            r'sudo\s+systemctl\s+(disable|stop|mask)\s+',
            r':(){ :\|:& };:',  # Fork bomb
            r'sudo\s+mv\s+.*/dev/null',
            r'sudo\s+>\s+/.*',
            r'sudo\s+.*(password|shadow|passwd)'
        ]

    def format_command(self, command):
        """Format command for display."""
        return f"<command>{command}</command>"

    def is_sudo_command(self, command):
        """Check if command uses sudo."""
        return command.strip().startswith('sudo ') or ' sudo ' in command

    def is_dangerous_command(self, command):
        """Check if command matches any dangerous patterns."""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command):
                return True
        return False

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
            # Even with auto-approve, still show warning for dangerous sudo commands
            if self.is_sudo_command(command) and self.is_dangerous_command(command):
                print_formatted_text(HTML(
                    f"<sudo_warning>⚠️ WARNING: About to execute potentially dangerous sudo command:</sudo_warning>\n"
                    f"<dangerous>{command}</dangerous>\n"
                    f"<sudo_warning>Auto-approve is enabled, but this command requires explicit confirmation.</sudo_warning>"
                ), style=APPROVAL_STYLE)
                user_input = prompt("Continue? (y/n): ").strip().lower()
                if user_input != 'y':
                    return False, None
            elif self.is_sudo_command(command):
                # Just show an informational message for non-dangerous sudo commands
                print_formatted_text(HTML(
                    f"<sudo_warning>ℹ️ Executing sudo command (Auto-approved):</sudo_warning>\n"
                    f"<command>{command}</command>"
                ), style=APPROVAL_STYLE)
            return True, None

        # Check if it's a sudo command
        is_sudo = self.is_sudo_command(command)
        is_dangerous = self.is_dangerous_command(command)

        # Calculate box width based on terminal width and command length
        box_width = min(self.term_width - 2, max(50, len(command) + 10))

        # Create the top border with appropriate label
        if is_sudo and is_dangerous:
            top_border = f"<border>╭─ </border><sudo_warning>⚠️ DANGEROUS SUDO COMMAND ⚠️</sudo_warning><border> {'─' * (box_width - 29)}╮</border>"
        elif is_sudo:
            top_border = f"<border>╭─ </border><sudo_warning>⚠️ SUDO COMMAND</sudo_warning><border> {'─' * (box_width - 17)}╮</border>"
        else:
            top_border = f"<border>╭─ </border><label>Command</label><border> {'─' * (box_width - 11)}╮</border>"

        # Format command with padding
        command_line = f"<border>│</border>  {self.format_command(command)}{' ' * max(1, box_width - len(command) - 3)}<border>│</border>"

        # Add warning line for dangerous sudo commands
        warning_lines = []
        if is_sudo and is_dangerous:
            warning = "This command has elevated privileges and could potentially harm your system!"
            warning_lines.append(f"<border>│</border>  <dangerous>{warning}</dangerous>{' ' * max(1, box_width - len(warning) - 3)}<border>│</border>")
        elif is_sudo:
            warning = "This command will be executed with elevated privileges."
            warning_lines.append(f"<border>│</border>  <sudo_warning>{warning}</sudo_warning>{' ' * max(1, box_width - len(warning) - 3)}<border>│</border>")

        # Create the bottom border with question
        execute_prompt = "Execute? (y/n/t)"
        if is_sudo and is_dangerous:
            execute_prompt = "Execute DANGEROUS command? (y/n)"
            bottom_border = f"<border>╰─ </border><dangerous>{execute_prompt}</dangerous><border> {'─' * (box_width - len(execute_prompt) - 4)}╯</border>"
        else:
            bottom_border = f"<border>╰─ </border><question>{execute_prompt}</question><border> {'─' * (box_width - len(execute_prompt) - 4)}╯</border>"

        # Print the approval request
        print_formatted_text(HTML(f"\n{top_border}"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(command_line), style=APPROVAL_STYLE)

        # Print any warning lines
        for line in warning_lines:
            print_formatted_text(HTML(line), style=APPROVAL_STYLE)

        print_formatted_text(HTML(bottom_border), style=APPROVAL_STYLE)

        # Get user input with a minimal prompt
        user_input = prompt("").strip().lower()

        # Add empty line after response for better readability
        print()

        # For dangerous sudo commands, don't allow 'all' approval and require explicit 'y'
        if is_sudo and is_dangerous:
            if user_input == 'y':
                return True, None
            else:
                print_formatted_text(HTML("<question>Command execution cancelled</question>"), style=APPROVAL_STYLE)
                return False, None

        # Normal approval flow
        if user_input == 'y':
            return True, None
        elif user_input == 't' and not (is_sudo and is_dangerous):
            self.auto_approve_all = True
            print_formatted_text(HTML(
                "<label>All future commands will be approved automatically</label>\n"
                "<sudo_warning>Note: Dangerous sudo commands will still require explicit approval</sudo_warning>"
            ), style=APPROVAL_STYLE)
            return True, 'all'
        else:
            print_formatted_text(HTML("<question>Command execution cancelled</question>"), style=APPROVAL_STYLE)
            return False, None