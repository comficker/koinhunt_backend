from django.core.management.base import BaseCommand
from utils import coingecko


class Command(BaseCommand):

    def handle(self, *args, **options):
        coingecko.fetch_cgk(
            break_wallet=9000,
            enable_detail=True,
            enable_ranges=[],
            push_file=True,
            push_mq=True
        )
