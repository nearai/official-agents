# This agent helps users buy audio equipment.
import json
from typing import Dict, Optional

from prompt import user_prompt
from shopping_mcp import ShoppingMCP
import products_aitp
import payments_aitp
import checkout_aitp
import asyncio
from nearai.agents.environment import Environment
from test_messages import request_decision, request_data, quote_with_shipping, payment_authorization, payment_result


class Agent:
    def __init__(self, env: Environment):
        self.env = env
        self.shopping_mcp_server = ShoppingMCP(env, tool_post_processor_function=self.post_process_tools)

    def request_decision_test(self, user_message):
        self.env.add_reply(json.dumps(request_decision))

    def detect_protocol_message(self, message: str) -> Optional[Dict]:
        """Determines if the message is an AITP protocol message."""
        # if the message is json and has a json $schema key starting with "https://aitp.dev" then it is a protocol message
        # in that case, return all keys other than the $schema key
        if message.startswith("{") and message.endswith("}"):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                return None
            if message.get("$schema") and message["$schema"].startswith("https://aitp.dev"):
                return {k: v for k, v in message.items() if k != "$schema"}
        return None

    async def route(self, protocol: dict):
        message_type = list(protocol.keys())[0]
        match message_type:
            case "decision":
                # call mcp with prompt to add to cart, pass decision
                messages = [{"role": "system", "content": "Add the following product to the cart"},
                            {"role": "user", "content": json.dumps(protocol)}]
                result = await self.shopping_mcp_server.run(messages)
                print(result)
                self.env.add_reply(json.dumps(request_data))
            case "data":
                # call mcp with prompt to update user data, pass data
                # todo: call mcp with prompt to return cart
                messages = [{"role": "system", "content": "Update the user's shipping data"},
                            {"role": "user", "content": json.dumps(protocol)}]
                result = await self.shopping_mcp_server.run(messages)
                print(result)
                self.env.add_reply(json.dumps(quote_with_shipping))
                pass
            case "payment_authorization":
                # call mcp with prompt to check out, pass payment authorization
                messages = [{"role": "system", "content": "Checkout with the following payment authorization"},
                            {"role": "user", "content": json.dumps(protocol)}]
                result = await self.shopping_mcp_server.run(messages)
                print(result)
                self.env.add_reply(json.dumps(payment_result))
            case _:
                self.env.add_agent_log(f"Unknown message type: {message_type}")
                return self.handle_general_request(json.dumps(protocol))

    def process_search_results(self, search_results):
        product_processor = products_aitp.ProductsAITP(self.env)
        aitp_request_decision = product_processor.generate_request_decision(search_results)
        return aitp_request_decision

        # future implementation
        # pass search_results to llm call to narrow them down and make recommendations.
        # Output should be recommendation text and reduced list
        # Convert list to aitp request decision format
        # validate that original (pre-LLM) product data matches data in AITP message
        # process_search_results should return both messages in the array. Or can use request_decision title & description


    def post_process_tools(self, tool_call, tool_result):
        # aitp_amazon_search
        # Description: Search for Amazon products by keyword
        #
        # aitp_amazon_add_to_cart
        # Description: Add a product to the cart
        #
        # aitp_amazon_checkout
        # Description: Amazon checkout - purchase all items in your cart
        #
        # aitp_amazon_cancel_order
        # Description: Cancel an order for a product on Amazon
        #
        # aitp_check_account_balance
        # Description: Check the USDC balance of a NEAR wallet
        #
        # check_usdc_balance
        # Description: Check the USDC balance of a NEAR wallet
        #
        # aitp_amazon_update_cart_buyer_identity
        # Description: Update cart buyer identity with shipping details
        #
        # aitp_amazon_get_cart_details
        # Description: Get details for a specific cart
        #
        print(f"Post processing Tool call: {tool_call.function.name}")
        match tool_call.function.name:
            case "aitp_amazon_search":
                return self.process_search_results(tool_result)
            case _:
                return tool_result

    async def handle_general_request(self, user_message):
        messages = [{"role": "system", "content": user_prompt},
                    {"role": "user", "content": user_message}]
        return await self.shopping_mcp_server.run(messages)

    async def run(self):
        env = self.env
        user_message = env.get_last_message()['content']
        protocol = self.detect_protocol_message(user_message)
        if protocol:
            await self.route(protocol)
        else:
            await self.handle_general_request(user_message)


if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    asyncio.run(agent.run())