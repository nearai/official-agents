import json
from typing import Optional, Dict

PROMPT = f"""Let's run some tests"""

class Agent:
    def __init__(self, env):
        self.env = env

    def run(self):
        try:
            env = self.env
            user_message = env.get_last_message()['content']
            print(f"User message: {user_message}")

            protocol = self.detect_protocol_message(user_message)
            if protocol:
                # catch decision messages
                decision = protocol.get("decision")
                print(f"decision: {decision}")
                if decision:
                    decision_id = decision.get("request_decision_id", "")
                    option_id = decision.get("options", "")[0].get("id", "")
                    if option_id.startswith("product"):
                        self.route(protocol)
                    else:
                        self.choose_test(option_id)
                else:
                    self.route(protocol)
            else:
                self.choose_test(user_message)
        except Exception as e:
            # print stacktrace
            import traceback
            traceback.print_exc()
            self.env.add_reply(f"Error: {e}")

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

    def route(self, protocol: dict):
        message_type = list(protocol.keys())[0]
        match message_type:
            case "decision":
                self.env.add_reply(json.dumps(request_data))
            case "data":
                self.env.add_reply(json.dumps(quote_with_shipping))
                pass
            case "payment_authorization":
                self.env.add_reply(json.dumps(payment_result))
            case "init":
                help_menu(self.env)
            case _:
                raise ValueError(f"Unknown message type: {message_type}")

    def completion(self, messages):
        self.env.add_reply(self.env.completion(messages))

if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    agent.run()
