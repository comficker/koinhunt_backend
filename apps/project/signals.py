import os

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.governance.models import TokenContract
from apps.project.models import Event, Token, Project, Incentive, Contribute, Validate, IncentiveDistribution
from django.contrib.contenttypes.models import ContentType
from utils.contracts import get_power
from django.utils import timezone
from django.db.models import Sum


def get_token_reward():
    token_reward, _ = TokenContract.objects.get_or_create(
        address=os.getenv("ADDR_TOKEN"),
        defaults={
            "name": "KH Token",
            "symbol": "KH"
        }
    )
    return token_reward


def make_init_contrib(instance):
    ct = ContentType.objects.get_for_model(instance)
    contrib = Contribute.objects.create(
        wallet=instance.wallet,
        nft=instance.nft,
        target_content_type=ct,
        target_object_id=instance.id,
        field="INIT",
        data={}
    )
    reward = int(os.getenv("REWARD_BASE"))
    power_target = float(os.getenv("REWARD_POWER"))
    if instance is Project:
        power_target = 3 * float(os.getenv("REWARD_POWER"))
    Incentive.objects.create(
        contribute=contrib,
        reward_token=get_token_reward(),
        reward_total=reward,
        reward_remain=reward,
        power_target=power_target,
        is_active=True,
    )
    Validate.objects.create(
        contribute=contrib,
        wallet=instance.wallet,
        nft=instance.nft,
        power=get_power(instance)
    )

    if instance.meta is None:
        instance.meta = {}
    instance.meta["contrib"] = contrib.id
    instance.save()


@receiver(post_save, sender=Project)
def on_project_post_save(sender, instance, created, *args, **kwargs):
    if os.getenv("REWARD_BASE") and created:
        make_init_contrib(instance)


@receiver(post_save, sender=Event)
def on_event_post_save(sender, instance, created, *args, **kwargs):
    if os.getenv("REWARD_BASE") and created:
        make_init_contrib(instance)


@receiver(post_save, sender=Token)
def on_token_post_save(sender, instance, created, *args, **kwargs):
    if os.getenv("REWARD_BASE") and created:
        make_init_contrib(instance)


@receiver(post_save, sender=Contribute)
def on_contrib_post_save(sender, instance, created, *args, **kwargs):
    if not created:
        for incentive in instance.incentives.filter(is_active=True, reward_total__gt=0):
            power_target = incentive.power_target
            if incentive.due_date and incentive.due_date >= timezone.now():
                power_target = instance.validation_score
            if power_target > 0:
                for validate in instance.validates.all():
                    p = instance.power / power_target
                    IncentiveDistribution.objects.create(
                        validate=validate,
                        incentive=incentive,
                        earned=p * incentive.reward_total
                    )
