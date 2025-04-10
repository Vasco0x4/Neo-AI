import re
import os
import shutil
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

# Define output style
OUTPUT_STYLE = Style.from_dict({
    'command': '#ffb347 bold',  # Orange
    'output': '#87ceeb',        # Sky Blue
    'error': '#ff6b6b',         # Soft Red
    'success': '#98fb98',       # Pale Green
    'warning': '#ffa07a',       # Light Salmon
    'system': '#d8bfd8 italic', # Thistle
    'highlight': '#40e0d0',     # Turquoise
    'sudo': '#ff5555 bold',     # Bright red for sudo commands
})

class CommandDisplay:
    """Handle display formatting for commands and their outputs."""

    def __init__(self):
        """Initialize the command display handler."""
        # Get terminal width for formatting
        self.term_width = shutil.get_terminal_size().columns

        # Patterns for formatting
        self.cmd_pattern = re.compile(r'<s>(.*?)</s>', re.DOTALL)
        self.error_pattern = re.compile(r'Error:|ERROR:|Failed:|fail|permission denied', re.IGNORECASE)
        self.success_pattern = re.compile(r'Success:|Completed:|Done:|successful', re.IGNORECASE)
        self.warning_pattern = re.compile(r'Warning:|WARN:|Caution:', re.IGNORECASE)

        # Additional patterns for sudo detection
        self.sudo_pattern = re.compile(r'^sudo\s+|[;&|]\s*sudo\s+', re.MULTILINE)

        # Patterns for specific command output interpretation
        self.apt_update_pattern = re.compile(r'(\d+)\s+packages can be upgraded')
        self.disk_usage_pattern = re.compile(r'(\d+)%\s+\/')

    def is_sudo_command(self, command):
        """Check if a command uses sudo."""
        return command.strip().startswith('sudo ') or re.search(r'[;&|]\s*sudo\s+', command)

    def format_command(self, command):
        """Format a command for display with sudo highlighting."""
        if self.is_sudo_command(command):
            # Add sudo icon and highlight
            return f"\n{'─' * self.term_width}\n🔐 <sudo>{command}</sudo>\n{'─' * self.term_width}"
        else:
            # Regular command formatting
            return f"\n{'─' * self.term_width}\n📎 <command>{command}</command>\n{'─' * self.term_width}"

    def format_output(self, output, command):
        """Format command output with syntax highlighting and enhanced interpretation."""
        # Determine if output contains errors, warnings, etc.
        has_error = bool(self.error_pattern.search(output))
        has_warning = bool(self.warning_pattern.search(output))
        has_success = bool(self.success_pattern.search(output))

        # Special formatting for sudo commands
        is_sudo = self.is_sudo_command(command)

        # Format output based on content
        formatted_output = output

        # Truncate very long outputs
        if len(output.split("\n")) > 20:
            lines = output.split("\n")
            formatted_output = "\n".join(lines[:10] + ["...", "(Output truncated for readability)"] + lines[-5:])

        # Prepare the formatted output with appropriate styling
        if has_error:
            style_class = 'error'
            icon = "❌"
        elif has_warning:
            style_class = 'warning'
            icon = "⚠️"
        elif has_success:
            style_class = 'success'
            icon = "✅"
        else:
            style_class = 'output'
            icon = "📄"

        # Add sudo indicator for sudo commands if not already showing an error
        if is_sudo and not has_error:
            icon = "🔒"
            if has_success:
                icon = "🔓✅"  # Unlocked with success

        # Try to extract meaningful information from common command outputs
        summary = self.generate_output_summary(output, command)
        if summary:
            formatted_output += f"\n\n<highlight>Summary:</highlight> {summary}"

        # Format the final output with headers
        result = f"\n{icon} <{style_class}>{formatted_output}</{style_class}>\n"
        result += f"{'─' * self.term_width}\n"

        return result

    def generate_output_summary(self, output, command):
        """Generate a helpful summary based on command output patterns."""
        # Detect apt update results
        apt_match = self.apt_update_pattern.search(output)
        if apt_match and 'apt update' in command:
            return f"{apt_match.group(1)} packages can be upgraded. Consider running 'sudo apt upgrade' to install them."

        # Detect disk usage warnings
        disk_match = self.disk_usage_pattern.search(output)
        if disk_match and 'df' in command:
            usage = int(disk_match.group(1))
            if usage > 90:
                return f"Warning: Disk usage is at {usage}%, which is very high. Consider freeing up space."
            elif usage > 75:
                return f"Note: Disk usage is at {usage}%, getting close to threshold."

        # If no specific pattern matched
        return None

    def print_command_execution(self, command):
        """Print a notification that a command is being executed."""
        formatted_cmd = self.format_command(command)
        print_formatted_text(HTML(formatted_cmd), style=OUTPUT_STYLE)

        if self.is_sudo_command(command):
            print_formatted_text(HTML("<sudo>Executing with elevated privileges...</sudo>"), style=OUTPUT_STYLE)
        else:
            print_formatted_text(HTML("<system>Executing command...</system>"), style=OUTPUT_STYLE)

    def print_command_output(self, output, command):
        """Print the formatted output of a command."""
        formatted_output = self.format_output(output, command)
        print_formatted_text(HTML(formatted_output), style=OUTPUT_STYLE)

    def extract_commands(self, text):
        """Extract commands from <s> tags in a text."""
        commands = self.cmd_pattern.findall(text)
        return commands

    def replace_tags_with_display(self, text):
        """Replace <s> tags with visually formatted command displays."""
        def replacement(match):
            cmd = match.group(1).strip()
            if self.is_sudo_command(cmd):
                return f"\n**Sudo Command:** `{cmd}`\n"
            else:
                return f"\n**Command:** `{cmd}`\n"

        return self.cmd_pattern.sub(replacement, text)

    def format_approval_request(self, command):
        """Format a command approval request."""
        terminal_width = self.term_width
        box_width = min(terminal_width - 4, 80)

        # Create a box for the approval request
        top_border = "┌" + "─" * (box_width - 2) + "┐"
        bottom_border = "└" + "─" * (box_width - 2) + "┘"

        # Format the command text to fit in the box
        command_lines = []
        line = ""
        for word in command.split():
            if len(line + " " + word) <= box_width - 6:
                line += " " + word if line else word
            else:
                command_lines.append(line)
                line = word
        if line:
            command_lines.append(line)

        # Build the message box with sudo highlighting if needed
        message = [top_border]

        if self.is_sudo_command(command):
            message.append("│ <sudo>🔐 Sudo Command Approval Required:</sudo>" + " " * (box_width - 38) + "│")
        else:
            message.append("│ <warning>Command Approval Required:</warning>" + " " * (box_width - 29) + "│")

        for line in command_lines:
            padding = " " * (box_width - 4 - len(line))
            if self.is_sudo_command(command):
                message.append(f"│ <sudo>{line}</sudo>{padding} │")
            else:
                message.append(f"│ <command>{line}</command>{padding} │")

        message.append("│" + " " * (box_width - 2) + "│")

        if self.is_sudo_command(command):
            message.append("│ <sudo>Approve? (y/n) - requires elevated privileges</sudo>" + " " * (box_width - 49) + "│")
        else:
            message.append("│ <system>Approve? (y/n/T for approve all)</system>" + " " * (box_width - 37) + "│")

        message.append(bottom_border)

        return "\n".join(message)