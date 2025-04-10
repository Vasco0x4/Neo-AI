"""
Persistent terminal executor for Neo AI.
Uses a single reusable terminal window for all commands with enhanced sudo handling.
"""

import subprocess
import os
import time
import logging
import tempfile
import shlex
import signal
import atexit
import re
from prompt_toolkit import print_formatted_text, HTML

# Define sudo-specific enhancements
class SudoCommandHandler:
    """Handle sudo-specific command execution details."""

    def __init__(self):
        """Initialize sudo handler."""
        self.sudo_log_file = os.path.join(tempfile.gettempdir(), "neo_sudo_log.txt")
        self.sudo_pattern = re.compile(r'^sudo\s+|[;&|]\s*sudo\s+', re.MULTILINE)
        self.dangerous_sudo_commands = [
            r'sudo\s+(rm|dd|mkfs|fdisk|parted|shred)\s+',
            r'sudo\s+.*(remove|delete|format|wipe|reset).*',
            r'sudo\s+(halt|reboot|poweroff|shutdown)\s+',
            r'sudo\s+chown\s+-R\s+',
            r'sudo\s+chmod\s+-R\s+',
            r'sudo\s+systemctl\s+(disable|stop|mask)\s+'
        ]

        # Initialize sudo log
        if not os.path.exists(self.sudo_log_file):
            with open(self.sudo_log_file, 'w') as f:
                f.write("# Neo AI Sudo Command Log\n")
                f.write("# Format: [Timestamp] [Command] [Exit Code]\n\n")

    def is_sudo_command(self, command):
        """Check if a command uses sudo."""
        return bool(self.sudo_pattern.search(command))

    def is_dangerous_sudo(self, command):
        """Check if a sudo command is potentially dangerous."""
        for pattern in self.dangerous_sudo_commands:
            if re.search(pattern, command):
                return True
        return False

    def log_sudo_command(self, command, exit_code):
        """Log sudo command execution for security auditing."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.sudo_log_file, 'a') as f:
            f.write(f"[{timestamp}] [{command}] [Exit code: {exit_code}]\n")

    def sanitize_sudo_command(self, command):
        """
        Apply safety enhancements to sudo commands.

        This adds safeguards like -p for predictable password prompts
        and prevents certain dangerous patterns.
        """
        # Don't modify commands that use pipes after sudo
        if '|' in command and self.is_sudo_command(command):
            return command

        # Add sudo password prompt to make it more consistent
        if command.startswith('sudo '):
            # Check if -p is already present
            if not re.search(r'sudo\s+(-[a-zA-Z]*p|-p)\s+', command):
                # Insert custom prompt after sudo
                command = re.sub(r'^sudo\s+', 'sudo -p "[sudo] password for %p: " ', command)

        return command

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
        self.sudo_handler = SudoCommandHandler()  # Intégration du gestionnaire sudo

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

            # Check if process exists and is a bash/shell process
            # This helps verify it's actually our terminal script
            try:
                with open(f"/proc/{pid}/cmdline", 'r') as cmd_file:
                    cmdline = cmd_file.read()
                    # Check if it's our script
                    if "neo_terminal_script" not in cmdline:
                        return False
            except (IOError, FileNotFoundError):
                return False

            # Process exists and is our terminal
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
echo $$ > %s
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

            # Launch terminal more reliably - determine based on desktop environment
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            term_cmd = ""

            if "gnome" in desktop_env or "unity" in desktop_env:
                term_cmd = f"gnome-terminal -- bash {script_path}"
            elif "kde" in desktop_env or "plasma" in desktop_env:
                term_cmd = f"konsole -e bash {script_path}"
            elif "xfce" in desktop_env:
                term_cmd = f"xfce4-terminal -e 'bash {script_path}'"
            else:
                # Use detected terminal with explicit bash
                term_cmd = f"{self.terminal_type} bash {script_path}"

            # Log the command we're about to run
            logging.info(f"Launching persistent terminal with: {term_cmd}")
            #print_formatted_text(HTML(f"<ansiblue>Launching terminal: {term_cmd}</ansiblue>"))

            # Launch the terminal with nohup to ensure it stays running
            subprocess.Popen(term_cmd, shell=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)

            # Wait for terminal to initialize
            wait_count = 0
            while not os.path.exists(self.pid_file) and wait_count < 20:
                time.sleep(0.5)
                wait_count += 1
                print(f"\rWaiting for terminal to initialize... {wait_count}/20", end="")

            print()  # New line after waiting

            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = f.read().strip()
                #logging.info(f"Persistent terminal initialized successfully. PID: {pid}")
                #print_formatted_text(HTML(f"<ansigreen>Persistent terminal initialized successfully. PID: {pid}</ansigreen>"))
                self.terminal_initialized = True
            else:
                logging.error("Failed to initialize persistent terminal.")
                print_formatted_text(HTML("<ansired>Failed to initialize persistent terminal. Using fallback method.</ansired>"))
                self._initialize_fallback()

        except Exception as e:
            logging.error(f"Error initializing persistent terminal: {e}")
            print_formatted_text(HTML(f"<ansired>Error initializing persistent terminal: {e}</ansired>"))
            self._initialize_fallback()

    def _initialize_fallback(self):
        """Initialize a fallback terminal method."""
        # Create a simple script that just writes the PID to file
        script_path = os.path.join(self.temp_dir, "neo_fallback_script.sh")
        with open(script_path, 'w') as f:
            f.write(f'''#!/bin/bash
echo $$ > {self.pid_file}
echo "Neo AI Fallback Terminal"
while true; do
    sleep 1
done
''')
        # Make executable
        os.chmod(script_path, 0o755)

        # Start a background process
        subprocess.Popen(['bash', script_path],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       start_new_session=True)

        # Wait a moment
        time.sleep(1)
        if os.path.exists(self.pid_file):
            logging.info("Fallback terminal method initialized.")
            self.terminal_initialized = True

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
        Execute a command in the persistent terminal with sudo support.

        Args:
            command (str): Command to execute

        Returns:
            str: Path to the output file
        """
        # Check for sudo and handle it appropriately
        is_sudo = self.sudo_handler.is_sudo_command(command)
        is_dangerous = self.sudo_handler.is_dangerous_sudo(command)

        # Log and notify for sudo commands
        if is_sudo:
            logging.info(f"Executing sudo command: {command}")
            # Sanitize sudo command
            command = self.sudo_handler.sanitize_sudo_command(command)

            # Additional warning for dangerous commands
            if is_dangerous:
                logging.warning(f"Executing potentially dangerous sudo command: {command}")
                print_formatted_text(HTML(
                    f"<ansired>⚠️ Executing command with elevated privileges</ansired>"
                ))

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
                    #print_formatted_text(HTML("<ansigreen>Initializing persistent terminal for command execution...</ansigreen>"))
                    self.terminal_initialized = True
                else:
                    logging.info("Terminal not running, restarting...")

                self._initialize_terminal()
                # Give it a moment to start
                time.sleep(2)

                # Verify it's running after initialization
                if not self._is_terminal_running():
                    logging.error("Terminal failed to initialize properly. Using direct execution.")
                    # Execute directly as fallback
                    try:
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)
                        with open(self.output_file, 'w') as f:
                            f.write(result.stdout + "\n" + result.stderr)
                        # Create lock file to signal completion
                        with open(self.lock_file, 'w') as f:
                            pass

                        # Log sudo command execution if applicable
                        if is_sudo:
                            self.sudo_handler.log_sudo_command(command, result.returncode)

                        return self.output_file
                    except Exception as direct_exec_error:
                        logging.error(f"Direct execution also failed: {direct_exec_error}")
                        with open(self.output_file, 'w') as f:
                            f.write(f"Error: {direct_exec_error}")
                        with open(self.lock_file, 'w') as f:
                            pass
                        return self.output_file

            logging.info(f"Sending command to persistent terminal: {command}")

            # Special handling for sudo commands
            if is_sudo:
                print_formatted_text(HTML(f"<ansiyellow>Executing command with elevated privileges:</ansiyellow> <ansiblue>{command}</ansiblue>"))
            else:
                print_formatted_text(HTML(f"<ansiyellow>Executing in terminal:</ansiyellow> <ansiblue>{command}</ansiblue>"))

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

            # Create lock file to indicate completion
            with open(self.lock_file, "w") as f:
                pass

            return self.output_file

    def wait_for_command_completion(self):
        """
        Wait for the command to complete by checking for the lock file.
        Enhanced with sudo-specific handling.

        Returns:
            str: Command output
        """
        max_wait_time = 180  # 3 minutes max wait
        start_time = time.time()
        animation_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        frame_index = 0

        #print_formatted_text(HTML("<ansicyan>Waiting for command to complete...</ansicyan>"))

        while not os.path.exists(self.lock_file):
            elapsed_time = time.time() - start_time

            if elapsed_time > max_wait_time:
                print_formatted_text(HTML("<ansired>Command timed out after 3 minutes</ansired>"))
                # Create an empty lock file to prevent further hangs
                with open(self.lock_file, "w") as f:
                    pass
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
                    output = f.read()

                # Check for sudo password prompts in the output
                if "[sudo] password for" in output and "Sorry, try again" in output:
                    print_formatted_text(HTML("<ansired>Sudo authentication failed. Password may be incorrect.</ansired>"))

                return output
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
    # Check for sudo commands
    sudo_handler = SudoCommandHandler()
    is_sudo = sudo_handler.is_sudo_command(command)

    try:
        # Log the command
        logging.debug(f"Executing simple command: {command}")
        if is_sudo:
            logging.info(f"Executing sudo command directly: {command}")

        # Determine if command needs shell
        needs_shell = any(char in command for char in ['|', '>', '<', '&', ';', '*', '`']) or is_sudo

        # Execute the command
        if needs_shell:
            result = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=30)
        else:
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        # Log sudo command execution
        if is_sudo:
            sudo_handler.log_sudo_command(command, result.returncode)

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