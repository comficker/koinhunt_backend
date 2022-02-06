from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.base.interface import BaseModel, HasIDSting, Validation
from apps.media.models import Media
from apps.authentication.models import Wallet
from django.utils.translation import ugettext_lazy as _


# Create your models here.

class Term(BaseModel, HasIDSting):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="terms", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)

    reputation = models.FloatField(default=0)
    taxonomy = models.CharField(max_length=10, default="tag")

    class Meta:
        unique_together = [['id_string', 'taxonomy']]


class Project(BaseModel, HasIDSting, Validation):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="projects", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)

    calculated_score = models.FloatField(default=0)

    terms = models.ManyToManyField(Term, related_name="projects", blank=True)
    wallet = models.ForeignKey(Wallet, related_name="hunted_projects", on_delete=models.SET_NULL, null=True, blank=True)

    def calculate_launch_date(self):
        last_event = self.project_events.filter(event_name="launch").order_by("-date_start").first()
        if last_event:
            self.launch_date = last_event.date_start
            self.save()


class Token(BaseModel, Validation):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="tokens", on_delete=models.SET_NULL, null=True, blank=True)

    chain = models.ForeignKey(Term, related_name="tokens", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=42)
    address = models.CharField(max_length=42)
    decimal = models.CharField(max_length=3, default=18)
    total_supply = models.FloatField(default=0)
    circulating_supply = models.FloatField(default=0)

    project = models.ForeignKey(Project, related_name="tokens", on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, related_name="hunted_tokens", on_delete=models.SET_NULL, null=True, blank=True)


class Event(BaseModel, Validation):
    class EventNameChoice(models.TextChoices):
        LAUNCH = "launch", _("Launch")
        IDO = "ido", _("Initial DEX Offering")
        IEO = "ieo", _("Initial Exchange Offering")
        IGO = "igo", _("Initial Gaming Offering")
        ADD_MEMBER = "add_member", _("Add member")
        ADD_INVESTOR = "add_investor", _("Add Investor")

    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="events", on_delete=models.SET_NULL, null=True, blank=True)

    event_name = models.CharField(
        max_length=40,
        default=EventNameChoice.LAUNCH
    )
    event_date_start = models.DateTimeField(null=True, blank=True)
    event_date_end = models.DateTimeField(null=True, blank=True)

    project = models.ForeignKey(Project, related_name="project_events", on_delete=models.CASCADE)
    targets = models.ManyToManyField(Project, related_name="target_events", blank=True)
    wallet = models.ForeignKey(Wallet, related_name="events", null=True, blank=True, on_delete=models.SET_NULL)


class Collection(BaseModel):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="collections", on_delete=models.SET_NULL, null=True, blank=True)

    wallet = models.ForeignKey(Wallet, related_name="collections", on_delete=models.CASCADE)
    projects = models.ManyToManyField(Project, related_name="collections", blank=True)


class Contribute(BaseModel, Validation):
    wallet = models.ForeignKey(Wallet, related_name="contributions", on_delete=models.CASCADE)
    target_content_type = models.ForeignKey(
        ContentType, related_name='contributions',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(max_length=128)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    field = models.CharField(max_length=128)
    meta = models.JSONField(null=True, blank=True)
    data = models.JSONField()


class Validate(BaseModel):
    wallet = models.ForeignKey(Wallet, related_name="validates", on_delete=models.CASCADE)
    target_content_type = models.ForeignKey(
        ContentType, related_name='validates',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(max_length=128)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    meta = models.JSONField(null=True, blank=True)
    power = models.FloatField(default=0)

