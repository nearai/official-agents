class AmazonMCPServer:
    def __init__(self, env):
        self.env = env

    def mcp_tool_definitions(self):
        # todo fetch tools
        # todo format tools
        tool_registry = self.env.get_tool_registry(True)
        # todo register MCP tools in the registry
        # tool_registry.register_tool(some_function)
        return tool_registry.get_all_tool_definitions()


