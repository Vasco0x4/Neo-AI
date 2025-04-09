"""
Interactive command support for Neo AI.
This module handles interactive terminal commands that may require user input.
"""

import os
import pty
import select
import threading
import time
import logging
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style

# Define style for interactive prompts
INTERACTIVE_STYLE = Style.from_dict({
    'prompt': '#ffb347 bold',  # Orange
    'text': '#87ceeb',  # Sky Blue
})


class InteractiveCommandHandler:
    """Handles interactive commands that require user input."""

    def __init__(self):
        self.active_process = None
        self.master_fd = None
        self.should_continue = True
        self.input_queue = []

    def _read_process_output(self, master_fd):
        """Read and display output from the process."""
        while self.should_continue:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if r:
                    data = os.read(master_fd, 1024)
                    if data:
                        # Display the output
                        output = data.decode('utf-8', errors='replace')
                        print_formatted_text(HTML(f"<text>{output}</text>"), style=INTERACTIVE_STYLE, end='')
                    else:
                        # EOF
                        break
            except Exception as e:
                logging.error(f"Error reading from process: {e}")
                break

    def _handle_user_input(self, master_fd):
        """Handle user input to the process."""
        while self.should_continue:
            try:
                # Wait for user input or input from queue
                if self.input_queue:
                    user_input = self.input_queue.pop(0) + "\n"
                else:
                    user_input = prompt("", multiline=False) + "\n"

                # Send the input to the process
                os.write(master_fd, user_input.encode())

                # Check if it's a termination command (like 'exit', 'quit', etc.)
                if user_input.strip().lower() in ['exit', 'quit', 'logout', 'bye']:
                    time.sleep(0.5)  # Give the process time to exit
                    if self.active_process.poll() is not None:
                        self.should_continue = False
                        break
            except EOFError:
                # Ctrl+D
                self.should_continue = False
                break
            except KeyboardInterrupt:
                # Ctrl+C
                self.should_continue = False
                break
            except Exception as e:
                logging.error(f"Error processing input: {e}")
                break

    def run_interactive_command(self, command, initial_inputs=None):
        """
        Run an interactive command.

        Args:
            command (str): Command to execute
            initial_inputs (list): List of inputs to send to the process

        Returns:
            int: Exit code of the process
        """
        self.should_continue = True
        self.input_queue = initial_inputs or []

        try:
            # Create a pseudo-terminal
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd

            # Prepare display
            print_formatted_text(HTML(f"\n<prompt>Starting interactive session for:</prompt> <text>{command}</text>"))
            print_formatted_text(HTML("<prompt>Type input directly. Use Ctrl+C to exit</prompt>\n"))

            # Start the command
            self.active_process = os.spawnvp(
                os.P_NOWAIT,
                "/bin/sh",
                ["/bin/sh", "-c", command]
            )

            # Start reader thread
            reader_thread = threading.Thread(target=self._read_process_output, args=(master_fd,))
            reader_thread.daemon = True
            reader_thread.start()

            # Start input handler thread
            input_thread = threading.Thread(target=self._handle_user_input, args=(master_fd,))
            input_thread.daemon = True
            input_thread.start()

            # Wait for threads to finish
            while self.should_continue:
                # Check if process has exited
                if self.active_process is not None:
                    pid, status = os.waitpid(self.active_process, os.WNOHANG)
                    if pid != 0:
                        self.should_continue = False
                        break
                time.sleep(0.1)

            # Clean up
            reader_thread.join(timeout=1.0)
            input_thread.join(timeout=1.0)
            os.close(master_fd)

            # Get and return process status
            try:
                pid, status = os.waitpid(self.active_process, 0)
                exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                print_formatted_text(
                    HTML(f"\n<prompt>Interactive session ended with exit code:</prompt> <text>{exit_code}</text>\n"))
                return exit_code
            except Exception as e:
                logging.error(f"Error getting process status: {e}")
                return -1

        except Exception as e:
            logging.error(f"Error in interactive command: {e}")
            print_formatted_text(HTML(f"<ansired>Error running interactive command: {e}</ansired>"))
            return -1

    def detect_interactive_command(self, command):
        """
        Detect if a command is likely to be interactive.

        Args:
            command (str): Command to check

        Returns:
            bool: True if command is likely interactive
        """
        interactive_commands = [
            'vi', 'vim', 'nano', 'emacs', 'top', 'htop', 'less', 'more',
            'mysql', 'psql', 'sqlite3', 'python', 'ipython', 'node',
            'ssh', 'telnet', 'ftp', 'sftp', 'scp'
        ]

        # Check if the command starts with any of the interactive commands
        cmd_parts = command.split()
        if cmd_parts and any(cmd_parts[0].endswith(cmd) for cmd in interactive_commands):
            return True

        # Check for shell session start
        if 'bash' in command or 'zsh' in command or 'sh -c' in command or '/bin/sh' in command:
            return True

        return False


# Create a singleton instance
interactive_handler = InteractiveCommandHandler()


def run_interactive_command(command, initial_inputs=None):
    """
    Run an interactive command.

    Args:
        command (str): Command to execute
        initial_inputs (list): Optional list of inputs to send

    Returns:
        int: Exit code
    """
    return interactive_handler.run_interactive_command(command, initial_inputs)


def is_interactive_command(command):
    """
    Check if a command is likely to be interactive.

    Args:
        command (str): Command to check

    Returns:
        bool: True if likely interactive
    """
    return interactive_handler.detect_interactive_command(command)