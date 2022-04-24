import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.governance.models import TokenContract
from apps.project.models import Event, Token, Project, Incentive, Contribute, Validate, IncentiveDistribution, Wallet
from django.contrib.contenttypes.models import ContentType
from utils.contracts import get_power
from django.utils import timezone
from utils.wallets import operators

REWARD_BASE = float(os.getenv("REWARD_BASE", "0"))


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
    reward = REWARD_BASE
    power_target = REWARD_BASE * 100
    if type(instance) is Project:
        reward = 5 * reward
        power_target = 5 * power_target
    Incentive.objects.create(
        contribute=contrib,
        reward_token=get_token_reward(),
        reward_total=reward,
        reward_remain=reward,
        power_target=power_target,
        is_active=True,
    )
    power = 0
    if instance.wallet.address in operators.keys():
        for w in operators.keys():
            wallet, _ = Wallet.objects.get_or_create(
                address=w,
                chain="binance-smart-chain"
            )
            init_validate = Validate.objects.create(
                contribute=contrib,
                wallet=instance.wallet,
                nft=instance.nft,
                power=get_power(instance) * 1.5
            )
            power = power + init_validate.power
    instance.refresh_from_db()
    if instance.meta is None:
        instance.meta = {}
    if type(instance) is Project:
        instance.score_hunt = power
    instance.meta["contrib"] = contrib.id
    instance.meta["contrib_reward"] = REWARD_BASE
    instance.init_power_target = power_target
    instance.save()


def check_contrib(instance):
    power_target_current = instance.target.score_validation
    for incentive in instance.incentives.filter(is_active=True, reward_total__gt=0):
        power_target = 0
        is_distributing = False
        if incentive.due_date and incentive.due_date >= timezone.now():
            if incentive.power_target == 0:
                power_target = power_target_current
            else:
                power_target = incentive.power_target
            is_distributing = True
        elif power_target_current >= incentive.power_target:
            power_target = incentive.power_target
            is_distributing = True
        if is_distributing:
            for validate in instance.validates.all():
                p = validate.power / power_target
                IncentiveDistribution.objects.create(
                    validate=validate,
                    incentive=incentive,
                    earned=p * incentive.reward_total
                )
            incentive.is_active = False
            incentive.save()
            if not instance.verified and instance.field == "INIT":
                instance.verified = True
                instance.target.verified = True
                instance.save()
                instance.target.save()


@receiver(post_save, sender=Project)
def on_project_post_save(sender, instance, created, *args, **kwargs):
    if os.getenv("REWARD_BASE") and created:
        make_init_contrib(instance)


@receiver(post_save, sender=Event)
def on_event_post_save(sender, instance, created, *args, **kwargs):
    if os.getenv("REWARD_BASE") and created:
        make_init_contrib(instance)
    instance.project.make_partners()


@receiver(post_save, sender=Token)
def on_token_post_save(sender, instance, created, *args, **kwargs):
    if os.getenv("REWARD_BASE") and created:
        make_init_contrib(instance)


@receiver(post_save, sender=Validate)
def on_validate_post_save(sender, instance, created, *args, **kwargs):
    if created:
        if instance.wallet.address in operators.keys():
            instance.power = 500
        else:
            instance.power = get_power(instance)
        instance.save()
        instance.contribute.get_validation_score()
        check_contrib(instance.contribute)
        contrib = instance.contribute
        contrib.score_detail[instance.wallet.id] = instance.power
        contrib.save()
        target = contrib.target
        target.score_detail[instance.wallet.id] = instance.power
        target.verified = target.score_validation >= target.init_power_target
        target.save()

