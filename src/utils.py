import re
import os


def load_persistent_memory():
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
    """Parse hooks like <system> or <s> tags in text."""
    # Support both <system> and <s> tags
    patterns = [
        r'<(\w+)>(.*?)</\1>',  # Generic pattern for all tags
    ]

    hooks = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            # If it's a system or s tag, consider it as a system command
            tag_type, content = match
            if tag_type in ["system", "s"]:
                hooks.append(("s", content.strip()))
            else:
                hooks.append((tag_type, content.strip()))

    return hooks