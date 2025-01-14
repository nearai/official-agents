import asyncio
import json
import random
import re

import tweepy
from nearai.agents.environment import Environment
from py_near.account import Account

master_account_id = globals()['env'].env_vars.get("master_account_id", None)
master_private_key = globals()['env'].env_vars.get("master_private_key", None)
api_key = globals()['env'].env_vars.get("api_key", None)
api_secret = globals()['env'].env_vars.get("api_secret", None)
access_token = globals()['env'].env_vars.get("access_token", None)
access_secret = globals()['env'].env_vars.get("access_secret", None)

contract_id = "token.raidvault.near"
airdrop_amount = "10000000000000000000000"  # 10.000

agent_key = "RAIDers"

debug_mode = False


if env.account_id != "fastnear.near":
    exit(1)

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


async def send_tokens(env: Environment, receiver_id):
    acc = Account(master_account_id, master_private_key)

    if not debug_mode:
        transaction_hash = await acc.function_call(contract_id, 'ft_transfer',
                                                   {"receiver_id": receiver_id, "amount": str(airdrop_amount)},
                                                   40000000000000,
                                                   int(1), nowait=True)
    else:
        transaction_hash = "DDD..."

    env.add_reply(
        f"Send tokens call: Transaction created: [{transaction_hash}](https://nearblocks.io/txns/{transaction_hash})")

    return transaction_hash


def get_name(env: Environment, near_account):
    near_account = re.sub(r'\d+', '', near_account)  # Removes all digits
    near_account = near_account.replace('.near', '').replace('.tg', '').replace('-', '').replace('_', '')
    messages = [
        {
            "role": "system",
            "content": f"""
                Generate an epic character title related to a specific creature, element, or fighting style, where each word starts with the letters of the name {near_account[:8]} in order. The title should be a coherent, powerful description of the character, emphasizing their combat abilities or creature characteristics. For example, if the name is "Leo", the title could be "Lethal Ethereal Overlord", suggesting a mystical and formidable combatant. Ensure the title is a single phrase, not a list, and make it sound grand, heroic, or fearsome, fitting the theme of a warrior or mythical creature. Avoid providing a list of individual words like "C - Carnivorous" or "O - Omniscient."
            """
        },
        {
            "role": "user",
            "content": f"My name is {near_account[:8]}. Reply with my heroic title only."
        }
    ]
    return env.completion(messages, temperature=0.9)


async def send_tweet(env: Environment, receiver_id, tr_hash, tweet_id):
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )

    player_name = get_name(env, receiver_id).strip('\"\'').rstrip('.').rstrip('.!')

    welcomes = [
        "Welcome, warrior! You’ve been invited to the raid. Your title:",
        "Welcome to the raid! Your new title:",
        "Congratulations! You’re invited to the raid. Your title is now:",
        "Welcome, raid participant! Your title:",
        "Ready for the raid? Welcome! Your official title:",
        "You’ve been summoned to the raid! Here’s your title:",
        "Welcome, brave raider! Your title:",
        "It’s time to raid! Welcome, and behold your title:",
        "Raid accepted! Welcome, your title is now:",
        "You’ve been invited to the raid! Your title:"
    ]

    messages = [
        "We’ve just sent you some $RAID tokens to your_address. Get ready to raid or be raided!",
        "Your $RAID tokens are here. Check your_address. Time to take what you deserve in the raid!",
        "We’ve dropped some $RAID tokens in your wallet at your_address. Go ahead, raid or get raided!",
        "Some $RAID tokens just landed in your_address. It’s time to claim your loot!",
        "You’ve got $RAID tokens now at your_address. Ready to steal or be stolen from?",
        "We sent you $RAID tokens at your_address. The raid’s on—are you going to conquer or crumble?",
        "Your $RAID tokens have arrived at your_address. Time to take control in the raid!",
        "We’ve given you some $RAID tokens at your_address. Now go take what’s yours—or lose it!",
        "You’ve got $RAID tokens waiting at your_address. It’s a raid—win big or lose it all!",
        "$RAID tokens are in your wallet at your_address. Raid hard, or get raided!"
    ]

    message = random.choice(messages)
    message = message.replace("your_address", receiver_id)
    welcome = random.choice(welcomes)

    tweet = f"{welcome} {player_name}! {message} Tx: {tr_hash}"
    print("Sending tweet", tweet)
    try:
        if not debug_mode:
            response = client.create_tweet(text=tweet, in_reply_to_tweet_id=tweet_id)
            print(f"Tweet published! ID: {response.data['id']}")
    except tweepy.TweepyException as e:
        print(f"Tweet creation failed: {e}")


