import asyncio
import json
import random
import re

from nearai.agents.environment import Environment
from py_near.account import Account

master_account_id = globals()['env'].env_vars.get("master_account_id", None)
master_private_key = globals()['env'].env_vars.get("master_private_key", None)
contract_id = "token.raidvault.near"

def get_name(near_account):
    near_account = re.sub(r'\d+', '', near_account)  # Removes all digits
    near_account = near_account.replace('.near', '').replace('.tg', '').replace('-', '').replace('_', '')
    messages = [
        {
            "role": "system",
            "content": f"""
                Generate a character title where each word starts with the letters of the name {near_account[:8]} in order. Make it related to a specific creature, element, or fighting style that defines their combat abilities. For example, if the name is "Leo", it could be "Lethal Ethereal Overlord" suggesting a mystical beast. Make it epic and focused on combat abilities or creature characteristics
            """
        },
        {
            "role": "user",
            "content": f"My name is {near_account[:8]}. Reply with my heroic title only."
        }
    ]
    return env.completion(messages, temperature=0.9)

def get_battle(fighter1, fighter1_title, fighter2, fighter2_title):
    rounds = random.randint(2, 4)
    messages = [
        {
            "role": "system",
            "content": f"""
            Generate a dramatic battle log between 2 NEAR ACCOUNTS: {fighter1} and {fighter2}. 
                Fighter 1 title & abilities/characteristics: {fighter1_title}
                Fighter 2 title & abilities/characteristics: {fighter2_title}
                
                Include {rounds} rounds of combat where each fighter uses their specific abilities based on their title, abilities and characteristics. Make the battle flow naturally using their defined powers and make it epic and entertaining.
            
            <json-interface-RESPONSE-JSON>
            interface Response {{
                rounds: string[];
                winner_near_account: string;
                verdict: string;
            }}
            </json-interface-RESPONSE-JSON>
            
            
            <example>
            {{
                "rounds": [
                    "Round 1: sender.near unleashes a spectral strike!",
                    "Round 2: receiver.tg counters with an infernal blast!",
                    "Round 3: Both beings clash with their ultimate powers!"
                ],
                "winner_near_account": "sender.near",
                "verdict": "Through mastery of spectral powers, sender.near emerges victorious!"
            }}
            </example>
            """
        },
        {
            "role": "user",
            "content": f"Generate a dramatic battle log between {fighter1} ({fighter1_title}) and {fighter2} ({fighter2_title}). Reply with proper json formated as RESPONSE-JSON only."
        }
    ]
    return env.completion(messages)


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


async def main(env: Environment):
    message = env.get_last_message()

    message_data = parse_response(message["content"])

    event = message_data.get("event", None)
    request_id = message_data.get("request_id", None)

    # ignore hub message, we will verify it from the chain
    # ft_transfer_message = message_data.get("message")

    if request_id is not None and event == "run_agent":
        acc = Account(master_account_id, master_private_key)

        request = await acc.view_function(contract_id, "get_request", {"request_id": request_id})
        request = request.result

        if request["sender_id"] and request["receiver_id"]:
            sender = request["sender_id"]
            receiver = request["receiver_id"]
            sender_title = get_name(sender)
            receiver_title = get_name(receiver)

            env.add_reply(f"Starting a fight between {sender} ({sender_title}) and {receiver} ({receiver_title})")

            battle_data = parse_response(get_battle(sender, sender_title, receiver, receiver_title))

            battle_log = ("\n".join(battle_data['rounds'])).strip()
            message = f"{battle_data['verdict']}\n{battle_log}"
            env.add_reply(message)

            message = message.replace("\n", " ")

            if battle_data["winner_near_account"] == sender or battle_data["winner_near_account"] == receiver:
                signature = "TODO"
                await respond(env, request["data_id"], request_id, True, message, battle_data["winner_near_account"],
                              signature)
            else:
                await respond(env, request["data_id"], request_id, False, "", "",
                              "Do not repeat others")
    else:
        messages = [
            {"role": "system", "content": """You are a helpful AI Agent called `RAID AGENT`. You have your own token `token.raidvault.near` deployed to NEAR Blockchain. Here’s how it works:
            
The Basics: Every transaction triggers an AI-generated battle between the sender and the receiver. The winner gets the tokens, and the loser... well, they don’t. No refunds.

The Raid: You can raid other players who hold tokens. Attack, steal, and conquer — but be careful, because if you’re the one who loses, you pay the price!

Play with Any NEAR Wallet: You can use any wallet to play! For example, let’s say you want to send 5 RAID tokens to your buddy. If your buddy already has 5 RAID on their balance, an AI battle automatically starts. The winner takes the 5 RAID tokens — if you lose, your 5 RAID will be transferred to your buddy. But if you win, not only do you keep your 5 RAID, but you also steal 5 more RAID from your buddy! Their balance will decrease accordingly.

But if your buddy doesn’t have 5 RAID tokens in their balance, no battle happens. Instead, they’ll simply receive your 5 RAID tokens without a fight. However, this means your buddy can now participate in future raids and battles — so don’t be too generous!

The Only Way to Raid: The only way to go on a raid with RAID tokens is by sending them using NEAR wallet. No other method will work.

AI Battles: These aren't just any fights. The battles are powered by AI, making each raid unique and unpredictable. The more you raid, the more thrilling the AI fights get.

The only Rule of RAID: If you lose the battle, you pay. There are no exceptions. The AI doesn’t care about your feelings.

Ready to start raiding? Go ahead, but remember: "Win or Cry" — it’s up to you!
            """}
        ] + env.list_messages()

        reply = env.completion(messages)
        env.add_reply(reply)
        env.set_next_actor("user")


async def respond(env: Environment, data_id, request_id, ok, message, winner, signature=None):
    acc = Account(master_account_id, master_private_key)

    data = {
        "message": message,
        "winner": winner
    }

    args = {
        "data_id": data_id,
        "request_id": request_id,
        "response": {
            "ok": ok,
            "data": json.dumps(data),
            # TODO
            # "signature": signature,
        }
    }

    tr = await acc.function_call(contract_id, 'respond', args, 200000000000000, 0)

    env.add_reply(f"Transaction created: [{tr.transaction.hash}](https://nearblocks.io/txns/{tr.transaction.hash})")


asyncio.run(main(env))

