from web3 import Web3
from eth_account import Account

PRIVATE_KEY = globals()['env'].env_vars.get("PRIVATE_KEY", None)

RPC_URL = 'https://eth-sepolia.public.blastapi.io'
CONTRACT_ADDRESS = '0xFd9e2642a170aDD10F53Ee14a93FcF2F31924944'
ABI = []


def setup_web3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise Exception("Failed to connect to Ethereum network")
    
    # Set up account
    account = Account.from_key(PRIVATE_KEY)
    w3.eth.default_account = account.address
    
    # Initialize contract
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=ABI
    )

    return w3


w3 = setup_web3()

