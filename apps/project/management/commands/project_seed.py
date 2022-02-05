import os

from django.core.management.base import BaseCommand, CommandError
from apps.project.models import Project, Term, Event
from apps.media.models import Media
from apps.authentication.models import Wallet
import json
import datetime


def link_define(url):
    # []
    if "facebook" in url:
        title = "Facebook"
    elif "twitter" in url:
        title = "Twitter"
    elif "telegram" in url:
        title = "Telegram"
    elif "t.me" in url:
        title = "Telegram"
    elif "youtube" in url:
        title = "Youtube"
    elif "tiktok" in url:
        title = "Tiktok"
    elif "reddit" in url:
        title = "Reddit"
    elif "medium" in url:
        title = "Medium"
    elif "discord" in url:
        title = "Discord"
    else:
        title = "Website"
    return {
        "url": url,
        "title": title
    }


class Command(BaseCommand):

    def handle(self, *args, **options):
        wallet, _ = Wallet.objects.get_or_create(
            address=os.getenv("MANAGER_WALLET")
        )
        with open('unique_out.json') as json_file:
            dataset = json.load(json_file)
            for data in dataset:
                title = data.get("title")
                description = data.get("des")
                links = list(map(lambda x: link_define(x), data.get("links")))
                if not Project.objects.filter(name=title).exists():
                    media = None
                    if data.get("img"):
                        media = Media.objects.save_url(data.get("img"))
                    project = Project.objects.create(
                        name=title,
                        description=description[0:599] if description else None,
                        media=media,
                        hunter=wallet,
                        meta={
                            "links": links,
                            "features": [],
                            "last_price": 0,
                            "market_cap": 0,
                            "max_supply": 0,
                        }
                    )
                    # ADD TERM
                    term = data.get("cat")[data.get("cat").find("(") + 1:data.get("cat").find(")")]
                    category, _ = Term.objects.get_or_create(
                        name=term,
                        taxonomy="category"
                    )
                    project.terms.add(category)
                    # ADD EVENT
                    try:
                        start_date = datetime.datetime.strptime('3 JANUARY 2022', '%d %B %Y')
                        Event.objects.create(
                            event_name=Event.EventNameChoice.LAUNCH,
                            project=project,
                            event_date_start=start_date
                        )
                    except Exception as e:
                        print(e)
                    print(project.name)
