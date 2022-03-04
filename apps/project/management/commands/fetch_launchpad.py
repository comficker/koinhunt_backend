from django.core.management.base import BaseCommand
from utils import coingecko
from utils.tracker_launchpad.gamefi import fetch_gafi, fetch_perform


class Command(BaseCommand):

    def handle(self, *args, **options):
        fetch_gafi(1)
        fetch_perform()
