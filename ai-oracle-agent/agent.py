import asyncio
import math

from nearai.agents.environment import Environment
from py_near.account import Account

import utils

CONTRACT_ID = "oracle.ai-is-near.near"


async def get_agent_data(env: Environment):
    acc = Account()
    agent_data = await acc.view_function(CONTRACT_ID, "get_agent_data",
                                         {"name": utils.get_oracle_name(env)})
    return agent_data.result.get("urls"), agent_data.result.get("prompt")


async def main(env: Environment):
    agent_urls, agent_prompt = await get_agent_data(env)
    env.add_reply(f"Loading `{agent_prompt}` from {len(agent_urls)} urls")

    responses = []
    responses_log = []
    for url in agent_urls:
        html_content = utils.fetch_page_content(url)
        if html_content:
            page_text = utils.extract_relevant_text(html_content) + "\n"

            if page_text:
                response = utils.determine_name(env, page_text, agent_prompt)
                if response:
                    president_name = response.get("response")
                    if president_name:
                        log = f"{agent_prompt} according to {url} is {president_name}"
                        env.add_reply(log)
                        responses_log.append(log)
                        responses.append(president_name)
                else:
                    env.add_reply(f"Could not determine {agent_prompt} on {url}.")
            else:
                env.add_reply(f"Failed to fetch or parse content from the website {url}.")

    # Divide the number by 2 and round it up to find the sufficient number of responses for continuation
    if len(responses) >= math.ceil(len(agent_urls) / 2):
        response_consistency_signed, messages = utils.check_consistency_with_llm(env, responses, agent_prompt)
        response_consistency = utils.parse_response(response_consistency_signed.get("response"))

        if response_consistency.get("result_found"):
            utils.prepare_app_html(env, agent_prompt, response_consistency.get("value"), responses_log, messages,
                                   response_consistency_signed.get("response"),
                                   response_consistency_signed.get("signature"),
                                   response_consistency_signed.get("public_key"))


asyncio.run(main(env))
