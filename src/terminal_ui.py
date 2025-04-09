"""
An improved terminal user interface for Neo AI using prompt_toolkit.
This provides a more interactive and visually appealing experience.
"""

import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import clear
from prompt_toolkit import print_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import WordCompleter
import re

# Define colors and styles
NEO_STYLE = Style.from_dict({
    'prompt': 'ansigreen bold',
    'command': 'ansiyellow',
    'output': 'ansiblue',
    'error': 'ansired',
    'info': 'ansimagenta',
    'highlight': 'ansicyan underline',
})

# Key bindings for additional functionality
kb = KeyBindings()

@kb.add('c-l')  # Clear screen with Ctrl+L
def _(event):
    clear()

@kb.add('c-d')  # Exit on Ctrl+D
def _(event):
    event.app.exit()

class ImprovedTerminalUI:
    """A more sophisticated terminal UI for Neo AI."""

    def __init__(self, neo_ai, config):
        """Initialize the terminal UI with Neo AI instance and config."""
        self.neo_ai = neo_ai
        self.config = config
        self.commands = ['help', 'history', 'clear', 'exit']

        # Create history file in user's home directory
        history_file = os.path.expanduser('~/.neo_history.txt')

        # Make sure history file exists and is a file, not a directory
        history_dir = os.path.dirname(history_file)
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        # If history_file is a directory, remove it and create a file
        if os.path.isdir(history_file):
            import shutil
            shutil.rmtree(history_file)

        # Create the file if it doesn't exist
        if not os.path.exists(history_file):
            with open(history_file, 'w') as f:
                pass

        # Create a custom completer that only works at the beginning of the line
        class CommandStartCompleter(WordCompleter):
            def get_completions(self, document, complete_event):
                # Only complete if we're at the start of the line or within the first word
                text_before_cursor = document.text_before_cursor
                if not text_before_cursor.strip() or ' ' not in text_before_cursor:
                    yield from super().get_completions(document, complete_event)

        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=kb,
            style=NEO_STYLE,
            complete_while_typing=True,
            completer=CommandStartCompleter(self.commands)
        )

        # Define patterns for command highlighting
        self.command_pattern = re.compile(r'<system>(.*?)</system>', re.DOTALL)
        self.highlight_pattern = re.compile(r'\*\*(.*?)\*\*')

    def print_banner(self):
        """Print Neo AI welcome banner."""
        banner = """
       Welcome to Neo AI Terminal !                    
        """
        print_formatted_text(HTML(f'<ansicyan>{banner}</ansicyan>'))

    def print_help(self):
        """Display help menu."""
        help_text = """
<info>Available commands:</info>
  • <highlight>help</highlight>    - Show this help menu
  • <highlight>history</highlight> - Show conversation history
  • <highlight>clear</highlight>   - Clear the screen
  • <highlight>exit</highlight>    - Exit Neo AI

<info>Tips:</info>
  • Use <highlight>Tab</highlight> for command completion
  • Use <highlight>Up/Down</highlight> arrows to navigate command history
  • Use <highlight>Ctrl+L</highlight> to clear the screen
  • Use <highlight>Ctrl+D</highlight> to exit
        """
        print_formatted_text(HTML(help_text), style=NEO_STYLE)

    def format_ai_response(self, response):
        """Format AI responses for better readability."""
        # Highlight commands
        formatted = response

        # Format bold text (** **)
        formatted = self.highlight_pattern.sub(
            lambda m: f'<b>{m.group(1)}</b>',
            formatted
        )

        # Handle detected commands - just for visual presentation
        if '<system>' in formatted and '</system>' in formatted:
            formatted = self.command_pattern.sub(
                lambda m: f'\n<ansiyellow>Command:</ansiyellow> <ansicyan>{m.group(1)}</ansicyan>\n',
                formatted
            )

        return formatted

    def display_history(self):
        """Display conversation history with improved formatting."""
        print_formatted_text(HTML('<b><u>Conversation History:</u></b>'), style=NEO_STYLE)

        history = self.neo_ai.get_conversation_history()
        if not history:
            print_formatted_text(HTML('<i>No conversation history yet.</i>'), style=NEO_STYLE)
            return

        for i, entry in enumerate(history, 1):
            role = "You" if entry["role"] == "user" else "Neo"
            content = entry["content"]

            # Format content based on role
            if role == "Neo":
                content = self.format_ai_response(content)
                print_formatted_text(HTML(f'<b><ansiblue>{role}:</ansiblue></b> {content}'), style=NEO_STYLE)
            else:
                print_formatted_text(HTML(f'<b><ansigreen>{role}:</ansigreen></b> {content}'), style=NEO_STYLE)

            # Add separator between messages
            if i < len(history):
                print_formatted_text(HTML('<ansigray>─────────────────────────────────────</ansigray>'), style=NEO_STYLE)

    def highlight_command(self, command):
        """Format command for improved visibility."""
        return HTML(f'<ansiyellow>Command:</ansiyellow> <ansicyan>{command}</ansicyan>')

    def run(self):
        """Run the interactive terminal UI."""
        self.print_banner()

        while True:
            try:
                # Display custom prompt with username
                username = os.getlogin()
                prompt_text = HTML(f'<prompt>{username}@neo</prompt> > ')

                # Get user input with the session
                user_input = self.session.prompt(prompt_text, style=NEO_STYLE)

                # Process commands
                user_input = user_input.strip()
                if not user_input:
                    continue

                if user_input.lower() == 'exit':
                    print_formatted_text(HTML('<ansired>Goodbye! Have a great day!</ansired>'), style=NEO_STYLE)
                    break

                elif user_input.lower() == 'help':
                    self.print_help()

                elif user_input.lower() == 'history':
                    self.display_history()

                elif user_input.lower() == 'clear':
                    clear()
                    self.print_banner()

                else:
                    # Send query to Neo AI
                    print_formatted_text(HTML('<output>Thinking...</output>'), style=NEO_STYLE)
                    self.neo_ai.query(user_input)

            except KeyboardInterrupt:
                print_formatted_text(HTML('\n<ansired>Interrupted. Type "exit" to quit.</ansired>'), style=NEO_STYLE)

            except EOFError:
                print_formatted_text(HTML('\n<ansired>Goodbye! Have a great day!</ansired>'), style=NEO_STYLE)
                break

            except Exception as e:
                print_formatted_text(HTML(f'<error>Error: {str(e)}</error>'), style=NEO_STYLE)