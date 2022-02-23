from django.core.management.base import BaseCommand
from apps.project.models import Token, Contribute, Validate


class Command(BaseCommand):

    def handle(self, *args, **options):
        tokens = Token.objects.all()
        for token in tokens:
            if token.short_report and token.price_init > 0:
                token.short_report["pac"] = round(token.short_report["ath"] / token.price_init)
                token.short_report["pcc"] = round(token.price_current / token.price_init)
                token.save()

