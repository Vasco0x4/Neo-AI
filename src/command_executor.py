"""
Improved external terminal executor for Neo AI.
Uses a more reliable approach with better terminal detection and output capture.
"""

import subprocess
import os
import time
import logging
import tempfile
import shlex
from prompt_toolkit import print_formatted_text, HTML

class ExternalTerminalExecutor:
    """Execute commands in an external terminal with improved reliability."""

    def __init__(self):
        """Initialize the terminal executor."""
        self.temp_dir = tempfile.gettempdir()
        self.output_file = os.path.join(self.temp_dir, "neo_command_output.txt")
        self.lock_file = os.path.join(self.temp_dir, "neo_command_lock")
        self.terminal_type = self._detect_terminal_type()

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=os.path.join(self.temp_dir, "neo_command.log"),
            filemode='a'
        )

    def _detect_terminal_type(self):
        """Detect the available terminal emulator."""
        terminals = [
            ("gnome-terminal", "gnome-terminal --"),
            ("konsole", "konsole --hold -e"),
            ("xfce4-terminal", "xfce4-terminal --hold -e"),
            ("mate-terminal", "mate-terminal --"),
            ("terminator", "terminator -e"),
            ("tilix", "tilix -e"),
            ("kitty", "kitty --hold -e"),
            ("alacritty", "alacritty -e"),
            ("x-terminal-emulator", "x-terminal-emulator -e")
        ]

        for terminal_cmd, launch_cmd in terminals:
            try:
                subprocess.run(["which", terminal_cmd],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              check=False)
                return launch_cmd
            except Exception:
                continue

        # Default fallback
        return "x-terminal-emulator -e"

    def execute_command(self, command):
        """
        Execute a command in an external terminal.

        Args:
            command (str): Command to execute

        Returns:
            str: Path to the output file
        """
        # Clean up any existing output and lock files
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

        try:
            logging.info(f"Executing command in external terminal: {command}")
            print_formatted_text(HTML(f"<ansiyellow>Executing in external terminal:</ansiyellow> <ansiblue>{command}</ansiblue>"))

            # Create the wrapper script that will capture output
            script_path = os.path.join(self.temp_dir, "neo_cmd_script.sh")
            with open(script_path, "w") as f:
                f.write(f"""#!/bin/bash
echo "Executing: {command}"
echo "----------------------------------------"
# Execute the command and capture output
{command} 2>&1 | tee "{self.output_file}"
EXIT_CODE=${{PIPESTATUS[0]}}
echo "----------------------------------------"
echo "Command completed with exit code: $EXIT_CODE" | tee -a "{self.output_file}"
echo "Press Enter to close this terminal..." | tee -a "{self.output_file}"
# Create a lock file to indicate completion
touch "{self.lock_file}"
read
""")

            # Make the script executable
            os.chmod(script_path, 0o755)

            # Determine terminal command based on desktop environment
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

            if "gnome" in desktop_env or "unity" in desktop_env:
                term_cmd = f"gnome-terminal -- {script_path}"
            elif "kde" in desktop_env or "plasma" in desktop_env:
                term_cmd = f"konsole --hold -e {script_path}"
            elif "xfce" in desktop_env:
                term_cmd = f"xfce4-terminal --hold -e {script_path}"
            else:
                # Use detected terminal
                term_cmd = f"{self.terminal_type} {script_path}"

            # Launch the terminal
            subprocess.Popen(term_cmd, shell=True)

            # Return the output file path
            return self.output_file

        except Exception as e:
            logging.error(f"Error executing command in external terminal: {str(e)}")

            # Create error output
            with open(self.output_file, "w") as f:
                f.write(f"Error executing command in external terminal: {str(e)}\n")

            return self.output_file

    def wait_for_command_completion(self):
        """
        Wait for the command to complete by checking for the lock file.

        Returns:
            str: Command output
        """
        max_wait_time = 180  # 3 minutes max wait
        start_time = time.time()
        animation_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        frame_index = 0

        print_formatted_text(HTML("<ansicyan>Waiting for command to complete...</ansicyan>"))

        while not os.path.exists(self.lock_file):
            elapsed_time = time.time() - start_time

            if elapsed_time > max_wait_time:
                print_formatted_text(HTML("<ansired>Command timed out after 3 minutes</ansired>"))
                break

            # Every 0.2 seconds, update the animation
            if int(elapsed_time * 5) % len(animation_frames) != frame_index:
                frame_index = int(elapsed_time * 5) % len(animation_frames)
                print(f"\r{animation_frames[frame_index]} Waiting for command to complete... ({int(elapsed_time)}s)", end="")

            time.sleep(0.1)

        print()  # New line after waiting animation

        # Read the output file
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, "r") as f:
                    return f.read()
            else:
                return "No output was captured. The command may have failed to execute properly."
        except Exception as e:
            return f"Error reading command output: {str(e)}"

# Function for simple command execution (without terminal)
def execute_command(command):
    """
    Execute a command and return its output.

    Args:
        command (str): Command to execute

    Returns:
        str: Command output or error message
    """
    try:
        # Log the command
        logging.debug(f"Executing simple command: {command}")

        # Determine if command needs shell
        needs_shell = any(char in command for char in ['|', '>', '<', '&', ';', '*', '`'])

        # Execute the command
        if needs_shell:
            result = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=30)
        else:
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        # Return the result
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: Command failed with exit code {result.returncode}\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out after 30 seconds"
    except FileNotFoundError:
        return f"Error: Command not found: {command.split()[0]}"
    except PermissionError:
        return f"Error: Permission denied when executing: {command}"
    except Exception as e:
        return f"Error: {str(e)}"

# Create a singleton instance
terminal_executor = ExternalTerminalExecutor()

def execute_command_in_terminal(command):
    """
    Execute a command in an external terminal.

    Args:
        command (str): Command to execute

    Returns:
        str: Path to the output file
    """
    return terminal_executor.execute_command(command)

def wait_for_command_completion(temp_file):
    """
    Wait for a command to complete and read its output.

    Args:
        temp_file (str): Path to the output file

    Returns:
        str: Command output
    """
    return terminal_executor.wait_for_command_completion()