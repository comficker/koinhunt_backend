import os
from django.db import models
from utils.slug import unique_slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Count

REWARD_BASE = float(os.getenv("REWARD_BASE", "0"))


class BaseModel(models.Model):
    STATUS_CHOICE = (
        (-1, _("Deleted")),
        (0, _("Pending")),
        (1, _("Active")),
    )
    meta = models.JSONField(null=True, blank=True)
    updated = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)
    db_status = models.IntegerField(choices=STATUS_CHOICE, default=1)

    class Meta:
        abstract = True


class HasIDString(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    id_string = models.CharField(max_length=200, db_index=True)

    def save(self, **kwargs):
        # generate unique slug
        if hasattr(self, 'id_string') and self.id is None and self.id_string is None or self.id_string == "":
            unique_slugify(self, self.name, "id_string")
        elif self.id is not None and self.id_string:
            unique_slugify(self, self.id_string, "id_string")
        super(HasIDString, self).save(**kwargs)

    class Meta:
        abstract = True


class Validation(models.Model):
    verified = models.BooleanField(default=False)
    score_validation = models.FloatField(default=0)
    init_power_target = models.FloatField(default=REWARD_BASE * 100)
    score_detail = models.JSONField(default=dict, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def get_validation_score(self):
        ct = ContentType.objects.get_for_model(self)
        contributions = ct.contributions.filter(
            target_object_id=self.id,
        ).order_by('-score_validation')
        count = contributions.count()
        self.score_validation = contributions.aggregate(total=Sum('score_validation')).get("total", 0)
        if hasattr(self, 'meta') and self.meta is None:
            self.meta = {}
        self.meta["contributions"] = list(map(lambda x: {
            "wallet": x.wallet.address,
            "score_validation": x.score_validation
        }, contributions[:5]))
        init_contrib = contributions.filter(field="INIT").first()
        if init_contrib:
            self.meta["validations"] = list(map(lambda x: {
                "wallet": x.wallet.address,
                "power": x.power
            }, init_contrib.validates.order_by("-id")[:5]))
        self.meta["count_contribution"] = count
        self.meta["count_validation"] = contributions.annotate(count=Count('validates')) \
            .aggregate(total=Sum("count")) \
            .get("total")
        self.save()


class BlockChain(models.Model):
    class ChainChoice(models.TextChoices):
        CHAIN_BSC_MAINNET = "bsc_mainnet", _("BSC mainnet")
        CHAIN_ETH_MAINNET = "eth_mainnet", _("ETH mainnet")

    chain_id = models.CharField(default=ChainChoice.CHAIN_BSC_MAINNET, max_length=50)
    address = models.CharField(max_length=100, db_index=True)

    class Meta:
        abstract = True
        unique_together = ['chain_id', 'address']
