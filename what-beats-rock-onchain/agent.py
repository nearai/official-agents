import asyncio
import json
from typing import re

from nearai.agents.environment import Environment
from py_near.account import Account


def parse_response(response):
    try:
        print("Parsing response", response)
        parsed_response = json.loads(response)
        return parsed_response

    except Exception:
        markdown_json_match = re.match(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if markdown_json_match:
            response = markdown_json_match.group(1)

        else:
            markdown_match = re.search(r'```(.*?)```', response, re.DOTALL)
            if markdown_match:
                response = markdown_match.group(1).replace('\n', '').strip()
            else:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0).replace('\n', '').strip()
        try:
            print("Parsing response", response)
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError:
            try:
                response = response.replace(";", "")
                print("Parsing response", response)
                parsed_response = json.loads(response)
                return parsed_response
            except json.JSONDecodeError:
                try:
                    response = response.replace("json{", "{")
                    print("Parsing response", response)
                    parsed_response = json.loads(response)
                    return parsed_response
                except json.JSONDecodeError:
                    print(f"JSON decode error: {response}")
                    return {"message": "JSON decode error"}


master_account_id = globals()['env'].env_vars.get("master_account_id", None)
master_private_key = globals()['env'].env_vars.get("master_private_key", None)
contract_id = "w00.ai-is-near.near"


async def main(env: Environment):
    message = env.get_last_message()

    message_data = json.loads(message["content"])

    event = message_data.get("event")
    request_id = message_data.get("request_id")
    user_message = message_data.get("message")

    if event == "run_agent":
        acc = Account(master_account_id, master_private_key)

        agent_data = await acc.view_function(contract_id, "agent_data", {"request_id": request_id})
        agent_data = agent_data.result

        request = agent_data["request"]
        all_champions = agent_data["champions"]
        system_prompt = agent_data["prompt"]

        if not (isinstance(all_champions, list) and len(all_champions) > 0):
            env.add_reply("Illegal contract data")
        else:
            current_champion = all_champions[-1]

            if user_message in all_champions:
                await respond(env, request["data_id"], request_id, False, current_champion, False,
                              "Do not repeat others")
            else:
                result = env.completion([{"role": "system", "content": system_prompt}] +
                                        [{"role": "user", "content": json.dumps(
                                            {"guess": request["message"], "prev": current_champion})}])

                data = parse_response(result)
                reason = data.get('output', {}).get('reason', '')
                guess_wins = data.get('output', {}).get('guess_wins', False)

                verdict_text = {"won!" if guess_wins else "lost"}
                env.add_reply(f"You {verdict_text}: {reason}")

                signature = "TODO"
                await respond(env, request["data_id"], request_id, True, current_champion, guess_wins, reason,
                              signature)


async def respond(env: Environment, data_id, request_id, ok, current_champion, guess_wins, reason, signature=None):
    acc = Account(master_account_id, master_private_key)

    data = {
        "current_champion": current_champion,
        "guess_wins": guess_wins,
        "reason": reason
    }

    args = {
        "data_id": data_id,
        "request_id": request_id,
        "response": {
            "ok": ok,
            "data": json.dumps(data),
            "signature": signature,
        }
    }

    tr = await acc.function_call(contract_id, 'respond', args, 200000000000000, 0)

    env.add_reply(f"Transaction created: [{tr.transaction.hash}](https://nearblocks.io/txns/{tr.transaction.hash})")


asyncio.run(main(env))