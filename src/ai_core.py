import httpx
import jwt
import json
import logging
import os
import time
from src.command_executor import execute_command_in_terminal, execute_command
from src.utils import parse_hooks, load_persistent_memory
import openai
from src.token_manager import TokenManager
from src.command_executor import wait_for_command_completion
from src.approval_handler import ApprovalHandler

os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('socks_proxy', None)
os.environ.pop('SOCKS_PROXY', None)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


class NeoAI:
    def __init__(self, config):
        self.mode = config.get('mode', 'lm_studio')
        logging.info(f"Initializing NeoAI in {self.mode} mode.")
        self.require_approval = config.get('command_approval', {}).get('require_approval', True)
        self.auto_approve_all = config.get('command_approval', {}).get('auto_approve_all', False)
        self.is_streaming_mode = config.get('stream', True)
        self.config = config

        if self.mode == 'digital_ocean':
            self.token_manager = TokenManager(
                agent_id=config['digital_ocean_config']['agent_id'],
                agent_key=config['digital_ocean_config']['agent_key'],
                auth_api_url="https://cluster-api.do-ai.run/v1"
            )
            self.access_token = self.token_manager.get_valid_access_token()
            self.token_timestamp = time.time()
            self.agent_endpoint = config['digital_ocean_config']['agent_endpoint']
            self.model = config['digital_ocean_config']['model']
        else:
            openai.api_base = config['api_url']
            openai.api_key = config['api_key']
            self.model = config['model']

        self.lm_studio_config = config.get('lm_studio_config', {})
        self.history = []
        self.context_initialized = False

    def _ensure_valid_token(self):
        """Vérifier que le token est toujours valide et le renouveler si nécessaire"""
        if self.mode != 'digital_ocean':
            return

        # On vérifie le token toutes les 15 minutes ou en cas d'erreur 401
        current_time = time.time()
        token_age = current_time - self.token_timestamp

        if token_age > 900:  # 15 minutes
            try:
                logging.info("Token age > 15 minutes, refreshing...")
                self.access_token = self.token_manager.get_valid_access_token()
                self.token_timestamp = current_time
            except Exception as e:
                logging.error(f"Error refreshing token: {e}")
                # On tente de réinitialiser complètement la gestion des tokens
                self.token_manager = TokenManager(
                    agent_id=self.config['digital_ocean_config']['agent_id'],
                    agent_key=self.config['digital_ocean_config']['agent_key'],
                    auth_api_url="https://cluster-api.do-ai.run/v1"
                )
                self.access_token = self.token_manager.get_valid_access_token()
                self.token_timestamp = current_time

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
        instruction = f"{self.lm_studio_config.get('input_prefix', '### Instruction:')} {prompt} {self.lm_studio_config.get('input_suffix', '### Response:')}"

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

                        if '<s>' in full_response:
                            system_command = full_response.split('<s>')[-1]
                        if '</s>' in system_command:
                            break

            print()

            if system_command and '</s>' in system_command:
                return self._process_response(full_response)
            else:
                return full_response.strip()

        except Exception as e:
            print(f"Erreur lors de la requête à LM Studio : {e}")
            return "An error occurred while querying LM Studio."

    def _query_digitalocean(self, prompt):
        self._ensure_valid_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": self.history + [{"role": "user", "content": prompt}],
            "stream": True,
        }

        max_retries = 2
        retry_count = 0

        while retry_count < max_retries:
            try:
                with httpx.stream(
                        "POST",
                        f"{self.agent_endpoint}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=30.0
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
                    return ""

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and retry_count < max_retries:
                    retry_count += 1
                    # Force token refresh
                    self.token_manager = TokenManager(
                        agent_id=self.config['digital_ocean_config']['agent_id'],
                        agent_key=self.config['digital_ocean_config']['agent_key'],
                        auth_api_url="https://cluster-api.do-ai.run/v1"
                    )
                    self.access_token = self.token_manager.get_valid_access_token()
                    self.token_timestamp = time.time()

                    # Mettre à jour l'en-tête avec le nouveau token
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    continue
                else:
                    print(f"Détails: {e}")
                    break

            except httpx.ReadTimeout:
                retry_count += 1
                if retry_count < max_retries:
                    self.access_token = self.token_manager.get_valid_access_token()
                    self.token_timestamp = time.time()
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    continue
                else:
                    print("Échec après plusieurs tentatives.")
                    break

            except Exception as e:
                import traceback
                print(f"\nErreur détaillée: {e}")
                print(traceback.format_exc())
                break

        return "Désolé, je n'ai pas pu obtenir une réponse. Veuillez réessayer."

    def query(self, prompt):
        try:
            if not self.context_initialized:
                context = self.initialize_context()
                prompt = f"{context}\n\n{prompt}"

            self.history.append({"role": "user", "content": prompt})

            if self.mode == 'digital_ocean':
                return self._query_digitalocean(prompt)
            else:
                response = self._query_lm_studio(prompt)
                if response:
                    self.history.append({"role": "assistant", "content": response})
                return response
        except Exception as e:
            import traceback
            print(f"Erreur détaillée: {e}")
            print(traceback.format_exc())

    def _process_response(self, response):
        try:
            hooks = parse_hooks(response)
            for hook_type, content in hooks:
                if hook_type == "s" or hook_type == "system":  # Accept both tag types
                    # Use the approval handler
                    approval_handler = ApprovalHandler(self.require_approval, self.auto_approve_all)
                    approved, option = approval_handler.request_approval(content)

                    if not approved:
                        return "Command execution was denied."
                    elif option == 'all':
                        self.auto_approve_all = True

                    # Execute the command with the new executor
                    temp_file = execute_command_in_terminal(content)
                    if temp_file:
                        result = wait_for_command_completion(temp_file)

                        # Send the result as a new message
                        follow_up_prompt = f"The command '{content}' was executed. Here is the result:\n{result}"
                        self.history.append({"role": "user", "content": follow_up_prompt})

                        if self.mode == "digital_ocean":
                            return self._query_digitalocean(follow_up_prompt)
                        elif self.mode == "lm_studio":
                            return self._query_lm_studio(follow_up_prompt)
                        else:
                            return f"Unknown mode: {self.mode}. Unable to send follow-up prompt."
                    else:
                        return "Error: Failed to execute the command."

        except Exception as e:
            import traceback
            print(f"\nAn unexpected error occurred while processing the response: {e}")
            print(traceback.format_exc())
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

                    if '<s>' in full_response:
                        system_command = full_response.split('<s>')[-1]
                    if '</s>' in system_command:
                        break

        if system_command and '</s>' in system_command:
            return self._process_response(full_response)
        return full_response.strip()

    def get_conversation_history(self):
        return self.history

    def reset_history(self):
        self.history = []
        self.context_initialized = False
        self.auto_approve_all = False