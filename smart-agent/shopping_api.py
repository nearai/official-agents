import traceback
from mcp import ClientSession
from mcp.client.sse import sse_client
import json
import requests
from prompt import request_decision_example, schema_mock, hello_mock

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
                "description": tool['description'] if hasattr(tool, 'description') else None,
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
                self.env.add_reply(f"Calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
                try:
                    tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
                    if not tool:
                        raise Exception(f"Tool {tool_call.function.name} not found")

                    # Extract method and endpoint from tool definition
                    method = tool.get('method', 'POST').upper()  # Default to POST if not specified
                    endpoint = tool.get('endpoint', "")

                    # Handle path parameters in endpoint
                    data = json.loads(tool_call.function.arguments)
                    if '{' in endpoint and '}' in endpoint:
                        for param in tool.get('inputSchema', {}).get('properties', []):
                            param_name = param['name']
                            if param_name in data and f"{{{param_name}}}" in endpoint:
                                endpoint = endpoint.replace(f"{{{param_name}}}", str(data[param_name]))
                                del data[param_name]  # Remove from body data after using in path

                    url = f"{self.api_url}/{endpoint.lstrip('/')}"
                    headers = {"Content-Type": "application/json"}

                    # Make request based on method
                    if method == 'GET':
                        # For GET requests, convert data to query parameters
                        params = '&'.join([f"{k}={v}" for k, v in data.items()])
                        full_url = f"{url}{'?' if params else ''}{params}"
                        response = requests.get(full_url, headers=headers)
                        self.env.add_reply(f"URL: {full_url}")
                    else:
                        # For POST/PUT/DELETE, send data in body
                        response = requests.request(method, url, headers=headers, json=data)
                        self.env.add_reply(f"URL: {url}")

                    self.env.add_reply(f"Response: {response.json()}")

                    response.raise_for_status()
                    tool_result = response.json()
                    result = await self.process_tool_result(tool_result)
                    if result:
                        results.extend(result)
                except Exception as e:
                    error_msg = f"Error executing tool {tool_call.function.name}: {e}"
                    print(error_msg)
                    results.append(error_msg)
                    raise e
            return results

    async def get_tool_schema(self, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                self.env.add_reply(f"Getting tool schema for {tool_call.function.name}")
                self.env.add_reply(f"Tools: {str(self.tools)}")
                tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
                if tool:
                    # Convert tool to a serializable dictionary, excluding any methods
                    self.env.add_reply(f"Tool found: {json.dumps(tool)}")
                    return tool['schema'] if 'schema' in tool else None
        return None

    async def handle_schema_response(self, schema, results, messages):
        schema_url = schema.get("url")
        self.env.add_reply(f"Received results in schema handler: {results}")
        self.env.add_reply(f"Received messages in schema handler: {messages}")
        self.env.add_reply(f"Received schema in schema handler: {schema}")

        json_schema = self.fetch_schema(schema_url)
        # json_schema = schema_mock
        # if json_schema:
        #     request_decision_schema = self.get_request_decision_schema(json_schema)
        #     if request_decision_schema:
        #         json_schema = request_decision_schema
                # json_schema['$schema'] = "https://aitp.dev/capabilities/aitp-02-decisions/v1.0.0/schema.json"

        comp = self.env.completion(
            messages + [{"role": "user", "content": str(results)}, {"role": "system", "content": """
                ### Schema:
                {json_schema}
            """}],
            response_format={"type": "json_object", "schema": json_schema}
        )
        self.env.add_reply(f"Completion in tool_calls: {comp}")
        try:
            # Handle both string and object responses
            if isinstance(comp, str):
                comp_dict = json.loads(comp)
            elif hasattr(comp, 'content'):
                # If comp is an object with content attribute
                comp_dict = json.loads(comp.content)
            elif isinstance(comp, dict):
                comp_dict = comp
            else:
                raise TypeError(f"Unexpected completion type: {type(comp)}")

            if comp_dict.get("$schema") != schema_url:
                comp_dict["$schema"] = schema_url
            self.env.add_reply(json.dumps(comp_dict))
        except (json.JSONDecodeError, TypeError, KeyError, AttributeError) as e:
            print(f"Error processing completion schema: {e}")
            # Fallback to original response if processing fails
            self.env.add_reply(str(comp))

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
        self.env.add_reply(f"Getting AITP hello")
        return hello_mock

    async def run(self, messages):
        try:
            # all_tools = await requests.get(f"{self.api_url}/hello")
            hello_response = await self.get_aitp_hello()
            # self.env.add_reply(f"Hello response: {hello_response}")
            self.tools = self.extract_tools_from_aitp_hello(hello_response)
            # self.env.add_reply(f"Tools: {self.tools}")
            tools_description = self.format_mcp_tools(self.tools)
            completion = self.env.completion_and_get_tools_calls(messages, tools=tools_description, run_tools=False)
            # print(f"Completion received: {completion}")
            # self.env.add_system_log(f"Completion: {completion}")
        except Exception as e:
            error_msg = f"Error processing chat completion with MCP tools: {e}"
            print(error_msg)
            self.env.add_reply(error_msg)
            raise e
            return

        if completion.message:
            self.env.add_reply(completion.message)
        if completion.tool_calls:
            results = await self.handle_tool_calls(completion)
            if results:
                self.env.add_reply(f"Results: {results}")
                schema = await self.get_tool_schema(completion)
                self.env.add_reply(f"Schema: {schema}")
                if schema:
                    await self.handle_schema_response(schema, results, messages)
                else:
                    self.env.add_reply(json.dumps(results))

    # def get_request_decision_schema(self, json_schema):
    #     # Find the schema containing request_decision from anyOf array
    #     for schema_variant in json_schema.get('anyOf', []):
    #         if 'request_decision' in schema_variant.get('properties', {}):
    #             # Remove '#' from the beginning of the reference if present
    #             ref = schema_variant['properties']['$schema']['$ref']

    #             schema_variant['properties']['$schema']['$ref'] = "https://aitp.dev/capabilities/aitp-02-decisions/v1.0.0/schema.json" + ref
    #             return schema_variant
    #     return None