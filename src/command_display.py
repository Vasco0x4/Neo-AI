"""
Enhanced command display and output formatting for Neo AI.
This module handles the visual presentation of commands and their outputs.
"""

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
})

class CommandDisplay:
    """Handle display formatting for commands and their outputs."""

    def __init__(self):
        """Initialize the command display handler."""
        # Get terminal width for formatting
        self.term_width = shutil.get_terminal_size().columns

        # Patterns for formatting
        self.cmd_pattern = re.compile(r'<s>(.*?)</s>', re.DOTALL)
        self.error_pattern = re.compile(r'Error:|ERROR:|Failed:', re.IGNORECASE)
        self.success_pattern = re.compile(r'Success:|Completed:|Done:', re.IGNORECASE)
        self.warning_pattern = re.compile(r'Warning:|WARN:|Caution:', re.IGNORECASE)

    def format_command(self, command):
        """Format a command for display."""
        return f"\n{'─' * self.term_width}\n📎 <command>{command}</command>\n{'─' * self.term_width}"

    def format_output(self, output, command):
        """Format command output with syntax highlighting."""
        # Determine if output contains errors
        has_error = bool(self.error_pattern.search(output))
        has_warning = bool(self.warning_pattern.search(output))
        has_success = bool(self.success_pattern.search(output))

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

        # Format the final output with headers
        result = f"\n{icon} <{style_class}>{formatted_output}</{style_class}>\n"
        result += f"{'─' * self.term_width}\n"

        return result

    def print_command_execution(self, command):
        """Print a notification that a command is being executed."""
        formatted_cmd = self.format_command(command)
        print_formatted_text(HTML(formatted_cmd), style=OUTPUT_STYLE)
        print_formatted_text(HTML("<s>Executing command...</s>"), style=OUTPUT_STYLE)

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

        # Build the message box
        message = [top_border]
        message.append("│ <warning>Command Approval Required:</warning>" + " " * (box_width - 29) + "│")
        for line in command_lines:
            padding = " " * (box_width - 4 - len(line))
            message.append(f"│ <command>{line}</command>{padding} │")
        message.append("│" + " " * (box_width - 2) + "│")
        message.append("│ <s>Approve? (y/n/T for approve all)</s>" + " " * (box_width - 37) + "│")
        message.append(bottom_border)

        return "\n".join(message)