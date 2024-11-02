from functools import partial

import tool_library
from prompts import main_prompt, categories_prompt, suggestions_prompt
from mock_memory import get_preferences
from template_output import TemplateOutput

MODEL = "qwen2p5-72b-instruct"



class Agent:

    def __init__(self, env):
        self.nearai_agent_client = env
        self.tool_result = None
        self.PRODUCT_VECTOR_STORE_ID = "vs_cd16bdf23124480faabd9bff" # local, but not implemented
        self.google_api_key = env.env_vars.get("google_api_key", "")
        self.rapidapi_key = env.env_vars.get("rapidapi_key", "")
        self.test_mode = env.env_vars.get("test_mode", True)
        if isinstance(self.test_mode, str) and self.test_mode.lower() == "False".lower():
            self.test_mode = False
        else:
            self.test_mode = bool(self.test_mode)


    def get_last_search_term(self, chat_history):
        for message in reversed(chat_history):
            if message['role'] == 'user':
                return message['content']
        return ''

    def process_products(self, products):
        self.nearai_agent_client.add_system_log(f"process_products callback")
        self.tool_result = products

    def run(self):

        chat_history = self.nearai_agent_client.list_messages()
        tool_registry = self.nearai_agent_client.get_tool_registry(True)

        # query_products is not yet used
        query_products = partial(self.nearai_agent_client.query_vector_store, self.PRODUCT_VECTOR_STORE_ID)

        tools = tool_library.CommonTools(query_products, self.google_api_key, self.rapidapi_key,
                                         process_product_results_function=self.process_products,
                                         test_mode=self.test_mode,
                                         nearai_agent_client=self.nearai_agent_client)
        tool_registry.register_tool(tools.product_search)
        tools = tool_registry.get_all_tool_definitions()

        last_search_term = self.get_last_search_term(chat_history)
        template_output = TemplateOutput(self.nearai_agent_client)
        user_query = f"## Search for '{last_search_term}'\n"

        # First call - use the product search tool to find products
        llm_response = self.nearai_agent_client.completion_and_run_tools(
            [{"role": "user", "content": main_prompt+user_query}],
            tools=tools,
            model=MODEL,
            agent_role_name="assistant",
            add_responses_to_messages=False)

        # Format the LLM response
        chat_message = llm_response.split("<")[0].replace("Shopping Assistant:", "").strip()

        # The tool_result should have been set in the process_products callback
        if self.tool_result is None:
            self.nearai_agent_client.add_reply("No product results")
            self.nearai_agent_client.request_user_input()
            return
        else:
            products =self.tool_result

        suggestions_enabled = True
        suggestion = ""

        if suggestions_enabled:
            suggestion_system_prompt = {"role": "system", "content": suggestions_prompt}
            options = '\n'.join(f"{i+1}. {item['title']}" for i, item in enumerate(products))
            suggestion_user_prompt_inp = f"""# Search:
        {last_search_term}
        {"Test mode results return only NEAR shirts." if self.test_mode else ""}
        ## Options:
        {options}
        ## Chat Message:
        {chat_message}
        ## Suggestion"""

            suggestion_user_prompt = {"role": "user", "content": suggestion_user_prompt_inp}
            suggestion = self.nearai_agent_client.completion([suggestion_system_prompt, suggestion_user_prompt], model=MODEL)

        template_output.handle_llm_response(products, last_search_term, chat_message, suggestion)
        self.nearai_agent_client.request_user_input()

agent = Agent(env)
agent.run()
