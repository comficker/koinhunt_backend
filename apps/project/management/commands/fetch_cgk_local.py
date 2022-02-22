from django.core.management.base import BaseCommand
from utils import coingecko


class Command(BaseCommand):

    def handle(self, *args, **options):
        coingecko.read_data_local()
