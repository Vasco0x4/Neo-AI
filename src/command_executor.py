import subprocess
import shlex
import subprocess
import time
import os

def execute_command(command):
    try:
        if any(char in command for char in ['|', '>', '<', '&']):
            result = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=30)
        else:
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def extract_system_commands(response):
    commands = []
    while "<system>" in response and "</system>" in response:
        start = response.index("<system>") + len("<system>")
        end = response.index("</system>")
        command = response[start:end].strip()
        commands.append(command)
        response = response[end + len("</system>"):]
    return commands


def execute_command_in_terminal(command):
    temp_file = "/tmp/neo_command_output.txt"

    if os.path.exists(temp_file):
        os.remove(temp_file)

    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    try:
        if "gnome" in desktop_env or "unity" in desktop_env:
            # GNOME Terminal
            subprocess.Popen(
                ["gnome-terminal", "--", "bash", "-c", f"{command} | tee {temp_file}; echo Done >> {temp_file}; exec bash"]
            )
        elif "kde" in desktop_env or "plasma" in desktop_env:
            # KDE Konsole
            subprocess.Popen(
                ["konsole", "--hold", "-e", f"bash -c \"{command} | tee {temp_file}; echo Done >> {temp_file}; exec bash\""]
            )
        else:
            print("Error: Unsupported desktop environment.")
            return None

        return temp_file
    except FileNotFoundError:
        print("Error: External terminal not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def wait_for_command_completion(temp_file):
    start_time = time.time()
    notified_long_execution = False

    while True:
        if os.path.exists(temp_file):
            with open(temp_file, "r") as f:
                content = f.read()
                if "Done" in content:
                    return content.replace("Done", "").strip()

        if not notified_long_execution and time.time() - start_time > 30:
            print("\033[1;33m[System]\033[0m Command is taking longer than expected. Please wait...")
            notified_long_execution = True

        time.sleep(1)
