from django.core.management.base import BaseCommand
from utils.coingecko import clean_short_report
from apps.project.models import Token


class Command(BaseCommand):

    def handle(self, *args, **options):
        tokens = Token.objects.all()
        for token in tokens:
            token.short_report = clean_short_report(token.short_report)
            token.init_price = token.short_report.get("atl", 0)
            token.save()
