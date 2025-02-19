from mcp import ClientSession
from mcp.client.sse import sse_client

import json
class ShoppingMCP:
    def __init__(self, env):
        self.env = env
        self.mcp_server_url = env.env_vars.get("MCP_SERVER_URL", "https://5jfjt8xpp3.us-west-2.awsapprunner.com")
        self.session = None
        self.tools = []

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

    def create_chat_messages(self):
        return [
            {
                "role": "system",
                "content": "You are a helpful assistant that can use various tools to help users interact. Format the tools response and answer the user's question accordingly and in a concise manner."
            }
        ] + [self.env.get_last_message()]

    async def process_tool_result(self, tool_result):
        if not tool_result or not hasattr(tool_result, 'content'):
            self.env.add_reply("No content received from tool")
            return

        for content in tool_result.content:
            if content.type != 'text':
                continue

            try:
                result_json = json.loads(content.text)
                self.env.add_reply(json.dumps(result_json, indent=2))
            except json.JSONDecodeError:
                self.env.add_reply(content.text)


    async def handle_tool_calls(self, session, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_result = await session.call_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                await self.process_tool_result( tool_result)

    async def get_mcp_tools(self, session):
        if len(self.tools):
            return self.tools

        tools_response = await session.list_tools()
        tools = tools_response.tools

        # Create a formatted message showing available tools
        tools_message = f"I have fetched {len(tools)} tools from MCP server.\n\nHere's what I can do:\n"

        for i, tool in enumerate(tools, 1):
            tool_name = tool.name
            tool_description = tool.description if hasattr(tool, 'description') else "No description available"
            tools_message += f"\n{i}. {tool_name}"
            tools_message += f"\n   Description: {tool_description}\n"

        self.env.add_reply(tools_message)
        return tools

    async def run(self):
        try:
            self.env.add_reply("Connecting MCP Client to MCP Server...")
            async with sse_client(f"{self.mcp_server_url}/sse") as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()

                    tools = await self.get_mcp_tools(session)
                    formatted_tools = self.format_mcp_tools(tools)

                    messages = self.create_chat_messages()
                    try:
                        completion = self.env.completion_and_get_tools_calls(messages, tools=formatted_tools, run_tools=False)
                    except Exception as e:
                        self.env.add_reply(f"Error processing chat completion: {e}")
                        return


                    if completion.message:
                        self.env.add_reply(completion.message)
                    if completion.tool_calls:
                        await self.handle_tool_calls(session, completion)
        except Exception as e:
            print(e)
            self.env.add_reply("Error connecting to MCP server")
            self.env.add_reply(f"Error connecting to MCP server: {e}")