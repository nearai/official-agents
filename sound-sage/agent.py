# This agent helps users buy audio equipment.
import json
import prompt
import shopping_mcp
import products_aitp
import payments_aitp
import checkout_aitp

class Agent:
    def __init__(self, env):
        self.env = env

    def request_decision_test(self, user_message):
        env = self.env

        env.add_reply(env.completion(
            [{"role": "system", "content": prompt.PROMPT},
             {"role": "system", "content": json.dumps(prompt.example_product_data)},
             {"role": "user", "content": user_message}],
            # response_format={'type': 'json_object'}
        ))

    def run(self):
        try:
            env = self.env
            user_message = env.get_last_message()
            self.request_decision_test(user_message['content'])
        except Exception as e:
            # print stacktrace
            import traceback
            traceback.print_exc()
            self.env.add_reply(f"Error: {e}")


if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    agent.run()
