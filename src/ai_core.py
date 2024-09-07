import openai  # type: ignore
import sys
import os
from src.command_executor import execute_command
from src.utils import parse_hooks, load_persistent_memory

class NeoAI:
    def __init__(self, config):
        openai.api_base = config['api_url']
        openai.api_key = config['api_key']
        self.model = config['model']
        self.lm_studio_config = config['lm_studio_config']
        self.history = []
        self.context_initialized = False
        self.require_approval = config.get('command_approval', {}).get('require_approval', True)
        self.auto_approve_all = config.get('command_approval', {}).get('auto_approve_all', False)
        self.is_streaming_mode = True

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

    def query(self, prompt):
        if not self.context_initialized:
            context = self.initialize_context()
            prompt = f"{context}\n\n{prompt}"

        self.history.append({"role": "user", "content": prompt})
        
        instruction = f"{self.lm_studio_config['input_prefix']}{prompt}{self.lm_studio_config['input_suffix']}"
        response = self._get_ai_response(instruction)
        
        if response:
            self.history.append({"role": "assistant", "content": response})
        return response

    def _get_ai_response(self, instruction):
        messages = self.history.copy()
        messages.append({"role": "user", "content": instruction})
        
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

    def _process_response(self, response):
        hooks = parse_hooks(response)
        for hook_type, content in hooks:
            if hook_type == "system":
                if self.require_approval and not self.auto_approve_all:
                    print("\n" + "="*50)
                    print(f"\033[1;33m[Approval Required]\033[0m Neo wants to execute: {content}. Approve? (y/n/T for approve all): ", end='')
                    approval = input().strip().lower()
                    print("="*50 + "\n")  

                    if approval == 'n':
                        print("\033[1;31m[System]\033[0m Command execution denied by user.")
                        return "Command execution was denied."
                    elif approval == 't':
                        self.auto_approve_all = True
                        print("\033[1;33m[System]\033[0m All future commands will be automatically approved.")
                
                ##print("\n" + "-"*50)
                ##print(f"\033[1;35m[Executing Command]\033[0m {content}")
                ##print("-"*50 + "\n")

                result = execute_command(content)

                print("\n" + "-"*50)
                print(f"\033[1;32m[Command Result]\033[0m\n{result}")
                print("-"*50 + "\n") 

                return self._get_ai_response(f"{self.lm_studio_config['input_prefix']}The command '{content}' has been executed. The result is:\n{result}\nPlease interpret this result and continue the conversation.{self.lm_studio_config['input_suffix']}")
        return response.strip()

    def get_conversation_history(self):
        return self.history

    def reset_history(self):
        self.history = []
        self.context_initialized = False
        self.auto_approve_all = False