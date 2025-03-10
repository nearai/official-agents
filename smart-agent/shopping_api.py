import traceback
from mcp import ClientSession
from mcp.client.sse import sse_client
import json
import requests

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

    def format_tools_to_llm(self, tools):
        return [{
            "type": "function",
            "function": {
                "name": tool['name'],
                "description": (tool['description'] if hasattr(tool, 'description') else "") + ("\n\n Tool Instructions: " + tool['prompt'] if hasattr(tool, 'prompt') else ""),
                "parameters": tool['parameters']
            }
        } for tool in tools]

    def update_state(self, tool_name, result):
        self.state.set(tool_name, result)
        self.save_state()

    def is_all_required_params_filled(self, tool_call):
        tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
        if not tool:
            raise Exception(f"Tool {tool_call.function.name} not found")

        parameters = tool.get('parameters', {})
        required_params = parameters.get('required', [])
        arguments = json.loads(tool_call.function.arguments)

        return all(param in arguments and bool(arguments[param]) for param in required_params)


    async def handle_tool_calls(self, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            results = []
            for tool_call in assistant_message.tool_calls:
                input_schema = await self.get_tool_schema(assistant_message, 'input_schema')
                if input_schema and not self.is_all_required_params_filled(tool_call):
                    self.env.add_system_log(f"Input schema: {input_schema}")
                    await self.handle_schema_llm_call(input_schema, tool_call.function.arguments)
                    return None

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
                    for param_name, param_info in tool.get('parameters', {}).get('properties', {}).items():
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
                        self.update_state(tool_call.function.name, result)
                except Exception as e:
                    error_msg = f"Error executing tool {tool_call.function.name}: {e}"
                    print(error_msg)
                    self.update_state(tool_call.function.name, error_msg)
                    results.append(error_msg)
            return results

    async def get_tool_schema(self, assistant_message, schema_key):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                self.env.add_system_log(f"Getting tool schema for {tool_call.function.name}")
                tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
                if tool:
                    # Convert tool to a serializable dictionary, excluding any methods
                    self.env.add_system_log(f"Tool found: {json.dumps(tool)}")
                    return tool[schema_key] if schema_key in tool else None
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

    async def handle_schema_llm_call(self, schema, data):
        schema_url = schema.get("url")
        json_schema = self.fetch_schema(schema_url)

        messages = [{"role": "system", "content": f"""You are a developer. You are given a schema and a content. Your task is to fill the schema with the content provided by the user.
                     The output must be a code that returns a 'result' variable containing the final output. Do not include any other text since the code block will be executed programmatically.
                     - The $schema property must be respected. It should be the first line of the 'result' output and it should be '{schema_url}'.
                     - The code must be in Python.
                     - Do not use fake data, you have the information provided by the user
                     - DO NOT USE ANY EXTERNAL LIBRARIES AND BE CAREFUL WITH THE IMPORTS - the code runs in an isolated environment
                     - Return the result in a 'result' variable pure dict, don't run json.loads or json.dumps on it
                     - The code must start with exactly '```python' and end with exactly '```'
                     """},
            {"role": "user", "content": f"""
            ## Content: {str(data)}
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


    def format_tools_message(self, tools):
        if not tools:
            return "No tools available"
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"{tool['name']}: {tool['description']}")
        return f"Available tools:\n{chr(10).join(tool_descriptions)}"

    async def get_aitp_hello(self):
        self.env.add_system_log(f"Getting AITP hello")
        return requests.get(f"{self.api_url}/hello").json()

    async def initialize(self):
        hello_response = await self.get_aitp_hello()
        self.tools = self.extract_tools_from_aitp_hello(hello_response)
        self.env.add_system_log(self.format_tools_message(self.tools))


    async def run(self, messages, state, save_state):
        try:
            await self.initialize()
            self.state = state
            self.save_state = save_state

            tools_description = self.format_tools_to_llm(self.tools)
            self.env.add_system_log(f"State: {state}")
            if state:
                messages.append({"role": "user", "content": "If you need to fill a tool parameter, use the following context only: " + state.model_dump_json()})

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
                schema = await self.get_tool_schema(completion, 'output_schema')
                self.env.add_system_log(f"Schema: {schema}")
                if schema:
                    await self.handle_schema_llm_call(schema, results)
                else:
                    output = self.env.completion(
                        messages=[{"role": "system", "content": "Show the results in a friendly format"}, {"role": "user", "content": str(results)}]
                    )
                    self.env.add_reply(output)