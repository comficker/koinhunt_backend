import os
import json

from web3 import Web3

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

with open('abi/Token.json') as json_file:
    ABI_TOKEN = json.load(json_file)
with open('abi/NFT.json') as json_file:
    ABI_NFT = json.load(json_file)

contract_token = w3.eth.contract(address=os.getenv("ADDR_TOKEN"), abi=ABI_TOKEN)
contract_nft_hunter = w3.eth.contract(address=os.getenv("ADDR_NFT_HUNTER"), abi=ABI_NFT)
contract_nft_validator = w3.eth.contract(address=os.getenv("ADDR_NFT_VALIDATOR"), abi=ABI_NFT)
