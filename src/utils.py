import re
import os
from src.mcp_protocol import mcp  # Import the MCP singleton


def load_persistent_memory():
    """
    Load persistent memory from file.
    Creates a new file with system information if it doesn't exist.

    Returns:
        str: Contents of persistent memory
    """
    memory_file = "/tmp/persistent_memory.txt"
    if not os.path.exists(memory_file):
        # Creating persistent memory file with system information
        with open(memory_file, "w") as f:
            f.write(f"Kernel Version: {os.uname().release}\n")
            f.write(f"OS Info: {os.uname().sysname}\n")
            f.write(f"Architecture: {os.uname().machine}\n")
            f.write(f"Hostname: {os.uname().nodename}\n")
            f.write(f"User: {os.getlogin()}\n")

    with open(memory_file, "r") as f:
        return f.read()


def parse_hooks(text):
    """
    Parse hooks like <mcp:protocol> tags and legacy <system> or <s> tags in text.
    This function utilizes the MCP singleton for parsing tags.

    Args:
        text (str): Text to parse for tags

    Returns:
        list: List of tuples (protocol, content)
    """
    # Use the MCP protocol parser to handle all tags
    mcp_tags = mcp.parse_mcp_tags(text)
    return mcp_tags


def extract_context_tags(text):
    """
    Extract content from <context> tags in the text.

    Args:
        text (str): Text to search for context tags

    Returns:
        str: Content within context tags or empty string if not found
    """
    context_pattern = re.compile(r'<context>(.*?)</context>', re.DOTALL)
    match = context_pattern.search(text)

    if match:
        return match.group(1).strip()
    return ""


def format_output_for_display(output, max_lines=20, max_line_length=80):
    """
    Format command output for display, truncating if necessary.

    Args:
        output (str): Command output to format
        max_lines (int): Maximum number of lines to display
        max_line_length (int): Maximum length of each line

    Returns:
        str: Formatted output
    """
    lines = output.split('\n')

    # Truncate number of lines if necessary
    if len(lines) > max_lines:
        half = max_lines // 2
        lines = lines[:half] + ['...', f'[Output truncated: {len(lines) - max_lines} more lines]'] + lines[-half:]

    # Truncate line length if necessary
    formatted_lines = []
    for line in lines:
        if len(line) > max_line_length:
            formatted_lines.append(line[:max_line_length] + '...')
        else:
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)


def save_to_persistent_memory(key, value):
    """
    Save a key-value pair to persistent memory.

    Args:
        key (str): Key to store
        value (str): Value to store

    Returns:
        bool: True if successful
    """
    memory_file = "/tmp/persistent_memory.txt"

    try:
        # Read existing content
        with open(memory_file, "r") as f:
            content = f.readlines()

        # Check if key already exists
        key_exists = False
        for i, line in enumerate(content):
            if line.startswith(f"{key}:"):
                content[i] = f"{key}: {value}\n"
                key_exists = True
                break

        # Append if key doesn't exist
        if not key_exists:
            content.append(f"{key}: {value}\n")

        # Write back to file
        with open(memory_file, "w") as f:
            f.writelines(content)

        return True
    except Exception as e:
        print(f"Error saving to persistent memory: {str(e)}")
        return False


def get_from_persistent_memory(key):
    """
    Get a value from persistent memory by key.

    Args:
        key (str): Key to retrieve

    Returns:
        str: Value if found, None otherwise
    """
    memory_file = "/tmp/persistent_memory.txt"

    try:
        if not os.path.exists(memory_file):
            return None

        with open(memory_file, "r") as f:
            for line in f:
                if line.startswith(f"{key}:"):
                    return line.split(":", 1)[1].strip()

        return None
    except Exception as e:
        print(f"Error reading from persistent memory: {str(e)}")
        return None