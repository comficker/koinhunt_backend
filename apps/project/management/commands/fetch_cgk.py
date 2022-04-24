from django.core.management.base import BaseCommand
from utils.tracker import coingecko


class Command(BaseCommand):

    def handle(self, *args, **options):
        coingecko.fetch_cgk(
            break_wallet=13490,
            enable_detail=True,
            enable_ranges=[1],
        )
