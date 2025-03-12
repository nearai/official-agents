import traceback

from mcp import ClientSession
from mcp.client.sse import sse_client

import json
class ShoppingMCP:
    def __init__(self, env, tool_post_processor_function = None):
        self.env = env # "http://host.docker.internal:3003") #
        self.mcp_server_url = env.env_vars.get("MCP_SERVER_URL")
        print(f"Using MCP server at {self.mcp_server_url}")
        self.session = None
        self.tools = []
        self.tool_post_processor_function = tool_post_processor_function

    def format_mcp_tools(self, tools):
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description if hasattr(tool, 'description') else None,
                "parameters": {
                    "type": "object",
                    "properties": tool.inputSchema.get("properties", {}),
                    "required": tool.inputSchema.get("required", []),
                    "additionalProperties": tool.inputSchema.get("additionalProperties", False)
                }
            }
        } for tool in tools]

    async def process_tool_result(self, tool_result):
        if not tool_result or not hasattr(tool_result, 'content'):
            self.env.add_reply("No content received from tool")
            return

        results = []
        for content in tool_result.content:
            if content.type != 'text':
                continue

            try:
                result_json = json.loads(content.text)
                results.append(json.dumps(result_json, indent=2))
            except json.JSONDecodeError:
                results.append(content.text)
        return results


    async def handle_tool_calls(self, session, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            results = []
            for tool_call in assistant_message.tool_calls:
                print(f"calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
                tool_result = await session.call_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                result = await self.process_tool_result(tool_result)
                if self.tool_post_processor_function:
                    result = self.tool_post_processor_function(tool_call, result)
                results.extend(result)
            return results

    async def get_mcp_tools(self, session):
        if len(self.tools):
            return self.tools

        tools_response = await session.list_tools()
        tools = tools_response.tools

        return tools

    def respond_about_tools(self, tools):
        # Create a formatted message showing available tools
        tools_message = f"I have fetched {len(tools)} tools from MCP server.\n\nHere's what I can do:\n"

        for i, tool in enumerate(tools, 1):
            tool_name = tool.name
            tool_description = tool.description if hasattr(tool, 'description') else "No description available"
            tools_message += f"\n{i}. {tool_name}"
            tools_message += f"\n   Description: {tool_description}\n"

        self.env.add_reply(tools_message)

    async def run(self, messages):
        try:
            async with sse_client(f"{self.mcp_server_url}/sse") as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    tools = await self.get_mcp_tools(session)
                    formatted_tools = self.format_mcp_tools(tools)

                    try:
                        completion = self.env.completion_and_get_tools_calls(messages, tools=formatted_tools, run_tools=False)
                    except Exception as e:
                        self.env.add_reply(f"Error processing chat completion with MCP tools: {e}")
                        return

                    if completion.message:
                        self.env.add_reply(completion.message)
                    if completion.tool_calls:
                        results = await self.handle_tool_calls(session, completion)
                        print(results)
                        if results:
                            for result in results:
                                self.env.add_reply(result)
        except Exception as e:
            print(f"Error running MCP: {e}")
            print(traceback.format_exc())
            self.env.add_reply(f"Error running MCP: {e}")