async def main(env: Environment):
    user_message = env.get_last_message(role="user")["content"]
    print("Input message", user_message)

    message_data = parse_response(user_message)
    action = message_data.get("action", None)
    replied_to = message_data.get("replied_to", [])
    user_text = message_data.get("text", "")
    tweet_id = message_data.get("tweet_id", "")

    if action != "twitter_mention":
        return False

    main_prompt = """
### Prompt for AI Agent

You are an AI assistant designed to analyze text and identify whether the user is asking to send $RAID tokens and, if so, extract the NEAR account where the tokens should be sent. Return your findings as a JSON object with two fields: `request_tokens` (boolean) and `near_account` (string or null). Follow these rules and examples to ensure accuracy:

**Rules:**
1. Identify explicit requests for RAID tokens, such as "send me RAID tokens," "transfer RAID to my account," or "can I get RAID tokens?".
2. Look for a NEAR account in the format of a string ending in `.near`, `.tg` or other valid NEAR account patterns.
3. If no NEAR account is provided, set `near_account` to `null`.
4. If the text does not request RAID tokens, set `request_tokens` to `false` and `near_account` to `null`.

**Output Format**
* Your output response must be a single JSON object ONLY that can be parsed by Python's "json.loads()". Any comments expect JSON will make your reply invalid.
* The JSON may contain these fields:
    request_tokens: bool
    near_account: String (NEAR Account Id) || null

**Examples:**

1. **Input:**
   ```
   Can you send 50 $RAID tokens to my wallet john_doe.near?
   ```
   **Output:**
   ```json
   {
       "request_tokens": true,
       "near_account": "john_doe.near"
   }
   ```

2. **Input:**
   ```
   I would like to receive some RAID tokens. My NEAR account is example.tg.
   ```
   **Output:**
   ```json
   {
       "request_tokens": true,
       "near_account": "example.tg"
   }
   ```

3. **Input:**
   ```
   Is it possible to get RAID tokens? My NEAR address: raiduser123.near.
   ```
   **Output:**
   ```json
   {
       "request_tokens": true,
       "near_account": "raiduser123.near"
   }
   ```

4. **Input:**
   ```
   Can you tell me more about RAID tokens? I don’t have a NEAR account yet.
   ```
   **Output:**
   ```json
   {
       "request_tokens": true,
       "near_account": null
   }
   ```

5. **Input:**
   ```
   Please send some tokens to my Ethereum wallet 0xabc123.
   ```
   **Output:**
   ```json
   {
       "request_tokens": true,
       "near_account": null
   }
   ```
   
6. **Input:**
   ```
   How are you?
   ```
   **Output:**
   ```json
   {
       "request_tokens": false,
       "near_account": null
   }
   ```
   
7. **Input:**
   ```
   I just registered an account my-new-account.near
   ```
   **Output:**
   ```json
   {
       "request_tokens": false,
       "near_account": "my-new-account.near"
   }
   ```

Use these examples and rules to ensure the correct output for similar inputs.
"""
    messages = [{"role": "system", "content": main_prompt},
                {"role": "user", "content": f"{user_text}. Reply with the single JSON object ONLY."}]

    reply = env.completion(messages)
    data = parse_response(reply.lower())

    is_request_tokens = "1871297260379951446" in replied_to or data.get("request_tokens", None)

    if is_request_tokens and data.get("near_account", None):
        print("We have a token request!")
        near_account = data.get("near_account")

        acc = Account(master_account_id, master_private_key)

        request = await acc.view_function(contract_id, "ft_balance_of", {"account_id": near_account})
        ft_balance = request.result

        print(f"Sending tokens to {near_account}. Current balance: {ft_balance}")
        near_account_history = env.get_agent_data_by_key(agent_key, '[]')

        near_account_list = json.loads(near_account_history["value"])

        print("Processed accounts:", near_account_list)

        # print("near_account_list", near_account_list)
        if near_account in near_account_list:
            print("Account already processed")
            return False

        if int(ft_balance) > 0:
            print("Account already has tokens")
            return False

        if "." not in near_account:
            print("Skip top level accounts")
            return False

        # insert account as processed
        near_account_list.append(near_account)
        env.save_agent_data(agent_key, json.dumps(near_account_list))

        tr_hash = await send_tokens(env, near_account)

        if tr_hash is None:
            print("Send tokens failed")
            return False

        await send_tweet(env, near_account, tr_hash, tweet_id)


asyncio.run(main(env))
