# This agent performs simple tests
import json

import requests

PROMPT = f"""Let's run some tests"""

request_decision_message = {"request_decision": {
    "type": "product",
    "options": [
        {
            "id": 1,
            "image_url": "https://...",
            "name": "Red Socks",
            "price": {
                "usd": 10.5
            },
            "url": "https://amazon.com/..."
        },
        {
            "id": 2,
            "image_url": "https://...",
            "name": "Blue Socks",
            "price": {
                "usd": 9
            },
            "url": "https://amazon.com/..."
        }
    ]
}
}

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

    def json_message_test(self):
        env = self.env
        env.add_reply({"json": request_decision_message})

    def encoded_json_message_test(self):
        env = self.env

        env.add_reply(json.dumps(request_decision_message))


    def request_decision(self, request_decision_json: dict):
        """When you need the user to make a choice or decision, call this tool to present the choice to the user.

        request_decision_json: products to choose between

        """
        print("Request choice tool called")
        # response = self.env.completion([
        #     {"role": "system", "content": "Convert the following product data to a request_decision message"},
        #     {"role": "user", "content": json.dumps(products)}])

        # validate the request_decision_json

        self.env.add_reply(json.dumps(request_decision_json))

    def request_decision_test(self):
        env = self.env

        prompt = """You are an agent that speaks Agent Interaction & Transaction Protocol (AITP)
            and calls tools to send messages of type: request_decision, and request_data.
            For example the following json message is a request_decision message that encodes product options:

            { "$schema": "https://aitp.dev/v1/requests.schema.json",
              "request_decision": {
                "id": "request_decision_1",
                "type": "products",
                "options": [
                  {
                    "id": "product_1",
                    "image_url": "https://...",
                    "name": "Red Socks",
                    {
                        type: 'Quote',
                        payee_id: 'foobar',
                        quote_id: 'foobar',
                        payment_plans: [
                          {
                            amount: $1,
                            currency: 'USD',
                            plan_id: 'foobar',
                            plan_type: 'one-time',
                          },
                        ],
                        valid_until: '2050-01-01T00:00:00Z',
                      }
                      "url": "https://amazon.com/..."
                  },
                  {
                    "id": "product_2",
                    "image_url": "https://...",
                    "name": "Blue Socks",
                    {
                        type: 'Quote',
                        payee_id: 'foobar',
                        quote_id: 'foobar',
                        payment_plans: [
                          {
                            amount: $2,
                            currency: 'USD',
                            plan_id: 'foobar',
                            plan_type: 'one-time',
                          },
                        ],
                        valid_until: '2050-01-01T00:00:00Z',
                      }
                      "url": "https://amazon.com/..."
                  }
                ]
              }
              
              When replying with a request_decision or request_data message, only return the json and no other text or formatting.
              """

        product_data = [
            {
              "code": "B0043P0IAK",
              "name": "",
              "description": "Scotch-Brite Zero Scratch Scrub Sponges, 6 Kitchen Sponges for Washing Dishes and Cleaning the Kitchen and Bath, Non-Scratch Sponge Safe for Non-Stick Cookware",
              "url": "https://www.amazon.com/dp/B0043P0IAK",
              "price": "$5.97",
              "imageUrl": "https://m.media-amazon.com/images/I/71fLn8-uF8L._AC_UL320_.jpg"
            },
            {
              "code": "B0CJ1NHWGX",
              "name": "",
              "description": "Scrub Daddy Color Sponges - Scratch-Free Multipurpose Dish Sponges for Kitchen, Bathroom + More - Household Cleaning Sponges Made with BPA-Free Polymer Foam (3 Count)",
              "url": "https://www.amazon.com/dp/B0CJ1NHWGX",
              "price": "$13.99",
              "imageUrl": "https://m.media-amazon.com/images/I/81a1n6xi-qL._AC_UL320_.jpg"
            },
            {
              "code": "B004IR3044",
              "name": "",
              "description": "Scotch-Brite Heavy Duty Scrub Sponges, Sponges for Cleaning Kitchen and Household, Heavy Duty Sponges Safe for Non-Coated Cookware, 6 Scrubbing Sponges",
              "url": "https://www.amazon.com/dp/B004IR3044",
              "price": "$5.97",
              "imageUrl": "https://m.media-amazon.com/images/I/81X7J+sBI9L._AC_UL320_.jpg"
            }]

        # Real usage would check client capabilities to decide whether to register the tool
        tool_registry = env.get_tool_registry(True)
        # tool_registry.register_tool(self.request_decision)
        # tools = tool_registry.get_all_tool_definitions()
        # print(f"Tools: {tools}")


        result = env.completion(
            [{"role": "system", "content": prompt},
             {"role": "system", "content": json.dumps(product_data)},
             {"role": "user", "content": "what product choices do I have?"}],
        )
        # tools=tools,
        # response_format={"type": "json_object"}  #should work according to Fireworks docs but is throwing 400

        env.add_reply(result)


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

    def run(self):
        try:
            env = self.env
            user_message = env.get_last_message()

            print(f"User message: {user_message}")
            match user_message["content"]:
                case "agent_data":
                    self.agent_data_test()
                case "json_message":
                    self.encoded_json_message_test()
                case "completion":
                    self.completion([{"role": "system", "content": "What's the answer to life, the universe, and everything?"}])
                case "tool":
                    self.tool_test("what is the weather in New York today?")
                case "request_decision":
                    self.request_decision_test()
                case _:
                    test_choices = {
                        "$schema": "https://aitp.dev/v1/requests.schema.json",
                        "request_decision": {
                            "options": [
                                {
                                    "id": "agent_data",
                                    "name": "agent_data",
                                    "action": {
                                        "$schema": "https://aitp.dev/v1/requests.schema.json",
                                        "decision": {
                                            "id": "agent_data",
                                        }
                                    }
                                },
                                {
                                    "id": "completion",
                                    "name": "completion",
                                    "action": {
                                        "$schema": "https://aitp.dev/v1/requests.schema.json",
                                        "decision": {
                                            "id": "completion",
                                        }
                                    }
                                },
                                {
                                    "id": "tool",
                                    "name": "tool",
                                    "action": {
                                        "$schema": "https://aitp.dev/v1/requests.schema.json",
                                        "decision": {
                                            "id": "tool",
                                        }
                                    }
                                },
                                {
                                    "id": "request_decision",
                                    "name": "request_decision",
                                    "action": {
                                        "$schema": "https://aitp.dev/v1/requests.schema.json",
                                        "decision": {
                                            "id": "request_decision",
                                        }
                                    }
                                }
                            ]
                        }}
                    env.add_reply("Specify a test to run.")
                    env.add_reply(json.dumps(test_choices))
        except Exception as e:
            # print stacktrace
            import traceback
            traceback.print_exc()
            self.env.add_reply(f"Error: {e}")


if globals().get('env', None):
    agent = Agent(globals().get('env', {}))
    agent.run()
