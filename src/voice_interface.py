import yaml
import speech_recognition as sr
import os
import threading
import time

class VoiceInterface:
    def __init__(self, neo_ai, config):
        self.config = config
        
        # Load microphone configurations
        self.microphone_index = self.get_config_value('microphone.index')
        self.language = self.get_config_value('microphone.language')

        self.neo_ai = neo_ai
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.stop_listening_flag = threading.Event()
        self.cli_mode = False
        self.setup_environment()

        # Check if microphone index is valid
        if not self.validate_microphone_index():
            self.display_system_message(f"Invalid or unconfigured microphone index: {self.microphone_index}.", "error")
            return

    def get_config_value(self, key):
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            raise KeyError(f"Configuration key '{key}' is missing in config.yaml.")

    def validate_microphone_index(self):
        # Validate if the microphone index exists
        try:
            sr.Microphone(device_index=self.microphone_index)
            return True
        except OSError:
            return False

    def setup_environment(self):
        # Suppress warnings and redirect errors to devnull
        os.environ["PYTHONWARNINGS"] = "ignore"
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)

    def show_ascii_banner(self):
        banner = """
        NEO AI - Your Personal Assistant
        """
        print(f"\033[1;34m{banner}\033[0m")
        print("=" * 50)


    def display_animation(self):
        animation_frames = ['|', '/', '-', '\\']
        for frame in animation_frames:
            print(f"\r\033[1;33mListening {frame}\033[0m", end='', flush=True)
            time.sleep(0.1)
        print("\r\033[1;33mProcessing...\033[0m", end='', flush=True)

    def listen_in_background(self):
        self.is_listening = True
        threading.Thread(target=self._background_listen).start()

    def _background_listen(self):
        self.show_ascii_banner() 
        self.display_history()

        while not self.stop_listening_flag.is_set():
            if self.cli_mode:
                self.handle_cli_in_voice_mode()
            else:
                command = self.listen()
                if command:
                    if command.lower() in ['switch to cli', 'return to cli', 'text mode']:
                        self.cli_mode = True
                        self.stop_listening_flag.set()
                        print("\n\033[1;33mSwitching to CLI mode...\033[0m")
                        break
                    response = self.neo_ai.query(command)
                    self.display_response(response)
                if command and command.lower() in ['exit', 'quit', 'bye', 'stop']:
                    self.stop_listening_flag.set()
                    break

    def handle_cli_in_voice_mode(self):
        try:
            user_input = input("\033[1;32mYou (voice mode CLI):\033[0m ").strip()
            if user_input.lower() in ['exit', 'quit', 'bye', 'stop']:
                print("\033[1;31mNeo: Exiting voice mode...\033[0m")
                self.stop_listening_flag.set()
            elif user_input.lower() == 'history':
                print("\033[1;33mNeo: Displaying conversation history...\033[0m")
                self.display_history()
            elif user_input.lower().startswith('save'):
                self.save_session(user_input)
            elif user_input.lower().startswith('load'):
                self.load_session(user_input)
            else:
                response = self.neo_ai.query(user_input)
                self.display_response(response)
        except KeyboardInterrupt:
            print("\n\033[1;31mNeo: Interrupted. Returning to CLI mode...\033[0m")
            self.cli_mode = False

    def listen(self):
        try:
            with sr.Microphone(device_index=self.microphone_index) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Adjust for ambient noise
                self.display_animation() 
                audio = self.recognizer.listen(source)
                self.display_animation()
                command = self.recognizer.recognize_google(audio, language=self.language)
                self.display_user_command(command)
                return command
        except sr.UnknownValueError:
            self.display_response("Sorry, I did not understand.")
        except sr.RequestError as e:
            self.display_response(f"Sorry, the voice service is unavailable. Error: {e}")
        except Exception as e:
            self.display_response(f"An error occurred: {str(e)}")
        return None

    def display_user_command(self, command):
        print("\n" + "-" * 50)
        print(f"\033[1;36mYou:\033[0m {command}")
        print("-" * 50 + "\n")

    def display_response(self, response):
        print(f"\033[1;34mNeo:\033[0m {response}")
        print("=" * 50 + "\n")

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

    def run(self):
        self.listen_in_background()

        try:
            while not self.stop_listening_flag.is_set():
                time.sleep(0.1) 
        except KeyboardInterrupt:
            self.cli_mode = True
            print("\n\033[1;33mSwitching to CLI mode...\033[0m")
            self.stop_listening_flag.set()

if __name__ == "__main__":
    class MockNeoAI:
        def query(self, command):
            return f"Command received: {command}"

        def get_conversation_history(self):
            return [{"role": "user", "content": "Hello"}, {"role": "neo", "content": "Hi there!"}]

        def reset_history(self):
            self.history = []

    voice_interface = VoiceInterface(MockNeoAI(), {})
    voice_interface.run()
