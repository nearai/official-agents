import traceback
from mcp import ClientSession
from mcp.client.sse import sse_client
import json
import requests
from prompt import request_decision_example, schema_mock, hello_mock

context_file = "context.json"

class ShoppingAPI:
    def __init__(self, env):
        self.env = env
        self.api_url = env.env_vars.get("AITP_API_URL")
        print(f"Using API at {self.api_url}")
        self.tools = []

    def fetch_schema(self, schema_url):
        """Fetch JSON schema from URL."""
        try:
            response = requests.get(schema_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching schema from {schema_url}: {e}")
            return None

    async def process_tool_result(self, tool_result):
        if not tool_result or 'body' not in tool_result:
            self.env.add_reply("No content received from tool")
            return

        results = []
        body = tool_result['body']
        if isinstance(body, list):
            results.append(json.dumps(tool_result['body']))
        else:
            try:
                if isinstance(body, dict):
                    results.append(json.dumps(body, indent=2))
                else:
                    result_json = json.loads(body)
                    results.append(json.dumps(result_json, indent=2))
            except json.JSONDecodeError:
                results.append(body)
        return results

    def format_mcp_tools(self, tools):
        return [{
            "type": "function",
            "function": {
                "name": tool['name'],
                "description": (tool['description'] if hasattr(tool, 'description') else "") + ("\n\n Tool Instructions: " + tool['prompt'] if hasattr(tool, 'prompt') else ""),
                "parameters": {
                    "type": "object",
                    "properties": tool['inputSchema']['properties'],
                    "required": tool['inputSchema']['required'] if 'required' in tool['inputSchema'] else [],
                    "additionalProperties": tool['inputSchema']['additionalProperties'] if 'additionalProperties' in tool['inputSchema'] else False
                }
            }
        } for tool in tools]


    async def handle_tool_calls(self, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            results = []
            for tool_call in assistant_message.tool_calls:
                print(f"Calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
                self.env.add_system_log(f"Calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
                try:
                    tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
                    if not tool:
                        raise Exception(f"Tool {tool_call.function.name} not found")

                    # Extract method and endpoint from tool definition
                    method = tool.get('method', 'POST').upper()  # Default to POST if not specified
                    endpoint = tool.get('endpoint', "")

                    # Handle path parameters in endpoint
                    data = json.loads(tool_call.function.arguments)
                    for param_name, param_info in tool.get('inputSchema', {}).get('properties', {}).items():
                        if param_name in data and f"{{{param_name}}}" in endpoint:
                            endpoint = endpoint.replace(f"{{{param_name}}}", str(data[param_name]))
                            del data[param_name]

                    url = f"{self.api_url}/{endpoint.lstrip('/')}"
                    headers = {"Content-Type": "application/json"}

                    # Make request based on method
                    if method == 'GET':
                        # For GET requests, convert data to query parameters
                        params = '&'.join([f"{k}={v}" for k, v in data.items()])
                        full_url = f"{url}{'?' if params else ''}{params}"
                        response = requests.get(full_url, headers=headers)
                        self.env.add_system_log(f"URL: {full_url}")
                    else:
                        # For POST/PUT/DELETE, send data in body
                        response = requests.request(method, url, headers=headers, json=data)
                        self.env.add_system_log(f"URL: {url}")

                    self.env.add_system_log(f"Response: {response.json()}")

                    response.raise_for_status()
                    tool_result = response.json()
                    result = await self.process_tool_result(tool_result)
                    if result:
                        results.extend(result)
                        self.save_state(tool_call.function.name, result)
                except Exception as e:
                    error_msg = f"Error executing tool {tool_call.function.name}: {e}"
                    print(error_msg)
                    self.save_state(tool_call.function.name, error_msg)
                    results.append(error_msg)
            return results

    async def get_tool_schema(self, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                self.env.add_system_log(f"Getting tool schema for {tool_call.function.name}")
                self.env.add_system_log(f"Tools: {str(self.tools)}")
                tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
                if tool:
                    # Convert tool to a serializable dictionary, excluding any methods
                    self.env.add_system_log(f"Tool found: {json.dumps(tool)}")
                    return tool['schema'] if 'schema' in tool else None
        return None

    def is_code_block(self, code):
        return code.startswith("```") and code.endswith("```")

    def remove_null_values(self, obj):
        if isinstance(obj, dict):
            return {k: self.remove_null_values(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self.remove_null_values(i) for i in obj if i is not None]
        return obj

    def sanitize_schema(self, schema):
        return self.remove_null_values(schema)

    async def handle_schema_response(self, schema, results):
        schema_url = schema.get("url")
        json_schema = self.fetch_schema(schema_url)

        messages = [{"role": "system", "content": """You are a developer. You are given a schema and a content. Your task is to fill the schema with the content provided by the user.
                     The output must be a code that returns a 'result' variable containing the final output. Do not include any other text since the code block will be executed programmatically.
                     - The code must be in Python.
                     - DO NOT USE ANY EXTERNAL LIBRARIES AND BE CAREFUL WITH THE IMPORTS - the code runs in an isolated environment
                     - Return the result in a 'result' variable pure dict, don't run json.loads or json.dumps on it
                     - The code must start with exactly '```python' and end with exactly '```'
                     """},
            {"role": "user", "content": f"""
            ## Content: {str(results)}
            ## Schema: {json_schema}
            """}]

        if schema.get("prompt"):
            messages.append({"role": "system", "content": "Specific instructions for the code: " + schema.get("prompt")})

        code = self.env.completion(messages, temperature=0.1)
        self.env.add_system_log(f"Completion in tool_calls: {code}")

        try:
            if self.is_code_block(code):
                code = code.replace("```python", "").replace("```", "")
                # Create a local dictionary to capture variables from exec
                local_dict = {}
                # Execute the code with the local dictionary
                exec(code, {}, local_dict)
                self.env.add_system_log(f"Local dict: {local_dict}")
                self.env.add_system_log(f"Local dict result: {local_dict.get('result')}")
                result = self.sanitize_schema(local_dict.get('result'))
                # Return the result - assuming the code creates a 'result' variable
                self.env.add_reply(json.dumps(result))
                return result
            else:
                raise ValueError("Invalid code")
        except Exception as e:
            print(f"Error executing code: {e}")
            self.env.add_reply(traceback.format_exc())
            return None

    def extract_tools_from_aitp_hello(self, response):
        # Parse the response string into JSON if it's not already parsed
        if isinstance(response, str):
            response = json.loads(response)

        tools = []
        for api_command in response['api_commands']:
            properties = {}
            required_params = []

            for parameter in api_command['parameters'] if 'parameters' in api_command else []:
                properties[parameter['name']] = {
                    "type": parameter['type'],
                    "description": parameter['description']
                }
                # Add parameter name to required list if required is True
                if parameter.get('required', False):
                    required_params.append(parameter['name'])

            tool = {
                "name": api_command['command'],
                "method": api_command['method'],
                "endpoint": api_command['endpoint'],
                "prompt": api_command['prompt'],
                "description": api_command['description'],
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                },
                "schema": api_command['schema'] if 'schema' in api_command else None,
            }
            tools.append(tool)
        return tools

    async def get_aitp_hello(self):
        self.env.add_system_log(f"Getting AITP hello")
        return requests.get(f"{self.api_url}/hello").json()

    async def initialize(self):
        hello_response = await self.get_aitp_hello()
        self.tools = self.extract_tools_from_aitp_hello(hello_response)
        self.env.add_system_log(format_tools_message(self.tools))

    def get_state(self):
        all_files = self.env.list_files(self.env.get_agent_temp_path())
        if context_file in all_files:
            try:
                _state = self.env.read_file(context_file)
                parsed_dict = json.loads(_state)
                return parsed_dict
            except json.JSONDecodeError:
                return {}
        else:
            return {}

    def save_state(self, key, value):
        current_state = self.get_state()
        current_state[key] = value
        self.env.add_system_log(f"Saving state: {current_state}")
        self.env.write_file(context_file, json.dumps(current_state, indent=2))

    async def run(self, messages):
        try:
            await self.initialize()

            tools_description = self.format_mcp_tools(self.tools)
            self.env.add_system_log(f"Messages: {messages}")
            if self.get_state():
                messages.append({"role": "user", "content": "Context: " + self.get_state()})

            completion = self.env.completion_and_get_tools_calls(messages, tools=tools_description, run_tools=False, temperature=0.0)
        except Exception as e:
            error_msg = f"Error processing chat completion with MCP tools: {e}"
            print(error_msg)
            self.env.add_reply(error_msg)
            return

        if completion.message:
            self.env.add_reply(completion.message)
        if completion.tool_calls:
            results = await self.handle_tool_calls(completion)
            if results:
                self.env.add_system_log(f"Results: {results}")
                schema = await self.get_tool_schema(completion)
                self.env.add_system_log(f"Schema: {schema}")
                if schema:
                    await self.handle_schema_response(schema, results)
                else:
                    output = self.env.completion(
                        messages=[{"role": "system", "content": "Show the results in a friendly format"}, {"role": "user", "content": str(results)}]
                    )
                    self.env.add_reply(output)

def format_tools_message(tools):
    if not tools:
        return "No tools available"
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(f"{tool['name']}: {tool['description']}")
    return f"Available tools:\n{chr(10).join(tool_descriptions)}"