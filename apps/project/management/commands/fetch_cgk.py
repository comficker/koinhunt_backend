from django.core.management.base import BaseCommand
from utils import coingecko


class Command(BaseCommand):

    def handle(self, *args, **options):
        coingecko.fetch_cgk(break_wallet="infinity-eth", enable_detail=False, enable_ranges=[1])
