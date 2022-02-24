from django.core.management.base import BaseCommand
from utils import coingecko


class Command(BaseCommand):

    def handle(self, *args, **options):
        coingecko.fetch_cgk(
            break_wallet="baby-floki-up",
            enable_detail=False,
            enable_ranges=[1],
            push_file=False,
            push_mq=True
        )
