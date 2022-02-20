import requests
from django.core.management.base import BaseCommand
from utils.coingecko import fetch_token, fetch_token_market_chart
from datetime import datetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        one_day = 86400
        now = datetime.now().timestamp()
        # token = fetch_token("step-hero")
        # fetch_token_market_chart(token, "step-hero", fr=now - one_day, to=now)
        # fetch_token_market_chart(token, "step-hero", fr=now - one_day * 90, to=now - one_day)
        # fetch_token_market_chart(token, "step-hero", fr=now - one_day * 180, to=now - one_day * 90)
        req = requests.get("https://api.coingecko.com/api/v3/coins/list")
        coins = req.json()
        start = False
        i = 0
        for coin in coins:
            print(coin)
            if coin["id"] and i < 5:
                if not start:
                    start = coin["id"] == "betswap-gg"
                    continue
                token = fetch_token(coin["id"])
                if token:
                    fetch_token_market_chart(token, coin["id"], fr=now - one_day, to=now)
                    fetch_token_market_chart(token, coin["id"], fr=now - one_day * 90, to=now - one_day)
                    fetch_token_market_chart(token, coin["id"], fr=now - one_day * 180, to=now - one_day * 90)
                i = i + 1
