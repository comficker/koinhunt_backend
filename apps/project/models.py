from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.base.interface import BaseModel, HasIDString, Validation, BlockChain
from apps.media.models import Media
from apps.authentication.models import Wallet
from apps.governance.models import NFT, TokenContract
from apps.authentication.models import Wallet
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db.models import Sum


def default_score():
    return {
        "term": 0,
        "token": 0,
        "hunt": 0,
        "validate": 0,
        "event": 0
    }


# Create your models here.
# ================ FOR PROJECT
class Term(BaseModel, HasIDString):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="terms", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)

    reputation = models.FloatField(default=0)
    taxonomy = models.CharField(max_length=10, default="tag")

    class Meta:
        unique_together = [['id_string', 'taxonomy']]


class Token(BaseModel, BlockChain, Validation):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="tokens", on_delete=models.SET_NULL, null=True, blank=True)

    symbol = models.CharField(max_length=42)
    decimal = models.CharField(max_length=3, default=18)
    total_supply = models.FloatField(default=0)
    circulating_supply = models.FloatField(default=0)

    price_init = models.FloatField(default=0)
    price_current = models.FloatField(default=0)
    price_ath = models.FloatField(default=0)
    price_atl = models.FloatField(default=0)

    tokenomics = models.JSONField(null=True, blank=True)
    platforms = models.JSONField(null=True, blank=True)
    short_report = models.JSONField(null=True, blank=True)
    external_ids = models.JSONField(null=True, blank=True)

    # FOR HUNTER
    wallet = models.ForeignKey(Wallet, related_name="tokens", null=True, blank=True, on_delete=models.SET_NULL)
    nft = models.ForeignKey(NFT, related_name="tokens", null=True, blank=True, on_delete=models.SET_NULL)

    time_check = models.DateTimeField(default=timezone.now)

    def fetch_short_report(self):
        self.short_report = {
            "market_cap": 856710672222,
            "market_cap_change_24h": 23843367924,
            "high_24h": 45406,
            "low_24h": 43341,
            "total_volume": 25514855122,
            "ath": 69045,
            "ath_change_percentage": -34.56069,
            "ath_date": "2021-11-10T14:24:11.849Z",
        }


class Project(BaseModel, HasIDString, Validation):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="projects", on_delete=models.SET_NULL, null=True, blank=True)
    id_string = models.CharField(max_length=200)

    homepage = models.CharField(max_length=128, blank=True)
    links = models.JSONField(null=True, blank=True)
    features = models.JSONField(null=True, blank=True)
    launch_date = models.DateTimeField(null=True, blank=True)

    score_hunt = models.FloatField(default=0)
    score_calculated = models.FloatField(default=0)
    score_detail = models.JSONField(default=default_score)

    terms = models.ManyToManyField(Term, through='ProjectTerm', related_name="projects", blank=True)
    tokens = models.ManyToManyField(Token, related_name="projects", blank=True)
    main_token = models.ForeignKey(
        Token, related_name="main_projects", blank=True, null=True,
        on_delete=models.SET_NULL
    )

    # FOR HUNTER
    wallet = models.ForeignKey(Wallet, related_name="hunted_projects", null=True, blank=True, on_delete=models.SET_NULL)
    nft = models.ForeignKey(NFT, related_name="hunted_projects", null=True, blank=True, on_delete=models.SET_NULL)

    def calculate_launch_date(self):
        last_event = self.project_events.filter(event_name="launch").order_by("-date_start").first()
        if last_event:
            self.launch_date = last_event.date_start
            self.save()


class ProjectTerm(models.Model):
    project = models.ForeignKey(Project, related_name="project_terms", on_delete=models.CASCADE)
    term = models.ForeignKey(Term, related_name="project_terms", on_delete=models.CASCADE)
    meta = models.JSONField(null=True, blank=True)


