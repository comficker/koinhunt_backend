from apps.authentication.models import Wallet
from django.utils.deprecation import MiddlewareMixin


class WalletMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        if request.headers.get("Wallet"):
            request.wallet, _ = Wallet.objects.get_or_create(
                address=request.headers.get("Wallet")
            )
        else:
            request.wallet = None
