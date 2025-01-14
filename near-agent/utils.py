import enum
import json
import re
from decimal import Decimal, getcontext, ROUND_DOWN

import base58
import ed25519
import requests
from nearai.agents.environment import Environment
from py_near.account import Account
from py_near.dapps.core import NEAR

STATE_FILE = "state.json"


def convert_from_decimals_to_string(number: float, decimals: int, round_digits: int = 6) -> str:
    getcontext().prec = decimals + 20
    decimal_number = Decimal(number)
    scaled_number = decimal_number / Decimal(10) ** decimals
    rounded_number = scaled_number.quantize(Decimal('1.' + '0' * round_digits), rounding=ROUND_DOWN)

    return str(rounded_number)


class State:
    def __init__(self, **entries):
        self.action = ""
        self.amount = None
        self.receiver_id = None

        self.all_available_tokens = None

        self.__dict__.update(entries)

    def to_dict(self):
        return {k: (v.name if isinstance(v, enum.Enum) else v) for k, v in self.__dict__.items()}

    def to_json(self):
        return json.dumps(self.to_dict())

    def remove_attribute(self, key):
        if key in self.__dict__:
            del self.__dict__[key]  # Use del to remove the attribute
        else:
            print(f"Attribute '{key}' not found in State.")


class AiUtils(object):
    def __init__(self, _env: Environment, _agent):
        self.env = _env
        self.agent = _agent

    def get_account_id(self, public_key):
        url = f"https://api.fastnear.com/v0/public_key/{public_key}"
        response = requests.get(url)
        response.raise_for_status()
        content = response.json()
        account_ids = content.get("account_ids", [])

        if len(account_ids):
            return account_ids[0]
        else:
            return None

    def get_public_key(self, extended_private_key):
        private_key_base58 = extended_private_key.replace("ed25519:", "")

        decoded = base58.b58decode(private_key_base58)
        secret_key = decoded[:32]

        signing_key = ed25519.SigningKey(secret_key)
        verifying_key = signing_key.get_verifying_key()

        base58_public_key = base58.b58encode(verifying_key.to_bytes()).decode()

        return base58_public_key

    async def get_account_balance(self, account_id, private_key):
        account = Account(account_id, private_key)

        return await account.get_balance() / NEAR

    def get_private_key(self, extended_private_key):
        private_key_base58 = extended_private_key.replace("ed25519:", "")
        decoded = base58.b58decode(private_key_base58)
        secret_key = decoded[:32]

        return base58.b58encode(secret_key).decode()

    def get_account_fts(self, state, account_id):
        url = f"https://api.fastnear.com/v1/account/{account_id}/ft"
        response = requests.get(url)
        response.raise_for_status()
        content = response.json()
        tokens = content.get("tokens", [])

        print("tokens", tokens)

        if len((state.all_available_tokens or [])) == 0:
            self.get_all_tokens(state)

        for token in tokens:
            token_contract_id = token["contract_id"]
            token_decimals = state.all_available_tokens[token_contract_id]["decimal"] or 0
            token_balance_full = token["balance"] or 0
            if token_decimals and token_balance_full:
                token["balance_hr"] = convert_from_decimals_to_string(token_balance_full, token_decimals)

        return tokens

    def format_tokens_as_markdown(self, state, tokens):
        markdown_list = []

        for token in tokens:
            token_contract_id = token["contract_id"]
            token_symbol = state.all_available_tokens[token_contract_id]["symbol"] or ""
            balance_hr = token["balance_hr"] or ""

            if token_symbol and balance_hr:
                markdown_list.append(f"- {token_symbol}: {balance_hr}\n")

        if markdown_list:
            markdown_list_str = "\n**List of FT tokens:**\n" + "".join(markdown_list)
        else:
            markdown_list_str = "\n**No FT tokens found**"

        return markdown_list_str

    def get_account_nfts(self, state, account_id):
        url = f"https://api.fastnear.com/v1/account/{account_id}/nft"
        response = requests.get(url)
        response.raise_for_status()
        content = response.json()
        tokens = content.get("tokens", [])

        print("nfts", tokens)

        return tokens

    def format_nfts_as_markdown(self, state, nfts):
        markdown_list = []

        for nft in nfts:
            nft_contract_id = nfts["contract_id"]
            if nft_contract_id:
                markdown_list.append(f"- [{nft_contract_id}](https://nearblocks.io/address/{nft_contract_id})\n")

        if markdown_list:
            markdown_list_str = "\n**List of NFTs:**\n" + "".join(markdown_list)
        else:
            markdown_list_str = "\n**No NFTs found**"

        return markdown_list_str

    def get_account_staking_pools(self, state, account_id):
        url = f"https://api.fastnear.com/v1/account/{account_id}/staking"
        response = requests.get(url)
        response.raise_for_status()
        content = response.json()
        pools = content.get("pools", [])

        print("staking_pools", pools)

        return pools

    def format_pools_as_markdown(self, state, pools):
        markdown_list = []

        for pool in pools:
            pool_id = pool["pool_id"]
            if pool_id:
                markdown_list.append(f"- [{pool_id}](https://nearblocks.io/address/{pool_id})\n")

        if markdown_list:
            markdown_list_str = "\n**List of staking pools:**\n" + "".join(markdown_list)
        else:
            markdown_list_str = "\n**No staking pools found**"

        return markdown_list_str

    def get_user_message(self, state):
        last_message = self.env.get_last_message()["content"]
        reminder = "Always follow INSTRUCTIONS and produce valid JSON only as explained in OUTPUT format."
        user_message = {"message": f"{last_message}\n{reminder}", "amount": state.amount,
                        "receiver_id": state.receiver_id}

        return {"role": "user", "content": json.dumps(user_message)}

    def get_messages(self, state):
        system_prompt = self.get_data_prompt(state)
        list_messages = self.env.list_messages()
        last_message = list_messages[-1]
        if last_message["role"] == "user":
            list_messages[-1] = self.get_user_message(state)

        messages = [{"role": "system", "content": system_prompt}] + list_messages

        print("PROMPT messages:", messages)

        return messages

    def fetch_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            return data

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err}")

    def get_all_tokens(self, state: State):
        if not state.all_available_tokens:
            state.all_available_tokens = self.fetch_url("https://api.ref.finance/list-token-price")

        return state.all_available_tokens

    def parse_response(self, response):
        try:
            print("Parsing response", response)
            parsed_response = json.loads(response)
            return parsed_response

        except Exception as err:
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
                    print(f"JSON decode error: {response}")
                    return {"message": "JSON decode error"}

    def get_state(self):
        all_files = self.env.list_files(self.env.get_agent_temp_path())
        if STATE_FILE in all_files:
            try:
                _state = self.env.read_file(STATE_FILE)
                parsed_dict = json.loads(_state)
                return parsed_dict
            except json.JSONDecodeError:
                return {}
        else:
            return {}

    def save_state(self, state):
        state.remove_attribute('all_available_tokens')
        print("Saving state", state.to_json())
        self.env.write_file(STATE_FILE, state.to_json())

    def get_list_token_prompt(self, state):
        prompt = f"""Below you will find  a list of all available tokens. Format of every entry: 
        NEAR_CONTRACT_ID:{{"price":PRICE_IN_USD_STRING,"symbol":"TOKEN_TICKER","decimal":NUMBER}}


        {self.get_all_tokens(state)}

        """

        return prompt

    def get_data_prompt(self, state):
        prompt = f""""
        You are an agent inside a multi-agent system that takes in a prompt from a user requesting an action to make transaction on NEAR Blocckchain. Transactions will be performed on NEAR Blockchain by another agent, you only need to collect data from the user to prepare the swap. The user is authenticated through a message signed by their NEAR account, but this part is beyond your scope. You must follow the instructions under the "INSTRUCTIONS" label. You must provide your response in the format specified under "OUTPUT_FORMAT".

LIST OF AVAILABLE ACTIONS:
- GET_USER_DATA. Collecting user data. No required data.
- NEAR_SHOW_ACCOUNT. Show data about current account: show balances of FT (fungible tokens), NFT (non-fungible tokens), NEAR native balance, NEAR account name etc.
- NEAR_TRANSFER. When user wants to send some `amount` of NEAR tokens to `receiver_id`. Required data: {{"amount": float, "receiver_id": String}}
- NEAR_STAKE. When user wants to stake some `amount` of NEAR tokens to `receiver_id` pool. Required data: {{"amount": float, "receiver_id": String}}

**INSTRUCTIONS**
You have a list of available actions and details for each of them. 
Collect data from the user to choose the requested action perform it.
If user asks what are your available actions (or just what can you do), list descriptions of your available actions here in human-readable format and rephrase them depending on user's quote. Try to speak NOT technical.
If you are missing data, ask user to clarify it. Keep asking user until you are sure.
Do not re-confirm action from the user if you have all the data you need to perform it, always overwrite action if you got full corresponding instructions from the user. 
Do not request Yes/No confirmation from the user, always ask the missing details.
Use the same writing style as the user. If they greet you, greet them back.

User's message has the highest priority. For example, if user in the message says that to want to send 3 NEAR token, but current `amount` contains other value, overwrite them with values from the latest user message.

**OUTPUT_FORMAT**
* Your output response must be a single JSON object ONLY that can be parsed by Python's "json.loads()". Any comments expect JSON will make your reply invalid.
* The JSON may contain these fields:
    // Message to the user
    message: String
    
    // Action
    action: String ["GET_USER_DATA", "NEAR_SHOW_ACCOUNT", "NEAR_STAKE", "NEAR_TRANSFER", ...]

    /// Amount for an action
    amount: Float || null

    /// Receiver id for an action
    receiver_id: String || null
   
EXAMPLES OF VALID OUTPUT:
===example 1.1===
Input: 
{{"message": "What is your name?", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm a NEAR agent and I can help you with ... (list descriptions of your available actions)", "action": "GET_USER_DATA", "amount": 1, "receiver": null}}
===example 1.2===
Input: 
{{"message": "How can you help me name?", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm a NEAR agent and I can help you with ... (list descriptions of your available actions)", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
===example 1.3===
Input: 
{{"message": "Can you stake NEAR?", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "Yes, I know how to stake NEAR, nut I need additional data from you ... (list required data for a specified action here and rephrase them depending on user's quote)", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
===example 2.1===
Input: 
{{"message": "Send NEAR to alex.near", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm ready to send NEAR tokens to alex.near, how much to send?", "action": "GET_USER_DATA", "amount": null, "receiver": "alex.near"}}
===example 2.2===
Input: 
{{"message": "Send 3 NEAR", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm ready to send 3 NEAR tokens, where to send it?", "action": "GET_USER_DATA", "amount": 3, "receiver": null}}
===example 3===
Input: 
{{"message": "Send 0.01 NEAR to alex.near", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm sending 0.01 NEAR to alex.near", "action": "NEAR_TRANSFER", "amount": 0.01, "receiver": "alex.near"}}
===example 4.1===
Input: 
{{"message": "Show data about my account", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "Loading your NEAR account details...", "action": "NEAR_SHOW_ACCOUNT", "amount": null, "receiver": null}}
===example 4.2===
Input: 
{{"message": "Show my balances", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "Loading your NEAR account details...", "action": "NEAR_SHOW_ACCOUNT", "amount": null, "receiver": null}}
===example 5.1===
Input: 
{{"message": "Stake NEAR to alex.poolv1.near", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm ready to stake NEAR tokens to alex.poolv1.near, how much to stake?", "action": "GET_USER_DATA", "amount": null, "receiver": "alex.poolv1.near"}}
===example 5.2===
Input: 
{{"message": "Stake 3 NEAR", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm ready to stake 3 NEAR tokens, where to stake it? Please send a pool address.", "action": "GET_USER_DATA", "amount": 3, "receiver": null}}
===example 6===
Input: 
{{"message": "Stake 1.5 NEAR to alex.pool.near", "action": "GET_USER_DATA", "amount": null, "receiver": null}}
Output:
{{"message": "I'm staking 1.5 NEAR to alex.pool.near", "action": "NEAR_STAKE", "amount": 1.5, "receiver": "alex.pool.near"}}

LIST OF AVAILABLE TOKENS:
{self.get_list_token_prompt(state)}

"""

        return prompt
