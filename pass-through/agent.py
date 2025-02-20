import json
from typing import Optional, Dict, Union

from nearai.agents.environment import Environment, ThreadMode
from openai.types.beta import Thread
from nearai.shared.models import ThreadMode, RunMode
from discovery import chat_with_vector_store

BASE_PROMPT = "You are a helpful assistant that often calls other assistant agents to accomplish tasks for the user."
PROMPTS = {
    # Prompt should tell the agent how and when to come up with user focused intents
    # if there is no active intent decides what the user intent is,
    #   come up with a simple answer
    #   build a plan to accomplish the intent.
    "handle_user":
        f"""{BASE_PROMPT}
If asked about your capabilities or given a simple greeting or help message, tell the user about some of the example 
tasks you can help with: planning travel, shopping for products, planning recipes, swapping crypto-currencies, and 
using NEAR Protocol.

If asked a more specific question, respond with both a short answer and a longer answer.
If asked to accomplish a task, respond with both a short answer and with a plan to accomplish the user's intent.
""",

    "handle_agent":
        f"""{BASE_PROMPT}
This is a sub-thread, a conversation between you and an agent you have called. 
Decide whether the next step is to respond to the agent or to the user.""" # user/agent tool calls
}


class Agent:
    """Pass-through agent hands off to other agents based on user input.
       Stores thread state via agent data:
           "thread_12345": {"selected_agent": "flatirons.near/sound-sage/0.0.1"}
    """
    def __init__(self, env: Environment):
        self.env = env
        self.discovery_vector_store_id = env.env_vars.get("discovery_vector_store_id", "vs_37babdabe471438391ed66dd")


    def discovery(self, user_message: str) -> Optional[dict]:
        """Attempt to find a useful agent to handle the user's message.
        user_message: the user's message
        """
        # vs_id = "vs_a0e2798f3f67434eb15ac297" #local    # prod"vs_37babdabe471438391ed66dd"
        result = chat_with_vector_store(self.env, self.discovery_vector_store_id, user_message)
        print(result)
        agent_url = result.get("agent_url")
        if agent_url:
            return result
        else:
            return None

    def process_user_message(self, thread):
        """Processes the user message"""
        user_message = self.env.get_last_message()["content"]
        protocol_message = self.detect_protocol_message(user_message)
        thread_data = self.env.get_agent_data_by_key(thread.id)
        thread_data_value = thread_data.get("value") if thread_data else None
        active_service_agent = thread_data_value.get("active_service_agent") if thread_data_value else None
        if protocol_message and active_service_agent:
            self.process_user_protocol_message(protocol_message, active_service_agent)
        else:
            selected_agent = self.discovery(user_message)

            if selected_agent:
                selected_agent_id = selected_agent["agent_url"]
                self.env.save_agent_data(thread.id, {"active_service_agent": selected_agent_id})
                self.env.add_agent_log(f"Handing off to agent: {selected_agent_id}")
                self.env.run_agent(selected_agent_id, query=selected_agent["message"], thread_mode=ThreadMode.CHILD, run_mode=RunMode.WITH_CALLBACK)
                self.env.request_agent_input()
            else:
                self.env.save_agent_data(thread.id, {"active_service_agent": ""})
                print("No service agent found.")
                prompt = {"role": "system", "content": PROMPTS["handle_user"]}
                result = self.env.completion([prompt] + self.env.list_messages())
                self.env.add_reply(result)
                self.env.request_user_input()

    def process_service_agent_message(self, subthread):
        """Processes the service agent message, decides how to respond to the message."""
        # prompt = {"role": "system", "content": PROMPTS["handle_agent"]}
        parent_thread = subthread.metadata.get("parent_id")
        agent_to_agent_conversation = self.env.list_messages() # subthread messages
        last_message = agent_to_agent_conversation[-1]
        if not last_message or not last_message.get("content"):
            self.env.add_reply("Sorry, something went wrong. Conversation with Service Agent was empty.")

        protocol_message = self.detect_protocol_message(last_message)
        if protocol_message:
            self.process_service_agent_protocol_message(protocol_message, parent_thread)
        else:
            self.process_general_service_agent_message(last_message["content"], parent_thread)


    def detect_protocol_message(self, message: Union[str,dict]) -> Optional[Dict]:
        """Determines if the message is an AITP protocol message."""
        # if the message is json and has a json $schema key starting with "https://aitp.dev" then it is a protocol message
        # in that case, return all keys other than the $schema key
        if isinstance(message, str):
            if message.startswith("{") and message.endswith("}"):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    return None
            else:
                return None
        if message.get("$schema") and message["$schema"].startswith("https://aitp.dev"):
            return message
        return None

    def process_user_protocol_message(self, message: dict, active_service_agent: str):
        """Routes each type of protocol message expected by a client."""
        keys = message.keys()
        if "$schema" in keys:
            pass # ignore the schema declaration
        if "decision" in keys:
            pass
        elif "data" in keys:
            pass
        self.env.add_agent_log(f"Handing off to active agent: {active_service_agent}")
        self.env.run_agent(active_service_agent, query=json.dumps(message), thread_mode=ThreadMode.CHILD, run_mode=RunMode.WITH_CALLBACK)
        self.env.request_agent_input()

    def process_general_service_agent_message(self, last_message_text, parent_thread):
        self.env.add_reply(last_message_text, thread_id=parent_thread)
        self.env.request_user_input()


    def process_service_agent_protocol_message(self, protocol_message: dict, parent_thread):
        """Routes each type of protocol message expected by an agent."""
        keys = protocol_message.keys()
        if "$schema" in keys:
            pass # ignore the schema declaration
        if "request_decision" in keys:
            pass # process_request_decision
        elif "request_data" in keys:
            pass # process_protocol_data_request
        elif "quote" in keys:
            pass # todo implement. decide whether to approve purchase or surface to user
        elif "payment_result" in keys:
            pass # todo implement. store in user memory
        self.env.add_reply(json.dumps(protocol_message), thread_id=parent_thread)
        self.env.request_user_input()


    # todo: implement.
    def process_protocol_data_request(self):
        """Determines whether the requested data is permitted to be shared with the service agent.
         If so, decides whether it can answer the request or if it should be passed up to the user.
         If not, decides whether to inform the user of the request (with a warning) or to choose another service agent.
        """
        pass

    # todo: implement.
    @staticmethod
    def request_data_tool(fields: dict):
        """When you need one or more pieces of data from a user, you can call this tool to request them.
        fields: a json object in the format:
        Examples: shipping data

        """

    # todo: implement, maybe
    def execute_user_focused_intent(self):
        """Evaluates the capabilities of the client, decides how to effectuate the intent,
         through a tool or through a text response."""
        pass

    # todo: implement.
    def update_state_json(self):
        """Writes to the state.json file, first performing validation"""
        # write shopping cart data to state.json
        pass

    # todo: implement.
    def process_request_decision(self):
        # is the decision consequential/inconsequential and reversible/irreversible?
        # if it is inconsequential and reversible, and all data is available make the decision
        pass


    # todo: implement. Mocked for now
    def client_capabilities(self, thread):
        """Retrieve client capabilities from the thread."""

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

