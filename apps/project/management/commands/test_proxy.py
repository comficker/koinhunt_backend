import requests
from django.core.management.base import BaseCommand
from utils.proxy import get_proxies


class Command(BaseCommand):

    def handle(self, *args, **options):
        req = requests.get(
            "https://api.coingecko.com/api/v3/coins/list",
            proxies={
                "http": get_proxies()
            }
        )
        print(req.json())
