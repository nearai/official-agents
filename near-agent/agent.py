import asyncio
import enum

from nearai.agents.environment import Environment
from py_near.account import Account
from py_near.dapps.core import NEAR

from utils import AiUtils, State

# load user's private key
signer_private_key = globals()['env'].env_vars.get("signer_private_key", None)

utils = AiUtils(env, agent)


async def agent(env: Environment, state: State):
    if not signer_private_key:
        env.add_reply("Add a secret `signer_private_key` with the private key from your NEAR mainnet account to start")
    else:
        reset_state = False

        if state.action == Actions.GET_USER_DATA:
            # collect user's data
            messages = utils.get_messages(state)
            reply = env.completion(messages)

            data = utils.parse_response(reply)

            if data.get("action") is not None:
                state.action = Actions(data["action"])

            if data.get("amount") is not None:
                state.amount = data["amount"]

            if data.get("receiver_id") is not None:
                state.receiver_id = data["receiver_id"]

            if state.action != Actions.NEAR_SHOW_ACCOUNT:
                env.add_reply(data.get("message"))

        if state.action == Actions.NEAR_SHOW_ACCOUNT:
            # if user asked to show account details
            signer_public_key = utils.get_public_key(signer_private_key)
            signer_account_id = utils.get_account_id(signer_public_key)

            print(f"Reading {signer_account_id}")

            if signer_account_id:
                balance = await utils.get_account_balance(signer_account_id, signer_private_key)

                print(f"Balance {balance}")

                fts = utils.get_account_fts(state, signer_account_id)
                if len(fts) > 0:
                    ft_balances_markdown_str = utils.format_tokens_as_markdown(state, fts)
                else:
                    ft_balances_markdown_str = ""

                nfts = utils.get_account_nfts(state, signer_account_id)
                if len(nfts) > 0:
                    nfts_markdown_str = utils.format_nfts_as_markdown(state, nfts)
                else:
                    nfts_markdown_str = ""

                pools = utils.get_account_staking_pools(state, signer_account_id)
                if len(pools) > 0:
                    pools_markdown_str = utils.format_pools_as_markdown(state, pools)
                else:
                    pools_markdown_str = ""

                env.add_reply(
                    f"Your account is [{signer_account_id}](https://nearblocks.io/address/{signer_account_id}).\nYour account balance is {balance} NEAR.{pools_markdown_str}{ft_balances_markdown_str}{nfts_markdown_str}")
            else:
                env.add_reply(f"Mainnet account with public key {signer_public_key} not found")

            reset_state = True

        if state.action == Actions.NEAR_TRANSFER and state.receiver_id and state.amount > 0:
            # if user asked to make a transfer, and we have all the necessary data

            signer_public_key = utils.get_public_key(signer_private_key)
            signer_account_id = utils.get_account_id(signer_public_key)
            acc = Account(signer_account_id, signer_private_key)

            await acc.startup()

            transaction_hash = await acc.send_money(state.receiver_id, int(NEAR * state.amount), nowait=True)

            env.add_reply(f"Transaction created: [{transaction_hash}](https://nearblocks.io/txns/{transaction_hash})")

            reset_state = True

        if state.action == Actions.NEAR_STAKE and state.receiver_id and state.amount > 0:
            # if user asked to make a transfer, and we have all the necessary data

            signer_public_key = utils.get_public_key(signer_private_key)
            signer_account_id = utils.get_account_id(signer_public_key)
            acc = Account(signer_account_id, signer_private_key)

            await acc.startup()

            transaction_hash = await acc.function_call(state.receiver_id, 'deposit_and_stake', {}, 100000000000000,
                                                       int(NEAR * state.amount), nowait=True)

            env.add_reply(f"Transaction created: [{transaction_hash}](https://nearblocks.io/txns/{transaction_hash})")

            reset_state = True

        if reset_state:
            # just reset state after the successful action
            state.action = "GET_USER_DATA"
            state.amount = None
            state.receiver_id = None

    utils.save_state(state)


class Actions(enum.Enum):
    GET_USER_DATA = "GET_USER_DATA"
    NEAR_SHOW_ACCOUNT = "NEAR_SHOW_ACCOUNT"
    NEAR_TRANSFER = "NEAR_TRANSFER"
    NEAR_STAKE = "NEAR_STAKE"


state = State(**utils.get_state())
if state.action:
    state.action = Actions(state.action)
if state.amount:
    state.amount = float(state.amount)

asyncio.run(agent(env, state))
