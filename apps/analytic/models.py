from django.utils import timezone
from django.db import models
from apps.base.interface import BaseModel
from apps.authentication.models import Profile
from apps.project.models import Token


# Create your models here.
class Transaction(BaseModel):
    tx_hash = models.CharField()
    ty_type = models.CharField(default="transfer")
    fr = models.ForeignKey(Profile, related_name="fr_transactions", on_delete=models.CASCADE)
    to = models.ForeignKey(Profile, related_name="to_transactions", on_delete=models.CASCADE)
    token = models.ForeignKey(Token, related_name="transactions", on_delete=models.CASCADE)
    meta = models.JSONField(null=True, blank=True)
    value = models.FloatField(default=0)
    time_stamp = models.DateTimeField(default=timezone.now)


class TrackSocial(BaseModel):
    network = models.CharField(max_length=42)
    channel = models.CharField(max_length=42)
    value = models.FloatField(default=0)
    time_stamp = models.DateTimeField(default=timezone.now)
    meta = models.JSONField(null=True, blank=True)


class PriceHistory(BaseModel):
    marketplace = models.ForeignKey(Token, related_name="history_prices", on_delete=models.CASCADE, null=True, blank=True)
    token = models.ForeignKey(Token, related_name="history_prices", on_delete=models.CASCADE)
    value = models.FloatField(default=0)
