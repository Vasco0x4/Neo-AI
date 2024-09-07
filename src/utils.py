import re
import os

def load_persistent_memory():
    memory_file = "/tmp/persistent_memory.txt"
    if not os.path.exists(memory_file):
        print("Persistent memory not found. Creating...")
        with open(memory_file, "w") as f:
            f.write(f"Kernel Version: {os.uname().release}\n")
            f.write(f"OS Info: {os.uname().sysname}\n")
            f.write(f"Architecture: {os.uname().machine}\n")
            f.write(f"Hostname: {os.uname().nodename}\n")
        print("Persistent memory created.")
    
    with open(memory_file, "r") as f:
        return f.read()


def parse_hooks(text):
  pattern = r'<(\w+)>(.*?)</\1>'
  return re.findall(pattern, text, re.DOTALL)


