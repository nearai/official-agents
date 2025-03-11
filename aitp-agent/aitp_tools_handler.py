import json
import requests

from nearai.agents.environment import Environment
from aitp_schema_handler import AitpSchemaHandler
from utils import Utils

class AitpToolsHandler(object):
  def __init__(self, tools, aitp_api_url, update_state, _env: Environment):
    self.tools = tools
    self.env = _env
    self.aitp_api_url = aitp_api_url
    self.update_state = update_state

    self.aitp_schema_handler = AitpSchemaHandler(_env)
    self.utils = Utils()

  def get_tool_by_name(self, name):
    tool = next((t for t in self.tools if t['name'] == name), None)
    if not tool:
        raise Exception(f"Tool {name} not found")
    return tool

  def get_tools_description_message(self):
    if not self.tools:
        return "No tools available"
    tool_descriptions = []
    for tool in self.tools:
        tool_descriptions.append(f"{tool['name']}: {tool['description']}")
    return f"Available tools:\n{chr(10).join(tool_descriptions)}"

  async def get_tool_schema(self, assistant_message, schema_key):
    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            self.env.add_system_log(f"Getting tool schema for {tool_call.function.name}")
            tool = next((t for t in self.tools if t['name'] == tool_call.function.name), None)
            if tool:
                self.env.add_system_log(f"Tool found: {json.dumps(tool)}")
                return tool[schema_key] if schema_key in tool else None
    return None

  def get_tools_in_llm_format(self):
    return [{
        "type": "function",
        "function": {
            "name": tool['name'],
            "description": (tool['description'] if hasattr(tool, 'description') else "") + ("\n\n Tool Instructions: " + tool['prompt'] if hasattr(tool, 'prompt') else ""),
            "parameters": tool['parameters']
        }
    } for tool in self.tools]

  async def get_tool_aitp_endpoint_response(self, aitp_endpoint_response):
    if not aitp_endpoint_response or 'body' not in aitp_endpoint_response:
      self.env.add_system_log("No content received from tool")
      return None

    results = []
    body = aitp_endpoint_response['body']
    if isinstance(body, list):
        results.append(json.dumps(aitp_endpoint_response['body']))
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


  async def handle_tool_calls(self, assistant_message):
    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
        results = []
        for tool_call in assistant_message.tool_calls:
            input_schema = await self.get_tool_schema(assistant_message, 'input_schema')

            if input_schema: # only use the schema if it still has any required params to be filled
                if not self.is_tools_params_ready(tool_call):
                    self.env.add_system_log(f"Input schema: {input_schema}")
                    await self.aitp_schema_handler.handle_schema_llm_call(input_schema, tool_call.function.arguments)
                    return None

            await self.call_tool(tool_call, results)

    await self.process_results(assistant_message, results)

  def is_tools_params_ready(self, tool_call):
    tool = self.get_tool_by_name(tool_call.function.name)

    parameters = tool.get('parameters', {})
    required_params = parameters.get('required', [])
    arguments = json.loads(tool_call.function.arguments)

    return self.utils.is_all_required_params_filled(arguments, required_params)

  async def call_tool(self, tool_call, results):
    self.env.add_system_log(f"Calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
    try:
        tool = self.get_tool_by_name(tool_call.function.name)

        method = tool.get('method', 'POST').upper()
        endpoint = tool.get('endpoint', "")

        if not endpoint:
            raise Exception(f"Tool {tool_call.function.name} has no endpoint to call")

        data = json.loads(tool_call.function.arguments)
        for param_name, param_info in tool.get('parameters', {}).get('properties', {}).items():
            if param_name in data and f"{{{param_name}}}" in endpoint:
                endpoint = endpoint.replace(f"{{{param_name}}}", str(data[param_name]))
                del data[param_name]

        url = f"{self.aitp_api_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}

        if method == 'GET':
            params = '&'.join([f"{k}={v}" for k, v in data.items()])
            full_url = f"{url}{'?' if params else ''}{params}"
            response = requests.get(full_url, headers=headers)
            self.env.add_system_log(f"URL: {full_url}")
        else:
            response = requests.request(method, url, headers=headers, json=data)
            self.env.add_system_log(f"URL: {url}")

        self.env.add_system_log(f"Response: {response.json()}")

        response.raise_for_status()
        tool_result = response.json()
        result = await self.get_tool_aitp_endpoint_response(tool_result)
        if result:
            results.extend(result)
            self.update_state(tool_call.function.name, result)
    except Exception as e:
        error_msg = f"Error executing tool {tool_call.function.name}: {e}"
        print(error_msg)
        self.update_state(tool_call.function.name, error_msg)
        results.append(error_msg)

  async def process_results(self, assistant_message, results):
    self.env.add_system_log(f"Results: {results}")
    schema = await self.get_tool_schema(assistant_message, 'output_schema')
    self.env.add_system_log(f"Schema: {schema}")
    if schema:
        await self.aitp_schema_handler.handle_schema_llm_call(schema, results)
    else:
        output = self.env.completion(
            messages=[{"role": "system", "content": "Show the results in a friendly format"}, {"role": "user", "content": str(results)}]
        )
        self.env.add_reply(output)