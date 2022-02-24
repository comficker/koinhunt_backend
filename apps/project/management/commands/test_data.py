import os
import json
from django.core.management.base import BaseCommand
from apps.project.models import Token, Contribute, Validate, Term

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
        full_sub_dir = "data/coingecko/step-hero/1645509247.519432.json"
        with open(full_sub_dir, 'r') as j:
            data = json.loads(j.read())
            for key in data.get("platforms", {}).keys():
                chain_raw = CHAIN_MAPPING.get(key)
                print(chain_raw)
                if chain_raw:
                    term, _ = Term.objects.get_or_create(
                        taxonomy="chain",
                        name=chain_raw.get("name"),
                        defaults={

                            "description": chain_raw.get("description")
                        }
                    )
                    print(term)
