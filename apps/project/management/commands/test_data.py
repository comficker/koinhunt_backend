import os
import json
from django.core.management.base import BaseCommand
from apps.project.models import Token, Wallet, Project, Term, ProjectTerm
from utils.coingecko import handle_data_token

CHAIN_MAPPING = {
    "binance-smart-chain": {
        "name": "Binance Smart Chain",
        "id_string": "binance-smart-chain",
        "description": "A Parallel Binance Chain to Enable Smart Contracts"
    },
    "ronin": {
        "name": "Ronin",
        "id_string": "ronin",
        "description": "The Ronin Block Explorer is an analytics platform for Ronin, "
                       "an Ethereum side-chain built by Sky Mavis."
    },
    "ethereum": {
        "name": "Ethereum",
        "id_string": "ethereum",
        "description": "Ethereum is a decentralized, open-source blockchain with smart contract functionality. "
                       "Ether is the native cryptocurrency of the platform."
    }
}


class Command(BaseCommand):

    def handle(self, *args, **options):
        full_sub_dir = "data/coingecko/aloha/1645705094.912683.json"
        with open(full_sub_dir, 'r') as j:
            data = json.loads(j.read())
            wallet = Wallet.objects.order_by("?").first()
            token = handle_data_token(data, wallet)
            print(token)
