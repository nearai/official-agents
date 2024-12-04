from functools import partial
from typing import List, Dict, Any

import common_tool_definitions

nearai_agent_client = globals()['env']

AGENT_NAME = 'common_tool_library'
MODEL='llama-v3p2-3b-instruct' # explicitly set llama model to trigger llama tool calling

FABRIC_PROMPTS_VECTOR_STORE_ID = "vs_eede93d96fc9461b8fad5b11"
OPENAPI_DIRECTORY_VECTOR_STORE_ID = "vs_c8166130e69e488e90163e06"
google_api_key = nearai_agent_client.env_vars.get("google_api_key", "")

PROMPT = """
As a general purpose agent you can respond in four ways:
1. With helpful information about what prompts are available in the prompt library.
2. By finding and using a prompt from the library that is relevant to the user's query.
   The prompts are not Tools, they are used by calling the prompt_search tool.
3. By asking the user for more information needed to use the prompt.
4. By performing a web search to find recent information with which to answer questions.
"""


def check_for_stop_conditions(chat_history, client):
    if len(chat_history) == 0:
        return True

    # if the last two messages are the same, stop and get input from the user
    agent_messages = [msg for msg in chat_history if msg['role'] == AGENT_NAME]
    if len(agent_messages) > 2 and chat_history[-1]['content'] == chat_history[-2]['content']:
        client.add_message("nearai", "Assistant needs more information to continue.")
        return True

    return False

def recent_prompt_library_usage(chat_history):
    agent_messages = [msg for msg in chat_history if msg['role'] == AGENT_NAME]
    for i in range(1, 3):
        if len(agent_messages) >= i:
            if "I found a relevant prompt" in agent_messages[-i]['content']:
                return True
    return False

class Library:
    def __init__(
            self,
            client,
            tools_without_prompt_search: str,
            tool_registry):
        self.client = client
        self.tools_without_prompt_search = tools_without_prompt_search
        self.tool_registry = tool_registry


    def prompt_search(self, task):
        """Search the common tool library for prompts that are useful for accomplishing the user's task .

        task: the search query containing what you want to search for.
        """
        fabric_prompt_results = self.client.query_vector_store(FABRIC_PROMPTS_VECTOR_STORE_ID, task, True)
        top_result = fabric_prompt_results[0]
        relevance = top_result["distance"]
        library_prompt = top_result["file_content"]

        if relevance < 0.5: # arbitrary threshold
            self.client.add_message(AGENT_NAME, "I couldn't find a relevant prompt. Let me try to help you.")

            self.client.completion_and_run_tools(
                [{"role": "system", "content": PROMPT}] + chat_history,
                tools=self.tools_without_prompt_search,
                agent_role_name=AGENT_NAME)
        else:
            self.client.add_message(AGENT_NAME, "I found a relevant prompt. Let me use it to help you.")
            chat_response = self.client.completion(
                [{"role": "system", "content": library_prompt}, {"role": "user", "content": task}],
                model=MODEL)
            self.client.add_message(AGENT_NAME, chat_response)

    def api_search(self, task):
        """Search the common tool library for APIs that are useful for accomplishing the user's task .

        task: the search query containing what you want to search for.
        """
        api_results = self.client.query_vector_store(OPENAPI_DIRECTORY_VECTOR_STORE_ID, task, True)
        top_result = api_results[0]
        relevance = top_result["distance"]
        library_api_signature = top_result["file_content"]

        if relevance < 0.5:
            self.client.add_message(AGENT_NAME, "I couldn't find a relevant api.")
            return False # ????  maybe a prompt_and_api_search tool that coordinates the two
        else:
            self.client.add_message(AGENT_NAME, "I found a relevant api. Using APIs isn't implemented yet, I'll print the openapi spec for now.")
            self.client.add_message(AGENT_NAME, library_api_signature)


            # todo resume writing this function

            # # get the url from the api signature
            #
            # self.client.add_message(AGENT_NAME, "I found a relevant api. Let me use it to help you.")
            # api_prompt = f"""Given the following api definition, generate the json parameters to pass to the api to
            # accomplish the user's task. Respond only with the json to pass to the api in the body of a request.
            # User's Task:
            # {task}
            # API Definition:
            # {library_api_signature}
            # """
            # response = self.client.completion(
            #     [{"role": "system", "content": api_prompt}],
            #     model=MODEL,
            #     response_format={ "type": "json_object" }
            # )
            #
            # # # dynamically create a function that calls the api, use the chunk as what is passed as the tool definition
            # # api_function = lambda *x: common_tool_definitions.api_call(library_api_signature.url, x)
            # # tool_registry.register_tool(library_api_signature, library_api_signature)



chat_history = nearai_agent_client.list_messages()
tool_registry = nearai_agent_client.get_tool_registry(True)
# tool_registry.register_tool(nearai_agent_client.request_user_input)

query_prompt_library = partial(nearai_agent_client.query_vector_store, FABRIC_PROMPTS_VECTOR_STORE_ID)

common_tools = common_tool_definitions.CommonTools(nearai_agent_client, google_api_key)
tool_registry.register_tool(common_tools.google_search)
tool_registry.register_tool(common_tools.prompt_help)
tool_registry.register_tool(common_tools.prompt_text)

prompt_library = Library(nearai_agent_client, tool_registry.get_all_tool_definitions(), tool_registry)

tool_registry.register_tool(prompt_library.prompt_search)
tool_registry.register_tool(prompt_library.api_search)
tools = tool_registry.get_all_tool_definitions()


if not check_for_stop_conditions(chat_history, nearai_agent_client):

    nearai_agent_client.completion_and_run_tools(
        [{"role": "system", "content": PROMPT}] + chat_history,
        tools=tools,
        model=MODEL,
        agent_role_name=AGENT_NAME)


    # if recent_prompt_library_usage(chat_history):
    #     chat_response = nearai_agent_client.completion_and_run_tools(
    #         chat_history,
    #         model=MODEL,
    #         tools=tools,
    #         agent_role_name=AGENT_NAME)
    #     nearai_agent_client.request_user_input()

print("requesting user input")
nearai_agent_client.request_user_input()
