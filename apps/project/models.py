from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from apps.base.interface import BaseModel, HasIDSting
from apps.media.models import Media
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


class Project(BaseModel, HasIDSting):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="projects", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)

    terms = models.ManyToManyField(Term, related_name="projects", blank=True)
    hunter = models.ForeignKey(User, related_name="hunted_projects", on_delete=models.SET_NULL, null=True, blank=True)
    calculated_score = models.FloatField(default=0)

    def calculate_score(self):
        self.calculated_score = self.votes.count()
        for event in self.project_events.all():
            if event.verified and event.partner is not None:
                self.calculated_score = self.calculated_score + event.partner.reputation
        self.save()

    def calculate_launch_date(self):
        last_event = self.project_events.filter(event_name="launch").order_by("-date_start").first()
        if last_event:
            self.launch_date = last_event.date_start
            self.save()


class Token(BaseModel):
    meta = models.JSONField(null=True, blank=True)
    project = models.ForeignKey(Project, related_name="tokens", on_delete=models.CASCADE)
    chain = models.ForeignKey(Term, related_name="tokens", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=42)
    address = models.CharField(max_length=42)
    decimal = models.CharField(max_length=3, default=18)
    total_supply = models.FloatField(default=0)
    circulating_supply = models.FloatField(default=0)


class Event(BaseModel):
    LAUNCH = "launch"

    class EventNameChoice(models.TextChoices):
        LAUNCH = "launch", _("Launch")
        IDO = "ido", _("Initial DEX Offering")
        IEO = "ieo", _("Initial Exchange Offering")
        IGO = "igo", _("Initial Gaming Offering")
        ADD_MEMBER = "add_member", _("Add member")
        ADD_INVESTOR = "add_investor", _("Add Investor")

    project = models.ForeignKey(Project, related_name="project_events", on_delete=models.CASCADE)
    targets = models.ManyToManyField(Project, related_name="target_events", blank=True)

    name = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="events", on_delete=models.SET_NULL, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)

    event_name = models.CharField(
        max_length=40,
        default=EventNameChoice.LAUNCH
    )  # launch airdrop presale ama audit partner collab
    event_date_start = models.DateTimeField(null=True, blank=True)
    event_date_end = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    user = models.ForeignKey(User, related_name="events", null=True, blank=True, on_delete=models.SET_NULL)
    followers = models.ManyToManyField(User, related_name="followed_events", blank=True)


class Vote(BaseModel):
    project = models.ForeignKey(Project, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="votes", on_delete=models.SET_NULL, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)


class Collection(BaseModel):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)

    user = models.ForeignKey(User, related_name="collections", on_delete=models.CASCADE)
    projects = models.ManyToManyField(Project, related_name="collections", blank=True)


class Contrib(BaseModel):
    user = models.ForeignKey(User, related_name="contributions", on_delete=models.CASCADE)
    target_content_type = models.ForeignKey(
        ContentType, related_name='contributions',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(max_length=128)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    field = models.CharField(max_length=128)
    meta = models.JSONField(null=True, blank=True)
    data = models.JSONField()
    verified = models.BooleanField(default=False)
