import traceback
from mcp import ClientSession
from mcp.client.sse import sse_client
import json
import requests
from prompt import request_decision_example
class ShoppingMCP:
    def __init__(self, env):
        self.env = env
        self.mcp_server_url = env.env_vars.get("MCP_SERVER_URL", "https://5770-2804-5c-518c-200-e486-7b7d-d1bf-35d3.ngrok-free.app")
        print(f"Using MCP server at {self.mcp_server_url}")
        self.session = None
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

    async def initialize(self):
        """Initialize connection to MCP server and fetch available tools."""
        try:
            async with sse_client(f"{self.mcp_server_url}/sse") as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    self.session = session
                    tools_response = await session.list_tools()
                    self.tools = tools_response.tools
                    return self.format_mcp_tools(self.tools)
        except Exception as e:
            print(f"Error initializing MCP client: {e}")
            self.env.add_reply(f"Error initializing MCP client: {e}")
            raise


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


    async def handle_tool_calls(self, session, assistant_message):
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            results = []
            for tool_call in assistant_message.tool_calls:
                print(f"Calling tool {tool_call.function.name} with arguments {tool_call.function.arguments}")
                try:
                    tool_result = await session.call_tool(
                        tool_call.function.name,
                        json.loads(tool_call.function.arguments)
                    )
                    result = await self.process_tool_result(tool_result)
                    if result:
                        results.extend(result)
                except Exception as e:
                    error_msg = f"Error executing tool {tool_call.function.name}: {e}"
                    print(error_msg)
                    results.append(error_msg)
            return results

    async def run(self, messages):
        try:
            async with sse_client(f"{self.mcp_server_url}/sse") as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()

                    try:
                        all_tools = await session.list_tools()
                        tools_description = self.format_mcp_tools(all_tools.tools)
                        completion = self.env.completion_and_get_tools_calls(messages, tools=tools_description, run_tools=False)
                        print(f"Completion received: {completion}")
                        self.env.add_system_log(f"Completion: {completion}")
                    except Exception as e:
                        error_msg = f"Error processing chat completion with MCP tools: {e}"
                        print(error_msg)
                        self.env.add_reply(error_msg)
                        return

                    if completion.message:
                        self.env.add_reply(completion.message)
                    if completion.tool_calls:
                        results = await self.handle_tool_calls(session, completion)
                        if results:
                            print(f"Results: {results}")
                            schema_url = "https://aitp.dev/capabilities/aitp-02-decisions/v1.0.0/schema.json"
                            json_schema = self.fetch_schema(schema_url)
                            # if json_schema:
                            #     request_decision_schema = self.get_request_decision_schema(json_schema)
                            #     if request_decision_schema:
                            comp = self.env.completion(
                                messages + [{"role": "user", "content": "product search results: " + str(results)}, {"role": "system", "content": """
                                    Transform the product search results into a request_decision message following these rules:

                                    1. Basic Structure:
                                       - $schema: "https://aitp.dev/v1/requests.schema.json"
                                       - request_decision object with type "products"
                                       - Generate a unique request_decision.id

                                    2. For each product in the search results, map these fields:
                                       - id: use product.code
                                       - name: use product.name
                                       - description: use product.description
                                       - image_url: use product.imageUrl ( don't omit this field )
                                       - url: use product.url
                                       - quote object:
                                         * type: "Quote"
                                         * payee_id: "foobar"
                                         * quote_id: generate unique
                                         * payment_plans: [{
                                             amount: convert product.price from "$199.00" format to number 199.00
                                             currency: "USD"
                                             plan_id: "foobar"
                                             plan_type: "one-time"
                                           }]
                                         * valid_until: "2050-01-01T00:00:00Z"

                                    3. Place each product directly in the request_decision.options array
                                    4. Do not use the variants field
                                    5. Preserve exact URLs from the input data

                                    Example product input format:
                                    {
                                      code: 'B0CZPLV566',
                                      name: 'Beats Solo 4',
                                      description: 'Wireless Headphones',
                                      url: 'https://amazon.com/dp/...',
                                      price: '$199.00',
                                      imageUrl: 'https://m.media-amazon.com/...'
                                    }
                                """}],
                                temperature=0.1,
                                response_format={"type": "json_object", "schema": json_schema}
                            )
                            print(f"Completion in tool_calls: {comp}")
                            self.env.add_reply(str(comp))
                            #     else:
                            #         self.env.add_reply("Error: Could not find request_decision schema")
                            # else:
                            #     self.env.add_reply("Error: Could not fetch schema for response formatting")
        except Exception as e:
            print(f"Error running MCP: {e}")
            print(traceback.format_exc())
            self.env.add_reply(f"Error running MCP: {e}")

    # def get_request_decision_schema(self, json_schema):
    #     # Find the schema containing request_decision from anyOf array
    #     for schema_variant in json_schema.get('anyOf', []):
    #         if 'request_decision' in schema_variant.get('properties', {}):
    #             schema_variant['properties']['$schema']['$ref'] = json_schema['$schema']
    #             return schema_variant
    #     return None