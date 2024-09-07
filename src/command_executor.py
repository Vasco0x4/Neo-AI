import subprocess
import shlex

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
