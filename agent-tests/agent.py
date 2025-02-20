# This agent performs simple tests
import json
from typing import Optional, Dict

import requests
from aitp_test_messages import request_decision, request_data, quote_with_shipping, payment_authorization, payment_result
from llm_aitp import dynamic_request_decision_test
from menu import help_menu

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



    def request_decision_test(self):
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
            case "init":
                help_menu(self.env)
            case _:
                raise ValueError(f"Unknown message type: {message_type}")

    def _process_search_results(self, search_results):
        """Default processing of search results from the google search API, returns result titles

        search_results: the search results from the google search API.
        """
        search_results = search_results["items"]
        search_results = [result["title"] for result in search_results]
        return search_results

    def _google_search(self, query):
        """Search the web to find recent information with which to answer questions.

        query: the search query containing what you want to search for.
        """
        api_key = self.env.env_vars.get("google_api_key", "")
        google_search_engine_id = "67ecbcdfba7584807" # normal google search

        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={google_search_engine_id}&q={query}"
        response = requests.get(url)
        sjson = response.json()
        return self._process_search_results(sjson)

    def tool_test(self, query):
        env = self.env
        tool_registry = env.get_tool_registry(True)
        tool_registry.register_tool(self._google_search)
        tools = tool_registry.get_all_tool_definitions()

        env.completion_and_run_tools(
            [{"role": "system", "content": "You are an assistant"},
             {"role": "user", "content": query}],
            model="llama-v3p3-70b-instruct",
            tools=tools,
        )

    def completion(self, messages):
        self.env.add_reply(self.env.completion(messages))

    def choose_test(self, user_message):
        match user_message:
            case "agent_data":
                self.agent_data_test()
            case "completion":
                self.completion([{"role": "system", "content": "What's the answer to life, the universe, and everything?"}])
            case "tool":
                self.tool_test("what is the weather in New York today?")
            case "request_decision":
                self.request_decision_test()
            case "dynamic_request_decision_test":
                dynamic_request_decision_test(self.env)
            case _:
                help_menu(self.env)

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


if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    agent.run()
