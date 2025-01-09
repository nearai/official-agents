# This agent performs simple tests
PROMPT = f"""Let's run some tests"""

class Agent:
    def __init__(self, env):
        self.env = env

    def agent_data_test(self):
        env = self.env
        env.save_agent_data("test_key", {"status": "test_value"})
        agent_data = env.get_agent_data()
        if agent_data:
            env.add_reply("SUCCESS: Agent data saved and retrieved successfully")
        else:
            env.add_reply("FAILURE: Agent data not saved or retrieved successfully")


    def run(self):
        env = self.env
        user_message = env.list_messages()[-1]

        match user_message["content"]:
            case "agent_data":
                self.agent_data_test()
            case _:
                env.add_reply("Specify a test to run: agent_data, ")

        env.request_user_input()

if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    agent.run()