class Event(BaseModel, Validation):
    class EventNameChoice(models.TextChoices):
        LAUNCH = "launch", _("Launch")
        LISTING = "listing", _("Listing")
        IDO = "ido", _("Initial DEX Offering")
        ICO = "ico", _("Initial CEX Offering")
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

    # FOR HUNTER
    wallet = models.ForeignKey(Wallet, related_name="events", null=True, blank=True, on_delete=models.SET_NULL)
    nft = models.ForeignKey(NFT, related_name="events", null=True, blank=True, on_delete=models.SET_NULL)


class Collection(BaseModel, Validation):
    meta = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=600, blank=True, null=True)
    media = models.ForeignKey(Media, related_name="collections", on_delete=models.SET_NULL, null=True, blank=True)

    # FOR HUNTER
    wallet = models.ForeignKey(Wallet, related_name="collections", on_delete=models.CASCADE)
    projects = models.ManyToManyField(Project, related_name="collections", blank=True)


# ================ FOR VALIDATION
class Contribute(BaseModel, Validation):
    # FOR HUNTER
    wallet = models.ForeignKey(Wallet, related_name="contributions", on_delete=models.CASCADE)
    nft = models.ForeignKey(NFT, related_name="contributions", null=True, blank=True, on_delete=models.SET_NULL)

    target_content_type = models.ForeignKey(
        ContentType, related_name='contributions',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(max_length=128)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    field = models.CharField(max_length=128, null=True)
    meta = models.JSONField(null=True, blank=True)
    data = models.JSONField()

    def get_validation_score(self):
        validates = self.validates.order_by("-power")
        count = validates.count()
        self.score_validation = validates.aggregate(total=Sum('power')).get("total") or 0
        if hasattr(self, 'meta') and self.meta is None:
            self.meta = {}
        self.meta["validates"] = list(map(lambda x: {"power": x.power, "wallet": x.wallet.address}, validates[:5]))
        self.meta["count_validate"] = count

        self.save()
        self.target.get_validation_score()


class Incentive(BaseModel):
    name = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=600, blank=True, null=True)

    contribute = models.ForeignKey(Contribute, related_name='incentives', on_delete=models.CASCADE)

    reward_token = models.ForeignKey(TokenContract, related_name="incentives", on_delete=models.CASCADE)
    reward_total = models.FloatField(default=0)
    reward_remain = models.FloatField(default=0)

    power_target = models.FloatField(default=0)
    due_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)


class Validate(BaseModel):
    # FOR Validator
    wallet = models.ForeignKey(Wallet, related_name="validates", on_delete=models.CASCADE)
    nft = models.ForeignKey(NFT, related_name="validates", null=True, blank=True, on_delete=models.SET_NULL)
    contribute = models.ForeignKey(Contribute, related_name='validates', on_delete=models.CASCADE)
    power = models.FloatField(default=0)


class IncentiveDistribution(BaseModel):
    validate = models.ForeignKey(Validate, related_name="incentive_distributions", on_delete=models.CASCADE)
    incentive = models.ForeignKey(Incentive, related_name="incentive_distributions", on_delete=models.CASCADE)
    earned = models.FloatField(default=0)
    is_claimed = models.BooleanField(default=False)


# ================ FOR TOKEN TRACKER
class TokenPrice(BaseModel):
    token = models.ForeignKey(Token, related_name="token_prices", on_delete=models.CASCADE)
    time_check = models.DateTimeField(default=timezone.now)
    time_open = models.DateTimeField(blank=True, null=True)
    time_close = models.DateTimeField(blank=True, null=True)
    supply = models.FloatField(default=0)
    price_open = models.FloatField(default=0)
    price_close = models.FloatField(default=0)
    price_avg = models.FloatField(default=0)


class TokenLog(models.Model):
    token = models.ForeignKey(Token, related_name="token_logs", on_delete=models.CASCADE)
    time_check = models.DateTimeField(default=timezone.now)
    field = models.CharField(max_length=50)
    value = models.JSONField()

# Hunt và Validate bằng NFT Được validate và donate sẽ thăng hạng NFT.
# Một người được sở hữu nhiều NFT và chọn NFT để hunt hoặc validate
