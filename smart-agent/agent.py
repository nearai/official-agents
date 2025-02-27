# This agent helps users buy audio equipment.
import json
from typing import Dict, Optional
from shopping_mcp import ShoppingMCP

import asyncio
from nearai.agents.environment import Environment
from state import State

STATE_FILE = "smart_agent_state.json"

presentation_prompt = f"""You are SoundSage, an AI-powered audio product recommendation agent specializing in helping users find the perfect audio equipment through intelligent, expert-level analysis. Your primary function is to provide comprehensive, nuanced recommendations for audio products available on Amazon, including headphones, speakers, earbuds, and related audio gear.
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

Obs.: If you have any tools available, use them to help the user, and also tell the user about the tools you have available - But make sure to tell what you can do in a friendly user way, and not in a technical way.
"""

class Agent:
    def __init__(self, env: Environment):
        self.env: Environment = env
        self.shopping_mcp_server = ShoppingMCP(env)
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

    async def handle_first_contact(self):
        """Handle the first interaction with the user."""
        try:
            # Initialize MCP server and get available tools
            await self.shopping_mcp_server.initialize()

            messages = [
                {"role": "system", "content": presentation_prompt},
                {"role": "user", "content": self.env.get_last_message()['content']}
            ]
            await self.shopping_mcp_server.run(messages)
        except Exception as e:
            print(f"Error in first contact: {e}")
            self.env.add_reply("I apologize, but I'm having trouble connecting to my tools. Let me try to help you without them.")

    async def handle_general_request(self):
        """Handle subsequent interactions with the user."""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that can help the user with their requests."},
                {"role": "system", "content": "If the response has a schema, format the response to be a json object following exactly the schema."},
            ] + self.env.list_messages()
            await self.shopping_mcp_server.run(messages)
        except Exception as e:
            print(f"Error in general request: {e}")
            self.env.add_reply("I encountered an error processing your request. Could you please try rephrasing it?")

    async def run(self):
        """Main execution flow."""
        try:
            if len(self.env.list_messages()) == 0:
                await self.handle_first_contact()
            else:
                await self.handle_general_request()
        except Exception as e:
            print(f"Error in agent run: {e}")
            self.env.add_reply("I apologize, but I encountered an unexpected error. Please try again.")

if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    asyncio.run(agent.run())
