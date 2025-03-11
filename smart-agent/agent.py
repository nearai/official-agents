import asyncio
from nearai.agents.environment import Environment

from aitp import Aitp
from state import State

presentation_prompt = f"""You are Smart Agent.

If you have any tools available, use them to help the user, and also tell the user about the tools you have available - But make sure to tell what you can do in a friendly user way, and not in a technical way.
"""

class Agent:
    def __init__(self, env: Environment):
        self.env: Environment = env
        self.aitp = Aitp(env)
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
        if not saved_state:
            return State()
        return State.model_validate(saved_state)

    def save_state(self):
        thread_id = self.thread.metadata["parent_id"] if self.thread.metadata.get("parent_id", None) else self.thread.id
        self.env.save_agent_data(thread_id, self.state.model_dump())

    async def handle_first_contact(self):
        """Handle the first interaction with the user."""
        try:
            messages = [
                {"role": "system", "content": presentation_prompt},
                {"role": "user", "content": self.env.get_last_message()['content']}
            ]
            await self.aitp.run(messages)
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
            await self.aitp.run(messages, self.state, self.save_state)
        except Exception as e:
            print(f"Error in general request: {e}")
            self.env.add_reply("I encountered an error processing your request. Could you please try rephrasing it?")
            raise e

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
            raise e

if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    asyncio.run(agent.run())
