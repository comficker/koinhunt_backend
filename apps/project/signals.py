from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.project.models import Event


@receiver(post_save, sender=Event)
def on_post_save(sender, instance, created, *args, **kwargs):
    if instance.token:
        instance.token.calculate_score()
        if instance.event_name == "launch":
            instance.token.calculate_launch_date()
