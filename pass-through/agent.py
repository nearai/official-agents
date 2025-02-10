from nearai.agents.environment import Environment

PROMPTS = {
    "test": "You are an agent that passes on information about its operating environment.",
    "process_user_intent": "",
    "process_user_focused_intent": ""
}

class Agent:

    def __init__(self, env: Environment):
        self.env = env

    # See https://docs.near.ai/agents for more information on building agents
    # See https://github.com/nearai/official-agents for examples and templates

    # Prompt should tell the agent how and when to come up with user focused intents

    def process_user_message(self):
        """Processes the user message,
        if there is no active intent decides what the user intent is, builds a plan to accomplish the intent."""
        pass


    def process_service_agent_message(self):
        """Processes the service agent message, decides how to respond to the message."""
        pass

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

    def execute_user_focused_intent(self):
        """Evaluates the capabilities of the client, decides how to effectuate the intent,
         through a tool or through a text response."""
        pass

    def update_state_json(self):
        """Writes to the state.json file, first performing validation"""
        pass

    def discovery(self):
        pass



    def run(self):
        prompt = {{"role": "system", "content": PROMPTS["test"]}}
        result = self.env.completion([prompt] + self.env.list_messages())
        self.env.add_reply(result)
        self.env.request_user_input()

if globals().get('env', None):
    agent = Agent(globals().get('env'))
    agent.run()

