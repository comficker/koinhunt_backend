from django.db import models
from django.contrib.auth.models import User
from apps.base.interface import BaseModel, HasIDSting
from apps.media.models import Media


# Create your models here.

class Term(BaseModel, HasIDSting):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="terms", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)
    reputation = models.FloatField(default=0)

    taxonomy = models.CharField(max_length=10, default="tag")


class Partner(BaseModel, HasIDSting):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="markets", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)
    reputation = models.FloatField(default=0)

    partner_type = models.CharField(max_length=50, default="market")
    terms = models.ManyToManyField(Term, related_name="markets", blank=True)


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
        for event in self.events.all():
            if event.verified and event.partner is not None:
                self.calculated_score = self.calculated_score + event.partner.reputation
        self.save()

    def calculate_launch_date(self):
        last_event = self.events.filter(event_name="launch").order_by("-date_start").first()
        if last_event:
            self.launch_date = last_event.date_start
            self.save()


class Token(BaseModel):
    project = models.ForeignKey(Project, related_name="tokens", on_delete=models.CASCADE)
    chain = models.ForeignKey(Term, related_name="tokens", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=42)
    address = models.CharField(max_length=42)
    decimal = models.CharField(max_length=3, default=18)
    total_supply = models.FloatField(default=0)
    circulating_supply = models.FloatField(default=0)


class Event(BaseModel):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="events", on_delete=models.SET_NULL, null=True, blank=True)

    partner = models.ForeignKey(Partner, related_name="events", on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, related_name="events", on_delete=models.CASCADE)

    event_name = models.CharField(max_length=20, default="launch")  # launch airdrop presale ama audit partner collab
    event_date_start = models.DateTimeField(null=True, blank=True)
    event_date_end = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)


class Vote(BaseModel):
    project = models.ForeignKey(Project, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="votes", on_delete=models.SET_NULL, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)
