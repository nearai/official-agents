import json

def help_menu(env):
    test_choices = {
        "$schema": "https://aitp.dev/v1/requests.schema.json",
        "request_decision": {
            "id": "test_choices",
            "title": "Specify a test to run.",
            "type": "confirmation",
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
                },
                {
                    "id": "dynamic_request_decision_test",
                    "name": "llm request_decision",
                    "action": {
                        "$schema": "https://aitp.dev/v1/requests.schema.json",
                        "decision": {
                            "id": "dynamic_request_decision_test",
                        }
                    }
                }
            ]
        }}
    env.add_reply(json.dumps(test_choices))
