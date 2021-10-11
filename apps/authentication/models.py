from django.db import models
from django.contrib.auth.models import User
from apps.base.interface import BaseModel
from apps.media.models import Media


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    nick = models.CharField(max_length=200, null=True, blank=True)
    bio = models.CharField(max_length=500, null=True, blank=True)
    media = models.ForeignKey(Media, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles")
    meta = models.JSONField(blank=True, null=True)
    options = models.JSONField(blank=True, null=True)


class Wallet(BaseModel):
    address = models.CharField(max_length=42, primary_key=True)
    meta = models.JSONField(null=True, blank=True)
