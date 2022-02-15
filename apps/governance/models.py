from datetime import datetime
from django.db import models
from apps.base.interface import BaseModel, HasIDString, BlockChain


# Create your models here.


class TokenContract(BaseModel, HasIDString, BlockChain):
    description = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(default="ERC20", max_length=20)
    symbol = models.CharField(max_length=50)
    total_supply = models.FloatField(default=0)
    decimals = models.IntegerField(default=18)


class NFT(BaseModel):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)
    contract = models.ForeignKey(TokenContract, related_name="nfts", on_delete=models.CASCADE)
    item_id = models.CharField(max_length=128)
    current_price = models.FloatField(default=0)
    media_url = models.CharField(max_length=512, null=True, blank=True)
    last_time_log = models.DateTimeField(default=datetime.now)
