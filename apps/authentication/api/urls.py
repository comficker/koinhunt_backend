from . import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import include, url

router = DefaultRouter()
router.register(r'wallets', views.WalletViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
