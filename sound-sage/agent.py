# This agent helps users buy audio equipment.
import json
from typing import Dict, Optional
import datetime

from prompt import user_prompt
from shopping_mcp import ShoppingMCP
import products_aitp
import payments_aitp
import checkout_aitp
import asyncio
from nearai.agents.environment import Environment
from test_messages import request_decision, request_data, quote_with_shipping, payment_authorization, payment_result
from state import State

STATE_FILE = "sound_sage_state.json"

class Agent:
    def __init__(self, env: Environment):
        self.env = env
        self.shopping_mcp_server = ShoppingMCP(env, tool_post_processor_function=self.post_process_tools)
        self.state = self.initialize_state()

    def initialize_state(self) -> State:
        state_file = self.env.read_file(STATE_FILE)
        if not state_file:
            return State()
        return State.model_validate_json(state_file)

    def save_state(self):
        self.env.write_file(STATE_FILE, self.state.model_dump_json())

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
                messages = [{"role": "system", "content": """
                              Add the following product to the cart.
                              Considerations:
                              1. Only send the productId
                              """},
                            {"role": "user", "content": json.dumps(protocol)}]
                result = await self.shopping_mcp_server.run(messages)
                print(result)
                self.env.add_reply(json.dumps(request_data))

            case "data":
                # call mcp with prompt to update user data and return current cart
                messages = [
                    {"role": "system", "content": """
                       Update the user's shipping data
                       Considerations:
                       1. Make sure to send only the information provided
                       2. Send the country as a 2 letter code in the 'countryCode' field, not the full country name
                    """},
                    {"role": "user", "content": json.dumps(protocol)},
                    {"role": "system", "content": f"Current cart IDs: {self.state.cart_ids}"}
                ]
                result = await self.shopping_mcp_server.run(messages)

            case "payment_authorization":
                # call mcp with prompt to check out, pass payment authorization and cart info
                messages = [
                    {"role": "system", "content": "Checkout with the following payment authorization"},
                    {"role": "user", "content": json.dumps(protocol)},
                    {"role": "system", "content": f"Cart IDs to process: {self.state.cart_ids}, Total amount: {self.state.total_amount}"}
                ]
                result = await self.shopping_mcp_server.run(messages)

                # Clear cart after successful payment
                if result and getattr(result, 'success', False):
                    self.state.clear_cart()
                    self.save_state()

                self.env.add_reply(json.dumps(payment_result))

            case _:
                self.env.add_agent_log(f"Unknown message type: {message_type}")
                return self.handle_general_request(json.dumps(protocol))

    def process_search_results(self, search_results):
        product_processor = products_aitp.ProductsAITP(self.env)
        print(f"Processing search results: {search_results}")
        aitp_request_decision = product_processor.generate_request_decision(search_results)
        return aitp_request_decision

        # future implementation
        # pass search_results to llm call to narrow them down and make recommendations.
        # Output should be recommendation text and reduced list
        # Convert list to aitp request decision format
        # validate that original (pre-LLM) product data matches data in AITP message
        # process_search_results should return both messages in the array. Or can use request_decision title & description

    def process_cart_buyer_identity_update(self, result):
        result_dict = json.loads(result[0])
        try:
            self.state.update_shipping_address(result_dict["body"]["buyerIdentity"])
            self.save_state()
        except Exception as e:
            print("Error saving state update-shipping-address: ", e)

        product_processor = products_aitp.ProductsAITP(self.env)
        return product_processor.generate_quote_response(result_dict)

    def process_add_to_cart(self, result):
        result_dict = json.loads(result[0])
        try:
            if result_dict.get("body", {}).get("cartId"):
                self.state.add_to_cart(
                    result_dict["body"]["cartId"],
                    result_dict["body"]["totalPrice"]
                )
                self.save_state()
        except Exception as e:
            print("Error saving state add-to-cart: ", e)
        return result

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
            case "aitp_amazon_add_to_cart":
                return self.process_add_to_cart(tool_result)
            case "aitp_amazon_update_cart_buyer_identity":
                return self.process_cart_buyer_identity_update(tool_result)
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