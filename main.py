"""
Main entry point for Neo AI terminal assistant.
This file initializes the Neo AI core and UI components.
"""

import os
import sys
import yaml
import argparse
from src.ai_core import NeoAI
from src.terminal_interface import TerminalInterface

try:
    from src.terminal_ui import ImprovedTerminalUI
    IMPROVED_UI_AVAILABLE = True
except ImportError:
    IMPROVED_UI_AVAILABLE = False
    print("Note: Improved UI not available, defaulting to classic interface.")
    print("To install improved UI requirements: pip install prompt_toolkit pygments")

def load_config():
    """Load configuration from config.yaml file."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, 'config', 'config.yaml')

    if os.path.exists(config_path):
        with open(config_path, "r") as config_file:
            return yaml.safe_load(config_file)
    else:
        print("Error: The 'config.yaml' file is missing. Please ensure it exists in the 'config' directory.")
        sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Neo AI - Your Linux Terminal Assistant')
    parser.add_argument('--classic', action='store_true', help='Use classic terminal interface')
    parser.add_argument('--version', action='version', version='Neo AI v1.1.0')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main():
    """Main entry point for Neo AI."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Load configuration
        config = load_config()

        # Check for required keys in the configuration
        if 'api_url' not in config:
            raise KeyError("'api_url'")

        # Initialize NeoAI
        neo_ai = NeoAI(config)

        # Choose interface based on argument and availability
        if args.classic or not IMPROVED_UI_AVAILABLE:
            # Use classic terminal interface
            terminal = TerminalInterface(neo_ai, config)
        else:
            # Use improved terminal UI
            terminal = ImprovedTerminalUI(neo_ai, config)

        # Run the selected interface
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