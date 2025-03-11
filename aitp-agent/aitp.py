import json
import requests
from nearai.agents.environment import Environment
from aitp_tools_handler import AitpToolsHandler

class Aitp(object):
    def __init__(self, _env: Environment):
        self.aitp_api_url = _env.env_vars.get("AITP_API_URL")
        self.aitp_tools_handler = None
        self.aitp_hello_response = None

        self.messages = []
        self.state = None
        self.save_state = None

        self.env = _env

    def update_state(self, tool_name, result):
        self.state.set(tool_name, result)
        self.save_state()

    async def get_aitp_hello(self):
        self.env.add_system_log(f"Getting AITP hello")
        self.aitp_hello_response = requests.get(f"{self.aitp_api_url}/hello").json()

    def extract_tools_from_aitp_hello(self):
        if isinstance(self.aitp_hello_response, str):
            self.aitp_hello_response = json.loads(self.aitp_hello_response)

        tools = []
        for api_command in self.aitp_hello_response['api_commands']:
            properties = {}
            required_params = []

            for parameter in api_command['parameters'] if 'parameters' in api_command else []:
                properties[parameter['name']] = {
                    "type": parameter['type'],
                    "description": parameter['description']
                }
                if parameter.get('required', False):
                    required_params.append(parameter['name'])

            tool = {
                "name": api_command['command'],
                "method": api_command['method'],
                "endpoint": api_command['endpoint'],
                "prompt": api_command['prompt'],
                "description": api_command['description'],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                },
                "output_schema": api_command['outputSchema'] if 'outputSchema' in api_command else None,
                "input_schema": api_command['inputSchema'] if 'inputSchema' in api_command else None,
            }
            tools.append(tool)
        return tools

    async def run(self, messages, state, save_state):
        try:
            self.messages = messages
            self.state = state
            self.save_state = save_state

            await self.get_aitp_hello()
            tools = self.extract_tools_from_aitp_hello()
            self.aitp_tools_handler = AitpToolsHandler(tools, self.aitp_api_url, self.update_state, self.env)
            self.env.add_system_log(self.aitp_tools_handler.get_tools_description_message())

            tools_description = self.aitp_tools_handler.get_tools_in_llm_format()
            self.env.add_system_log(f"State: {self.state}")
            if self.state:
                self.messages.append({"role": "user", "content": "If you need to fill a tool parameter, use the following context only: " + self.state.model_dump_json()})

            self.env.add_system_log(f"\nRunning completion and get tools calls with: \n\nmessages: {self.messages}, \ntools: {tools_description}, \nrun_tools: False, \ntemperature: 0.0\n")
            completion = self.env.completion_and_get_tools_calls(self.messages, tools=tools_description, run_tools=False, temperature=0.1)
            self.env.add_system_log(f"\nCompletion: {completion}\n\n")
        except Exception as e:
            error_msg = f"Error processing chat completion with MCP tools: {e}"
            print(error_msg)
            self.env.add_reply(error_msg)
            return

        if completion.message:
            self.env.add_reply(completion.message)
        if completion.tool_calls:
            await self.aitp_tools_handler.handle_tool_calls(completion)

