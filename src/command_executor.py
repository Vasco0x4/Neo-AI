"""
Enhanced command executor for Neo AI.
This module handles the execution of system commands with improved display and security.
"""

import subprocess
import shlex
import time
import os
import re
import logging
from prompt_toolkit import print_formatted_text, HTML
from src.command_display import CommandDisplay

# Initialize command display
display = CommandDisplay()

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
        logging.debug(f"Executing command: {command}")

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

def extract_system_commands(response):
    """
    Extract commands from <system> tags in the response.

    Args:
        response (str): Text containing commands in <system> tags

    Returns:
        list: List of extracted commands
    """
    commands = []

    # Try with <system> tags first (original format)
    system_pattern = re.compile(r'<system>(.*?)</system>', re.DOTALL)
    commands.extend(system_pattern.findall(response))

    # Also try with <s> tags (new format for better display)
    s_pattern = re.compile(r'<s>(.*?)</s>', re.DOTALL)
    commands.extend(s_pattern.findall(response))

    return [cmd.strip() for cmd in commands]

def execute_command_in_terminal(command):
    """
    Execute a command in an external terminal and save output to file.

    Args:
        command (str): Command to execute

    Returns:
        str: Path to the output file or None on failure
    """
    temp_file = "/tmp/neo_command_output.txt"

    # Display the command being executed
    display.print_command_execution(command)

    if os.path.exists(temp_file):
        os.remove(temp_file)

    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    try:
        if "gnome" in desktop_env or "unity" in desktop_env:
            # GNOME Terminal with minimal styling
            term_cmd = (
                f"gnome-terminal -- bash -c '"
                f"{command} 2>&1 | tee {temp_file}; "
                f"echo \"Done\" >> {temp_file}; exec bash'"
            )
            subprocess.Popen(term_cmd, shell=True)

        elif "kde" in desktop_env or "plasma" in desktop_env:
            # KDE Konsole with minimal styling
            term_cmd = (
                f"konsole --hold -e bash -c '"
                f"{command} 2>&1 | tee {temp_file}; "
                f"echo \"Done\" >> {temp_file}; exec bash'"
            )
            subprocess.Popen(term_cmd, shell=True)

        elif "xfce" in desktop_env:
            # XFCE Terminal
            term_cmd = (
                f"xfce4-terminal --hold -e 'bash -c \""
                f"{command} 2>&1 | tee {temp_file}; "
                f"echo \"Done\" >> {temp_file}; exec bash\"'"
            )
            subprocess.Popen(term_cmd, shell=True)

        else:
            # Fallback to more basic terminal
            term_cmd = f"x-terminal-emulator -e 'bash -c \"{command} | tee {temp_file}; echo Done >> {temp_file}; exec bash\"'"
            subprocess.Popen(term_cmd, shell=True)

        return temp_file
    except FileNotFoundError:
        print_formatted_text(HTML("<e>Error: External terminal not found.</e>"))
        # Fallback to direct execution
        try:
            result = execute_command(command)
            with open(temp_file, "w") as f:
                f.write(result)
                f.write("\nDone")
            return temp_file
        except Exception as e:
            print_formatted_text(HTML(f"<e>Error executing command: {e}</e>"))
            return None
    except Exception as e:
        print_formatted_text(HTML(f"<e>Error: {e}</e>"))
        return None


def wait_for_command_completion(temp_file):
    """
    Wait for a command to complete and read its output.

    Args:
        temp_file (str): Path to the output file

    Returns:
        str: Command output
    """
    start_time = time.time()
    notified_long_execution = False
    animation_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    frame_index = 0

    while True:
        if os.path.exists(temp_file):
            with open(temp_file, "r") as f:
                content = f.read()
                if "Done" in content:
                    # No message needed - let the output speak for itself
                    return content.replace("Done", "").strip()

        elapsed_time = time.time() - start_time

        if elapsed_time > 60 and not notified_long_execution:
            print(f"\r⏳ Command taking longer than expected... ({int(elapsed_time)}s)", end="")
            notified_long_execution = True

        # Every 0.2 seconds, update the animation
        if int(elapsed_time * 5) % len(animation_frames) != frame_index:
            frame_index = int(elapsed_time * 5) % len(animation_frames)
            # Clear the line and print the new frame - keep it minimal
            print(f"\r{animation_frames[frame_index]} {int(elapsed_time)}s", end="")

        time.sleep(0.1)