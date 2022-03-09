from django.core.management.base import BaseCommand
from apps.project.models import Token, Contribute, Validate, Project, SocialTracker

SOCIAL_MAPPING = {
    "twitter_screen_name": {
        "link": "follower_twitter",
        "origin": "twitter_followers",
        "social_field": "twitter"
    },
    "telegram_channel_identifier": {
        "link": "follower_telegram",
        "origin": "telegram_channel_user_count",
        "social_field": "telegram_channel"
    },
    "facebook_username": {
        "link": "follower_facebook",
        "origin": "facebook_likes",
        "social_field": "facebook"
    }
}


class Command(BaseCommand):

    def handle(self, *args, **options):
        items = Project.objects.all()
        for item in items:
            token = item.main_token
            if item.socials is None:
                item.socials = {}
            if token and item.meta.get("social"):
                community_data = item.meta.get("social")
                if item.links is None:
                    continue
                for link in item.links:
                    k = None
                    v = None
                    if "https://twitter.com/" in link["url"]:
                        k = "twitter_screen_name"
                        v = link["url"].replace("https://twitter.com/", "")
                    elif "https://www.facebook.com/" in link["url"]:
                        k = "facebook_username"
                        v = link["url"].replace("https://www.facebook.com/", "")
                    elif "https://t.me/" in link["url"]:
                        k = "telegram_channel_identifier"
                        v = link["url"].replace("https://t.me/", "")
                    if k and v:
                        sm = SOCIAL_MAPPING.get(k, None)
                        print("{}_{}_{}".format(sm["link"], v, community_data[sm["origin"]]))
                        if community_data[sm["origin"]] and item.socials.get(sm["social_field"]) is None:
                            SocialTracker.objects.get_or_create(
                                time_check=token.time_check,
                                social_metric=sm["link"],
                                social_id=v,
                                value=community_data[sm["origin"]]
                            )
                        item.socials[sm["social_field"]] = {
                            "id": v,
                            "total": community_data[sm["origin"]]
                        }
            item.save()
