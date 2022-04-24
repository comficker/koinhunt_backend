from django.core.management.base import BaseCommand
from utils.tracker_launchpad.gamefi_v2 import fetch, fetch_igo


class Command(BaseCommand):

    def handle(self, *args, **options):
        fetch("05TfXTSF5_7vpLam60k8c", 1)
        fetch_igo("mysterious-box", 1)
        fetch_igo("complete-sale-pools", 1)
