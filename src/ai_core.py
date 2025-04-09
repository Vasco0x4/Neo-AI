import httpx
import jwt
import json
import logging
from src.command_executor import execute_command_in_terminal, execute_command
from src.utils import parse_hooks, load_persistent_memory
import openai
from src.token_manager import TokenManager
from src.command_executor import wait_for_command_completion

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

from src.token_manager import TokenManager


class NeoAI:
    def __init__(self, config):
        self.mode = config.get('mode', 'lm_studio')
        logging.info(f"Initializing NeoAI in {self.mode} mode.")
        self.require_approval = config.get('command_approval', {}).get('require_approval', True)
        self.auto_approve_all = config.get('command_approval', {}).get('auto_approve_all', False)
        self.is_streaming_mode = config.get('stream', True)

        if self.mode == 'digital_ocean':
            self.token_manager = TokenManager(
                agent_id=config['digital_ocean_config']['agent_id'],
                agent_key=config['digital_ocean_config']['agent_key'],
                auth_api_url="https://cluster-api.do-ai.run/v1"
            )
            self.access_token = self.token_manager.get_valid_access_token()
            self.agent_endpoint = config['digital_ocean_config']['agent_endpoint']
            self.model = config['digital_ocean_config']['model']
        else:
            openai.api_base = config['api_url']
            openai.api_key = config['api_key']
            self.model = config['model']

        self.lm_studio_config = config['lm_studio_config']
        self.history = []
        self.context_initialized = False

    def initialize_context(self):
        context_commands = [
            "pwd",
            "ls"
        ]
        context_data = load_persistent_memory()
        initial_context = "<context>\n"

        for command in context_commands:
            result = execute_command(command)
            initial_context += f"Command: {command}\nResult:\n{result}\n"

        full_context = f"{context_data}\n\n{initial_context}</context>"
        self.context_initialized = True
        return full_context

    def _query_lm_studio(self, prompt):
        instruction = f"{self.lm_studio_config['input_prefix']}{prompt}{self.lm_studio_config['input_suffix']}"

        messages = self.history.copy()
        messages.append({"role": "user", "content": instruction})

        try:
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=self.is_streaming_mode,
            )

            full_response = ""
            system_command = ""
            is_first_chunk = True

            for chunk in completion:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    content = chunk['choices'][0]['delta'].get('content', '')
                    if content:
                        if is_first_chunk:
                            print("\033[1;34mNeo:\033[0m ", end='', flush=True)
                            is_first_chunk = False

                        print(content, end='', flush=True)
                        full_response += content

                        if '<system>' in full_response:
                            system_command = full_response.split('<system>')[-1]
                        if '</system>' in system_command:
                            break

            print()

            if system_command and '</system>' in system_command:
                return self._process_response(full_response)
            else:
                return full_response.strip()

        except Exception as e:
            print(f"Error LM Studio : {e}")
            return "An error occurred while querying LM Studio."

    def _query_digitalocean(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": self.history + [{"role": "user", "content": prompt}],
            "stream": True,
        }

        try:
            transport = httpx.HTTPTransport(proxy=None)
            client = httpx.Client(transport=transport)

            with client.stream(
                    "POST",
                    f"{self.agent_endpoint}/chat/completions",
                    json=payload,
                    headers=headers,
            ) as response:
                response.raise_for_status()

                is_first_chunk = True
                assistant_response = ""

                for line in response.iter_lines():
                    line = line.strip()
                    if line.startswith("data:"):
                        line = line[len("data:"):].strip()

                    if line:
                        try:
                            chunk = json.loads(line)
                            if "choices" in chunk and chunk["choices"]:
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    if is_first_chunk:
                                        print("\033[1;34mNeo:\033[0m ", end="", flush=True)
                                        is_first_chunk = False
                                    print(content, end="", flush=True)
                                    assistant_response += content
                        except json.JSONDecodeError:
                            if line == "[DONE]":
                                break
                            continue
                print()

                if assistant_response.strip():
                    self.history.append({"role": "assistant", "content": assistant_response.strip()})
                    return self._process_response(assistant_response.strip())

        except httpx.HTTPStatusError as e:
            print("\nErreur HTTP.")
            print(f"Details: {str(e)}")
        except Exception as e:
            print("\nError.")
            print(f"Details: {str(e)}")

    def query(self, prompt):
        try:
            if not self.context_initialized:
                context = self.initialize_context()
                prompt = f"{context}\n\n{prompt}"

            self.history.append({"role": "user", "content": prompt})

            if self.mode == 'digital_ocean':
                self._query_digitalocean(prompt)
            else:
                response = self._query_lm_studio(prompt)
                if response:
                    self.history.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"Erreur: {e}")

    def _process_response(self, response):
        try:
            hooks = parse_hooks(response)
            for hook_type, content in hooks:
                if hook_type == "system":
                    if self.require_approval and not self.auto_approve_all:
                        print("\n" + "=" * 50)
                        print(
                            f"\033[1;33m[Approval Required]\033[0m Neo wants to execute: {content}. Approve? (y/n/T for approve all): ",
                            end='')
                        approval = input().strip().lower()
                        print("=" * 50 + "\n")

                        if approval == 'n':
                            print("\033[1;31m[System]\033[0m Command execution denied by user.")
                            return "Command execution was denied."
                        elif approval == 't':
                            self.auto_approve_all = True
                            print("\033[1;33m[System]\033[0m All future commands will be automatically approved.")

                    temp_file = execute_command_in_terminal(content)
                    if temp_file:
                        print("[System] Command sent.")
                        result = wait_for_command_completion(temp_file)

                        follow_up_prompt = f"The command '{content}' was executed. Here is the result:\n{result}"
                        self.history.append({"role": "user", "content": follow_up_prompt})

                        if self.mode == "digital_ocean":
                            return self._query_digitalocean(follow_up_prompt)
                        elif self.mode == "lm_studio":
                            return self._query_lm_studio(follow_up_prompt)
                        else:
                            return f"Unknown mode: {self.mode}. Unable to send follow-up prompt."
                    else:
                        return "Error: Failed to execute the command in an external terminal."

        except Exception as e:
            print(f"\nUne erreur inattendue s'est produite lors du traitement de la réponse : {e}")
            return "An error occurred while processing the system command."

        return response.strip()

    def _get_ai_response(self, instruction):
        messages = self.history + [{"role": "user", "content": instruction}]

        completion = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            stream=self.is_streaming_mode,
        )

        full_response = ""
        system_command = ""

        for chunk in completion:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                content = chunk['choices'][0]['delta'].get('content', '')
                if content:
                    full_response += content

                    if '<system>' in full_response:
                        system_command = full_response.split('<system>')[-1]
                    if '</system>' in system_command:
                        break

        if system_command and '</system>' in system_command:
            return self._process_response(full_response)
        return full_response.strip()

    def get_conversation_history(self):
        return self.history

    def reset_history(self):
        self.history = []
        self.context_initialized = False
        self.auto_approve_all = False