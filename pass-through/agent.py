import json
from typing import Optional, Dict

from nearai.agents.environment import Environment, ThreadMode
from openai.types.beta import Thread
from nearai.shared.models import ThreadMode, RunMode

BASE_PROMPT = "You are a helpful assistant that often calls other assistant agents to accomplish tasks for the user."
PROMPTS = {
    "handle_user":
        f"""{BASE_PROMPT}
If a user starts a new conversation (usually with a hello aitp message), tell them about your capabilities and ask them what they need help with.
""", # come up with a simple answer and also make a plan.
    "handle_agent":
        f"""{BASE_PROMPT}
This is a sub-thread, a conversation between you and an agent you have called. 
Decide whether the next step is to respond to the agent or to the user.""" # user/agent tool calls
}


class Agent:

    def __init__(self, env: Environment):
        self.env = env

    # See https://docs.near.ai/agents for more information on building agents
    # See https://github.com/nearai/official-agents for examples and templates

    # Prompt should tell the agent how and when to come up with user focused intents

    def discovery(self, user_message: str) -> Optional[str]:
        """Placeholder for discovery calls."""
        if "headphones" in user_message:
            # look up relevant agents
            # decide whether there is a relevant agent
            # store the agent as the active service agent
            # call the agent
            return "flatirons.near/sound-sage/0.0.1"
        else:
            return None

    def process_user_message(self, thread):
        """Processes the user message,
        if there is no active intent decides what the user intent is, build a plan to accomplish the intent."""
        prompt = {"role": "system", "content": PROMPTS["handle_user"]}
        user_message = self.env.get_last_message()["content"]
        selected_agent = self.discovery(user_message)
        if selected_agent:
            self.env.add_reply("Running agent: agent-tests")
            self.env.run_agent(selected_agent, query=user_message, thread_mode=ThreadMode.CHILD, run_mode=RunMode.WITH_CALLBACK)
            self.env.request_agent_input()
        else:
            result = self.env.completion([prompt] + self.env.list_messages())
            self.env.add_reply(result)
            self.env.request_user_input()

    def process_service_agent_message(self, subthread):
        """Processes the service agent message, decides how to respond to the message."""
        prompt = {"role": "system", "content": PROMPTS["handle_agent"]}
        parent_thread = subthread.metadata.get("parent_id")
        agent_to_agent_conversation = self.env.list_messages() # subthread messages
        print(f"agent_to_agent_conversation: {agent_to_agent_conversation}")
        last_message = agent_to_agent_conversation[-1]
        if not last_message or not last_message.get("content"):
            self.env.add_reply("Sorry, something went wrong. Conversation with Service Agent was empty.")
        # pass message through for now
        # result = self.env.completion([prompt] + agent_to_agent_conversation)
        # could add system:subthread end message here
        self.env.add_reply(last_message.get("content"), thread_id=parent_thread)
        self.env.request_user_input()


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

    def process_user_protocol_message(self, message: dict):
        """Routes each type of protocol message expected by a user."""
        keys = message.keys()
        if "decision" in keys:
            pass
        elif "data" in keys:
            pass

    def pass_message_to_service_agent(self, message: dict):
        """Passes the message to the service agent."""
        pass

    def process_service_agent_protocol_message(self, message: dict):
        """Routes each type of protocol message expected by an agent."""
        pass

    def process_protocol_data_request(self):
        """Determines whether the requested data is permitted to be shared with the service agent.
         If so, decides whether it can answer the request or if it should be passed up to the user.
         If not, decides whether to inform the user of the request (with a warning) or to choose another service agent.
        """
        pass

    @staticmethod
    def request_data_tool(fields: dict):
        """When you need one or more pieces of data from a user, you can call this tool to request them.
        fields: a json object in the format:
        Examples: shipping data

        """

    def execute_user_focused_intent(self):
        """Evaluates the capabilities of the client, decides how to effectuate the intent,
         through a tool or through a text response."""
        pass

    def update_state_json(self):
        """Writes to the state.json file, first performing validation"""
        pass

    def process_request_decision(self):
        # is the decision consequential/inconsequential and reversible/irreversible?
        # if it is inconsequential and reversible, and all data is available make the decision
        pass


    def client_capabilities(self, thread):
        """Retrieve client capabilities from the thread."""

        # todo: implement. Mocked for now
        return [
            {"$schema": "https://aitp.dev/v1/requests.schema.json" },
            {"$schema": "https://aitp.dev/v1/data.schema.json" },
            {"$schema": "https://aitp.dev/v1/payments.schema.json" }
        ]


    def run(self):
        # get thread, check whether it has a parent_id
        thread = self.env.get_thread()
        client_capabilities = self.client_capabilities(thread)

        parent_id: Thread = thread.metadata.get("parent_id")
        print(f"parent_id: {parent_id}")
        if parent_id:
            self.process_service_agent_message(thread)
        else:
            self.process_user_message(thread)


if globals().get('env', None):
    agent = Agent(globals().get('env'))
    agent.run()

