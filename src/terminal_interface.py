import readline
from pynput import keyboard
from src.voice_interface import VoiceInterface
import os 

class TerminalInterface:
    def __init__(self, neo_ai, config):
        self.neo_ai = neo_ai
        self.config = config
        self.voice_interface = VoiceInterface(neo_ai, config)
        self.commands = ['reset', 'history', 'save', 'load', 'exit', 'quit', 'bye', 'voice']

    def completer(self, text, state):
        options = [i for i in self.commands if i.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None

    def run(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        print("\033[1;34mWelcome to Neo Terminal. Type 'exit' to quit or 'voice' to activate voice mode.\033[0m")
        while True:
            try:
                user_input = input("\033[1;32mYou:\033[0m ").strip()
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\033[1;31mNeo: Goodbye!\033[0m")
                    break
                elif user_input.lower() == 'reset':
                    self.neo_ai.reset_history()
                    print("\033[1;33mNeo: Session history has been reset.\033[0m")
                elif user_input.lower() == 'history':
                    print("\033[1;33mNeo: Displaying conversation history\033[0m")
                    self.display_history()
                elif user_input.lower().startswith('save'):
                    self.save_session(user_input)
                elif user_input.lower().startswith('load'):
                    self.load_session(user_input)
                elif user_input.lower() == 'voice':
                    print("\033[1;33mNeo: Activating voice mode. Please wait...\033[0m")
                    self.voice_interface.run()
                else:
                    response = self.neo_ai.query(user_input)
            except KeyboardInterrupt:
                print("\n\033[1;31mNeo: Interrupted. Goodbye!\033[0m")
                break
            except Exception as e:
                print(f"\033[1;31mAn error occurred: {str(e)}\033[0m")

    def display_history(self):
        for entry in self.neo_ai.get_conversation_history():
            role = "\033[1;32mYou:\033[0m" if entry["role"] == "user" else "\033[1;34mNeo:\033[0m"
            print(f"{role} {entry['content']}")

    def save_session(self, user_input):
        filename = user_input.split(' ')[1] if len(user_input.split(' ')) > 1 else 'neo_session.txt'
        with open(filename, 'w') as f:
            for entry in self.neo_ai.get_conversation_history():
                f.write(f"{entry['role']}: {entry['content']}\n")
        print(f"\033[1;33mNeo: Session saved to {filename}\033[0m")

    def load_session(self, user_input):
        filename = user_input.split(' ')[1] if len(user_input.split(' ')) > 1 else 'neo_session.txt'
        with open(filename, 'r') as f:
            self.neo_ai.reset_history()
            for line in f:
                role, content = line.split(': ', 1)
                self.neo_ai.history.append({"role": role.strip(), "content": content.strip()})
        print(f"\033[1;33mNeo: Session loaded from {filename}\033[0m")

    @staticmethod
    def integrate_with_bash():
        bashrc_path = os.path.expanduser("~/.bashrc")
        with open(bashrc_path, "a") as bashrc:
            bashrc.write("\n# Neo AI Integration\n")
            bashrc.write('alias neo="python /path/to/your/neo_ai/main.py"\n')
        print("Neo AI has been integrated with your bash terminal. Restart your terminal or run 'source ~/.bashrc' to apply changes.")
