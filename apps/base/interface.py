from django.db import models
from utils.slug import unique_slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum


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

    def save(self, **kwargs):
        # generate unique slug
        self.created = timezone.now()
        self.updated = timezone.now()
        super(BaseModel, self).save(**kwargs)


class HasIDString(models.Model):
    name = models.CharField(max_length=200)
    id_string = models.CharField(max_length=200)

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
    validation_score = models.FloatField(default=0)

    class Meta:
        abstract = True

    def get_validation_score(self):
        ct = ContentType.objects.get_for_model(self)
        qs = ct.validates.filter(target_object_id=self.id).order_by("-power")
        count = qs.count()
        if count:
            self.validation_score = qs.aggregate(total=Sum('power')).get("total")
            if hasattr(self, 'meta') and self.meta is None:
                self.meta = {}
            self.meta["count_validate"] = count
            self.meta["validates"] = list(map(lambda x: {
                "power": x.power,
                "wallet": x.wallet.address
            }, qs[:5]))
            self.meta["count_validator"] = qs.count()
            self.save()


class BlockChain(models.Model):
    class ChainChoice(models.TextChoices):
        CHAIN_BSC_MAINNET = "bsc_mainnet", _("BSC mainnet")
        CHAIN_ETH_MAINNET = "eth_mainnet", _("ETH mainnet")

    chain_id = models.CharField(default=ChainChoice.CHAIN_BSC_MAINNET, max_length=50)
    address = models.CharField(max_length=100)

    class Meta:
        abstract = True
        unique_together = ['chain_id', 'address']
