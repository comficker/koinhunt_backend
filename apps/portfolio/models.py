from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from apps.base.interface import BaseModel
from apps.media.models import Media
from apps.project.models import Token
from apps.authentication.models import Wallet


# Create your models here.
# PORTFOLIO
class Portfolio(BaseModel):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=600, blank=True, null=True)
    meta = models.JSONField(null=True, blank=True)
    media = models.ForeignKey(Media, related_name="portfolios", on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, related_name="portfolios", on_delete=models.CASCADE)
    tokens = models.ManyToManyField(Token, related_name="portfolios", blank=True)
    wallets = models.ManyToManyField(Wallet, related_name="portfolios", blank=True)


class Entry(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="entries")
    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name="entries")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="entries")
    in_amount = models.FloatField(default=0)
    in_price = models.FloatField(default=0)  # USD
    in_date = models.DateTimeField(default=timezone.now)
