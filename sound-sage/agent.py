# This agent helps users buy audio equipment.
import json
from typing import Dict, Optional

import prompt
import shopping_mcp
import products_aitp
import payments_aitp
import checkout_aitp
from test_messages import request_decision, request_data, quote_with_shipping, payment_authorization, payment_result


class Agent:
    def __init__(self, env):
        self.env = env

    def request_decision_test(self, user_message):
        self.env.add_reply(json.dumps(request_decision))

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
            case _:
                raise ValueError(f"Unknown message type: {message_type}")

    def run(self):
        try:
            env = self.env
            user_message = env.get_last_message()['content']  # query comes in as a user message, is this what we want?
            protocol = self.detect_protocol_message(user_message)
            if protocol:
                self.route(protocol)
            else:
                self.request_decision_test(user_message)
        except Exception as e:
            # print stacktrace
            import traceback
            traceback.print_exc()
            self.env.add_reply(f"Error: {e}")


if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    agent.run()
