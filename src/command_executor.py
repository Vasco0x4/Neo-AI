"""
Persistent terminal executor for Neo AI.
Uses a single reusable terminal window for all commands.
"""

import subprocess
import os
import time
import logging
import tempfile
import shlex
import signal
import atexit
from prompt_toolkit import print_formatted_text, HTML

class PersistentTerminalExecutor:
    """Execute commands using a single persistent terminal window."""

    def __init__(self):
        """Initialize the persistent terminal executor."""
        self.temp_dir = tempfile.gettempdir()
        self.output_file = os.path.join(self.temp_dir, "neo_command_output.txt")
        self.lock_file = os.path.join(self.temp_dir, "neo_command_lock")
        self.pid_file = os.path.join(self.temp_dir, "neo_terminal_pid.txt")
        self.fifo_path = os.path.join(self.temp_dir, "neo_terminal_fifo")
        self.terminal_type = self._detect_terminal_type()
        self.terminal_process = None
        self.terminal_initialized = False

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=os.path.join(self.temp_dir, "neo_command.log"),
            filemode='a'
        )

        # Create FIFO if it doesn't exist
        if not os.path.exists(self.fifo_path):
            try:
                os.mkfifo(self.fifo_path)
            except Exception as e:
                logging.error(f"Failed to create FIFO: {e}")

        # Check if there's an existing terminal running
        if self._is_terminal_running():
            self.terminal_initialized = True
            logging.info("Found an existing Neo terminal session, will reuse it.")

        # Register cleanup on exit
        atexit.register(self._cleanup)

    def _detect_terminal_type(self):
        """Detect the available terminal emulator."""
        terminals = [
            ("gnome-terminal", "gnome-terminal --"),
            ("konsole", "konsole -e"),
            ("xfce4-terminal", "xfce4-terminal -e"),
            ("mate-terminal", "mate-terminal -e"),
            ("terminator", "terminator -e"),
            ("tilix", "tilix -e"),
            ("kitty", "kitty -e"),
            ("alacritty", "alacritty -e"),
            ("x-terminal-emulator", "x-terminal-emulator -e")
        ]

        for terminal_cmd, launch_cmd in terminals:
            try:
                result = subprocess.run(["which", terminal_cmd],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       check=False)
                if result.returncode == 0:
                    return launch_cmd
            except Exception:
                continue

        # Default fallback
        return "x-terminal-emulator -e"

    def _is_terminal_running(self):
        """Check if the terminal process is still running."""
        if not os.path.exists(self.pid_file):
            return False

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists
            os.kill(pid, 0)
            return True
        except (OSError, ValueError, ProcessLookupError):
            # Process doesn't exist or invalid PID
            return False

    def _initialize_terminal(self):
        """Initialize the persistent terminal if not already running."""
        if self._is_terminal_running():
            logging.info("Persistent terminal is already running.")
            return

        try:
            # Create the terminal script
            script_path = os.path.join(self.temp_dir, "neo_terminal_script.sh")
            with open(script_path, 'w') as f:
                f.write('''#!/bin/bash
echo "$" > %s
echo "Neo AI Terminal - DO NOT CLOSE THIS WINDOW"
echo "This terminal will be used for all Neo AI commands."
echo "---------------------------------------------------"

# Function to handle commands
process_command() {
    # Read command from FIFO
    command=$(cat %s)
    
    # Create lock file to indicate we're running a command
    rm -f %s
    
    # Display command
    echo ""
    echo "---------------------------------------------------"
    echo "Executing: $command"
    echo "---------------------------------------------------"
    
    # Execute the command and capture output
    eval "$command" 2>&1 | tee %s
    EXIT_CODE=${PIPESTATUS[0]}
    
    # Add exit code to output
    echo "" >> %s
    echo "---------------------------------------------------" >> %s
    echo "Command completed with exit code: $EXIT_CODE" >> %s
    
    # Create lock file to indicate completion
    touch %s
    
    echo "---------------------------------------------------"
    echo "Command completed. Waiting for next command..."
    echo "---------------------------------------------------"
}

# Main loop - keep reading commands
while true; do
    if [ -e %s ]; then
        process_command
    else
        sleep 0.5
    fi
done
''' % (self.pid_file, self.fifo_path, self.lock_file,
       self.output_file, self.output_file, self.output_file,
       self.output_file, self.lock_file, self.fifo_path))

            # Make script executable
            os.chmod(script_path, 0o755)

            # Determine terminal command based on desktop environment
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

            if "gnome" in desktop_env or "unity" in desktop_env:
                term_cmd = f"gnome-terminal -- {script_path}"
            elif "kde" in desktop_env or "plasma" in desktop_env:
                term_cmd = f"konsole -e {script_path}"
            elif "xfce" in desktop_env:
                term_cmd = f"xfce4-terminal -e {script_path}"
            else:
                # Use detected terminal
                term_cmd = f"{self.terminal_type} {script_path}"

            # Launch the terminal
            logging.info(f"Launching persistent terminal: {term_cmd}")
            self.terminal_process = subprocess.Popen(term_cmd, shell=True)

            # Wait for terminal to initialize
            wait_count = 0
            while not os.path.exists(self.pid_file) and wait_count < 10:
                time.sleep(0.5)
                wait_count += 1

            if os.path.exists(self.pid_file):
                logging.info("Persistent terminal initialized successfully.")
                print_formatted_text(HTML("<ansigreen>Persistent terminal initialized successfully.</ansigreen>"))
            else:
                logging.error("Failed to initialize persistent terminal.")
                print_formatted_text(HTML("<ansired>Failed to initialize persistent terminal. Falling back to new terminals.</ansired>"))

        except Exception as e:
            logging.error(f"Error initializing persistent terminal: {e}")
            print_formatted_text(HTML(f"<ansired>Error initializing persistent terminal: {e}</ansired>"))

    def _cleanup(self):
        """Clean up resources on exit."""
        try:
            # Remove FIFO
            if os.path.exists(self.fifo_path):
                os.unlink(self.fifo_path)

            # Terminal will auto-close when its script exits
            if os.path.exists(self.pid_file):
                try:
                    with open(self.pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
                os.unlink(self.pid_file)
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def execute_command(self, command):
        """
        Execute a command in the persistent terminal.

        Args:
            command (str): Command to execute

        Returns:
            str: Path to the output file
        """
        # Remove any existing lock file
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)

        # Clear the output file
        with open(self.output_file, 'w') as f:
            f.write("")

        try:
            # Make sure terminal is running - lazy initialization
            if not self._is_terminal_running():
                if not self.terminal_initialized:
                    logging.info("First command detected, initializing terminal...")
                    print_formatted_text(HTML("<ansigreen>Initializing persistent terminal for command execution...</ansigreen>"))
                    self.terminal_initialized = True
                else:
                    logging.info("Terminal not running, restarting...")

                self._initialize_terminal()
                # Give it a moment to start
                time.sleep(1)

            logging.info(f"Sending command to persistent terminal: {command}")
            print_formatted_text(HTML(f"<ansiyellow>Executing in persistent terminal:</ansiyellow> <ansiblue>{command}</ansiblue>"))

            # Send command to terminal via FIFO
            with open(self.fifo_path, 'w') as f:
                f.write(command)

            # Return the output file path
            return self.output_file

        except Exception as e:
            logging.error(f"Error sending command to persistent terminal: {e}")
            print_formatted_text(HTML(f"<ansired>Error: {e}</ansired>"))

            # Create error output
            with open(self.output_file, "w") as f:
                f.write(f"Error executing command: {e}\n")

            # If terminal fails, try to restart it
            self._initialize_terminal()

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
terminal_executor = PersistentTerminalExecutor()

def execute_command_in_terminal(command):
    """
    Execute a command in the persistent terminal.

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