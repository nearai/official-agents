# This agent helps users buy audio equipment.
import json
from typing import Dict, Optional

from shopping_mcp import ShoppingMCP
import products_aitp
import asyncio
from nearai.agents.environment import Environment
from test_messages import request_data
from state import State

STATE_FILE = "sound_sage_state.json"

user_prompt = f"""You are SoundSage, an AI-powered audio product recommendation agent specializing in helping users find the perfect audio equipment through intelligent, expert-level analysis. Your primary function is to provide comprehensive, nuanced recommendations for audio products available on Amazon, including headphones, speakers, earbuds, and related audio gear.
Core Capabilities:
  * Generate an initial, comprehensive list of product recommendations based on minimal user input.
  * Provide a multi-tiered recommendation framework with clear categories:
  * Overall Top Pick
  * Best Budget Option
  * Premium/Audiophile Selection
  * Best Upgrade
  * Specialized Use Case Recommendation
  * Stay updated on the latest audio technology and product releases
  * Maintain comprehensive database of audio product reviews, specifications, and performance metrics
  * Explain technical specifications in accessible language
  * When searching for products use keywords that will help you find the best product for the user
"""



class Agent:
    def __init__(self, env: Environment):
        self.env = env
        self.shopping_mcp_server = ShoppingMCP(env, tool_post_processor_function=self.post_process_tools)
        self.thread = self.env.get_thread()
        try:
            self.state = self.initialize_state()
        except Exception as e:
            print(f"Error initializing state: {e}")
            self.state = State()

    def initialize_state(self) -> State:
        # store data by parent thread id if it exists, otherwise use the current thread_id
        thread_id = self.thread.metadata["parent_id"] if self.thread.metadata.get("parent_id", None) else self.thread.id
        data = self.env.get_agent_data_by_key(thread_id)
        saved_state = data.get("value") if data else None
        print(f"saved_state: {saved_state}")
        if not saved_state:
            return State()
        return State.model_validate(saved_state)

    def save_state(self):
        thread_id = self.thread.metadata["parent_id"] if self.thread.metadata.get("parent_id", None) else self.thread.id
        self.env.save_agent_data(thread_id, self.state.model_dump())

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
                cart_id = self.state.cart_ids[0] if self.state.cart_ids else ""
                cart_clause = f"2. Current cart_id: {cart_id}" if cart_id else ""
                messages = [{"role": "system", "content": f"""
                              Add the following product to the cart.
                              Considerations:
                              1. Only send the productId
                              {cart_clause}
                              """},
                            {"role": "user", "content": json.dumps(protocol)}]
                await self.shopping_mcp_server.run(messages)
                self.env.add_reply(json.dumps(request_data)) # ask for shipping info

            case "data":
                # call mcp with prompt to update user data and return current cart
                cart_id = self.state.cart_ids[0] if self.state.cart_ids else ""
                messages = [
                    {"role": "system", "content": """
                       Update the user's shipping data by updating the cart buyer identity.
                       Considerations:
                       1. Make sure to send only the information provided
                       2. Send the country as a 2 letter code in the 'countryCode' field, not the full country name
                       3. Send the state as a 2 letter code in the 'provinceCode' field, not the full state name. Send only the state 2 letter state code and nothing more in the 'provinceCode' field.
                    """},
                    {"role": "user", "content": json.dumps(protocol)},
                    {"role": "system", "content": f"Current cart_id: {cart_id}"}
                ]
                await self.shopping_mcp_server.run(messages)
                # tool call post-processing produces quote response which is sent by shopping_mcp code

            case "payment_authorization":
                # call mcp with prompt to check out, pass payment authorization and cart info
                cart_id = self.state.cart_ids[0] if self.state.cart_ids else ""
                payment_authorization = protocol.get("payment_authorization")
                details = payment_authorization.get("details")[0]
                transaction_hash = details.get("transaction_id")
                sender_id = details.get("account_id")
                amountUSDC = details.get("amount")
                params = {
                    "cartId": cart_id,
                    "transactionHash": transaction_hash,
                    "senderId": sender_id,
                    "amountUSDC": amountUSDC * 1000000
                }
                result = await self.shopping_mcp_server.direct_tool_call("aitp_amazon_checkout", json.dumps(params))
                response = result[0]
                json_response = json.loads(response)
                if json_response and json_response.get("statusCode") == 200:
                    reply = self.generate_payment_result(payment_authorization, json_response.get("body"))

                    # Clear cart after successful payment
                    if json_response.get("status", "ERROR") == "COMPLETED":
                        self.state.clear_cart()
                        self.save_state()

                    self.env.add_reply(json.dumps(reply))
                else:
                    print(f"Error processing order: {json.dumps(result)} {json.dumps(payment_authorization)}")
                    reply = "Error processing order. Your funds should have been refunded. If they were not, please contact support@near.ai and include the transaction id of your payment."
                    self.env.add_reply(reply)

            case _:
                self.env.add_agent_log(f"Unknown message type: {message_type}")
                return self.handle_general_request(json.dumps(protocol))

    def generate_payment_result(self, payment_authorization, response):
        details = payment_authorization.get("details", {})[0]
        transaction_hash = details.get("transaction_id", "")
        quote_id = payment_authorization.get("quote_id", "")
        result = "success" if response.get("status", "ERROR") == "COMPLETED" else "failure"
        order_id = response.get("orderId", "No Order Id")
        return {
            "$schema": "https://aitp.dev/v1/payments.schema.json",
            "payment_result": {
                "transaction_id": transaction_hash,
                "quote_id": quote_id,
                "result": result,
                "message": f"Order id: {order_id}",
                "timestamp": payment_authorization.get("timestamp", ""),
                "details": []
            }
        }

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

    def process_cart_buyer_identity_update(self, result):
        result_dict = json.loads(result[0])
        try:
            self.state.update_shipping_address(result_dict["body"]["buyerIdentity"])
            self.save_state()
        except Exception as e:
            print("Error saving state update-shipping-address: ", e)

        product_processor = products_aitp.ProductsAITP(self.env)
        print("Generating quote response", result_dict)
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
        return [] # cart message is only for debugging, route send request for shipping info

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
        self.env.add_system_log(f"Post processing tool call: {tool_call.function.name} with result: {tool_result}")

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