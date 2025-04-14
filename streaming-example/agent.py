from nearai.agents.environment import Environment

class Agent:
    def __init__(self, env: Environment):
        self.env = env

    def run(self):
        prompt = {"role": "system", "content": "say hello in a humorous way"}
        # Pass stream=True to enable streaming of deltas
        # They will then show automatically in the UI or can be fetched at /threads/{thread_id}/stream/{run_id}
        result = self.env.completion([prompt] + self.env.list_messages(), stream=True)
        self.env.add_reply(result)
        self.env.request_user_input()

if globals().get('env', None):
    agent = Agent(globals().get('env'))
    agent.run()

