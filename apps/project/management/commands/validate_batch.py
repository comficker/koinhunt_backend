from django.core.management.base import BaseCommand
from apps.project.models import Contribute, Validate, Wallet
from utils.wallets import operators


class Command(BaseCommand):

    def handle(self, *args, **options):
        contributes = Contribute.objects.filter(
            target_content_type__model="event",
            verified=False,
            field="INIT"
        )
        for contrib in contributes:
            print(contrib)
            for address in operators.keys():
                if address != contrib.wallet.address:
                    operator_wallet = Wallet.objects.get(
                        address=address,
                        chain="binance-smart-chain"
                    )
                    Validate.objects.get_or_create(
                        wallet=operator_wallet,
                        contribute=contrib
                    )
