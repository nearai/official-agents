
from mcp import ClientSession
from mcp.client.sse import sse_client
from nearai.agents.environment import Environment
import asyncio

class AmazonMCPServer:
    def __init__(self, env: Environment):
        self.env = env
        self.mcp_server_url = env.env_vars.get("MCP_SERVER_URL", "https://5jfjt8xpp3.us-west-2.awsapprunner.com")
        self.session = None


    async def register_mcp_tool_definitions(self):
        tool_registry = self.env.get_tool_registry(True)

        def create_tool_wrapper(tool_name, tool_description=None, tool_params=None):
            async def wrapper(**kwargs):
                """{description}

                {parameters}
                """
                try:
                    return await self.session.call_tool(tool_name, kwargs)
                except Exception as e:
                    print(f"Error calling tool {tool_name}: {e}")
                    raise

            # Format the parameters documentation
            param_docs = []
            if tool_params:
                for param_name, param_info in tool_params.items():
                    # required = "required" if param_name in tool_params.get('required', []) else "optional"
                    desc = param_info.get('description', 'No description available')
                    param_docs.append(f"{param_name.strip()}: {desc}")

            # Format and set the docstring
            wrapper.__doc__ = wrapper.__doc__.format(
                name=tool_name,
                description=tool_description or "No description available",
                parameters='\n'.join(param_docs)
            )
            wrapper.__name__ = tool_name
            return wrapper

        try:
            async with sse_client(f"{self.mcp_server_url}/sse") as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    self.session = session
                    await session.initialize()
                    tools_response = await session.list_tools()

                    for tool in tools_response.tools:
                        tool_wrapper = create_tool_wrapper(
                            tool.name,
                            tool.description if hasattr(tool, 'description') else None,
                            tool.inputSchema.get("properties", {}) if hasattr(tool, 'inputSchema') else None
                        )
                        tool_registry.register_tool(tool_wrapper)

                    return tool_registry.get_all_tool_definitions()
        except Exception as e:
            self.env.add_reply(f"Error in register_mcp_tool_definitions: {e}")
            raise