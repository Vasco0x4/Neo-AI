import os
from src.ai_core import NeoAI
from src.terminal_interface import TerminalInterface
import yaml

def load_config():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, 'config', 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, "r") as config_file:
            return yaml.safe_load(config_file)
    else:
        return {}

def main():
    config = load_config()
    neo_ai = NeoAI(config)
    terminal = TerminalInterface(neo_ai, config)
    terminal.run()

if __name__ == "__main__":
    main()
