import os
import sys
import yaml
from src.ai_core import NeoAI
from src.terminal_interface import TerminalInterface

def load_config():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, 'config', 'config.yaml')

    if os.path.exists(config_path):
        with open(config_path, "r") as config_file:
            return yaml.safe_load(config_file)
    else:
        print("Error: The 'config.yaml' file is missing. Please ensure it exists in the 'config' directory.")
        sys.exit(1)

def main():
    try:
        # Load configuration
        config = load_config()

        # Check for required keys in the configuration
        if 'api_url' not in config:
            raise KeyError("'api_url'")

        # Initialize NeoAI and TerminalInterface
        neo_ai = NeoAI(config)
        terminal = TerminalInterface(neo_ai, config)
        terminal.run()

    except KeyError as e:
        if str(e) == "'api_url'":
            print("Error: The key 'api_url' is missing in the 'config.yaml' file.")
            print("Please ensure that the 'config.yaml' file is properly configured with all required fields.")
        else:
            print(f"Error: Missing configuration key: {e}. Please check your 'config.yaml' file.")
        sys.exit(1)

    except FileNotFoundError:
        print("Error: The 'config.yaml' file is missing.")
        sys.exit(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

