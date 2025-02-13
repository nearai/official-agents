from nearai.agents.environment import Environment, ThreadMode
from openai.types.beta import Thread

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

    def process_user_message(self, thread):
        """Processes the user message,
        if there is no active intent decides what the user intent is, build a plan to accomplish the intent."""
        prompt = {"role": "system", "content": PROMPTS["handle_user"]}
        user_message = self.env.get_last_message()["content"]
        if "headphones" in user_message:
            self.env.add_reply("Running agent: agent-tests")
            self.env.run_agent("flatirons.near", "agent-tests", "0.0.1",
                               query="request_decision", thread_mode=ThreadMode.CHILD)
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


    def detect_protocol_message(self):
        """Determines if the message is a protocol message."""
        pass

    def process_protocol_message(self):
        """Routes each type of protocol message."""
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

    def discovery(self):
        # add system message with discovery information
        pass

    def process_request_decision(self):
        # is the decision consequential/inconsequential and reversible/irreversible?
        # if it is inconsequential and reversible, and all data is available make the decision
        pass


    def run(self):
        # get thread, check whether it has a parent_id
        thread = self.env.get_thread()
        parent_id: Thread = thread.metadata.get("parent_id")
        print(f"parent_id: {parent_id}")
        if parent_id:
            self.process_service_agent_message(thread)
        else:
            self.process_user_message(thread)


if globals().get('env', None):
    agent = Agent(globals().get('env'))
    agent.run()

