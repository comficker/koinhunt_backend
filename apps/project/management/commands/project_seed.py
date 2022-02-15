import os
from utils.helpers import link_define
from django.core.management.base import BaseCommand, CommandError
from apps.project.models import Project, Term, Event, ProjectTerm
from apps.media.models import Media
from apps.authentication.models import Wallet
import json
import datetime


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
                        wallet=wallet,
                        links=links,
                        meta={
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

                    ProjectTerm.objects.get_or_create(
                        term=category,
                        project=project
                    )
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
