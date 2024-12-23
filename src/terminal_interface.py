import readline

class TerminalInterface:
    def __init__(self, neo_ai, config):
        self.neo_ai = neo_ai
        self.config = config
        self.commands = ['history','exit']

    def completer(self, text, state):
        options = [i for i in self.commands if i.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None

    def run(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        print("\033[1;34mWelcome to Neo Terminal.\033[0m")
        while True:
            try:
                user_input = input("\033[1;32mYou:\033[0m ").strip()
                if user_input.lower() in ['exit']:
                    print("\033[1;31mGoodbye!\033[0m")
                    break
                elif user_input.lower() == 'history':
                    print("\033[1;33mDisplaying conversation history\033[0m")
                    self.display_history()
                else:
                    self.neo_ai.query(user_input)
            except KeyboardInterrupt:
                print("\n\033[1;31mInterrupted. Goodbye!\033[0m")
                break
            except Exception as e:
                print(f"\033[1;31mAn error occurred: {str(e)}\033[0m")

    def display_history(self):
        for entry in self.neo_ai.get_conversation_history():
            role = "\033[1;32mYou:\033[0m" if entry["role"] == "user" else "\033[1;34mNeo:\033[0m"
            print(f"{role} {entry['content']}")