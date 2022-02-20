from django.db import models
from apps.base.interface import BaseModel
from apps.media.models import Media


class Wallet(models.Model):
    chain = models.CharField(max_length=20, default="binance-smart-chain")
    address = models.CharField(max_length=42)
    nick = models.CharField(max_length=200, null=True, blank=True)
    bio = models.CharField(max_length=500, null=True, blank=True)
    media = models.ForeignKey(Media, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles")
    meta = models.JSONField(blank=True, null=True)
    options = models.JSONField(blank=True, null=True)
