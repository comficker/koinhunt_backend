import random
import os
import json
from apps.project.models import Token, Wallet, TokenContract, Project, Term, ProjectTerm, Event
from apps.media.models import Media
from utils.wallets import operators
from utils.coingecko import handle_data_token, handle_data_token_price
from utils.helpers import link_define
from datetime import datetime, timezone


def handle_queue_launchpad(data):
    # data = {
    #     "name": str,
    #     "description": str,
    #     "media": str,
    #     "homepage": str,
    #     "links": [str],
    #     "features": [str],
    #     "socials": {
    #         "twitter": str,
    #         "facebook": str,
    #         "telegram_channel": str,
    #         "telegram_group": str
    #     },
    #     "launch_date": int,
    #     "terms": [str],
    #     "tokens": [
    #         {
    #             "name": "",
    #             "description": "",
    #             "media": "",
    #             "chain_id": "",
    #             "address": "",
    #             "symbol": "",
    #             "decimal": "",
    #             "total_supply": "",
    #             "circulating_supply": "",
    #             "price_init": "",
    #             "price_current": "",
    #             "platforms": "",
    #             "short_report": "",
    #             "external_ids": {},
    #         }
    #     ],
    #     "events": [{
    #         "name": "",
    #         "description": "",
    #         "event_name": str,
    #         "event_date_start": int,
    #         "event_date_end": int,
    #         "targets": [str],
    #     }]
    # }

    if data["homepage"]:
        wallet, _ = Wallet.objects.get_or_create(
            address=random.choice(list(operators.keys())),
            chain="binance-smart-chain"
        )
        media = Media.objects.save_url(data["media"]) if data["media"] else None
        raw_project = {
            "name": data["name"],
            "description": data["description"][:300],
            "media": media,
            "links": list(map(lambda x: link_define(x), data["links"])),
            "wallet": wallet,
            "features": data["features"],
            "socials": data["socials"],
        }
        if data["launch_date"]:
            raw_project["launch_date"] = datetime.fromtimestamp(data["launch_date"], tz=timezone.utc)
        project, _ = Project.objects.get_or_create(
            homepage=data["links"]["homepage"][0],
            defaults=raw_project
        )
        for item in data["terms"]:
            term, _ = Term.objects.get_or_create(
                name=item,
                taxonomy="tag"
            )
            if term not in project.terms.all():
                ProjectTerm.objects.create(
                    project=project,
                    term=term
                )
        for item in data["tokens"]:
            raw = {
                "name": item["name"],
                "description": item["description"],
                "media": media,
                "symbol": item["symbol"],
                "decimal": item["decimal"],
                "total_supply": item["total_supply"],
                "circulating_supply": item["circulating_supply"],
                "price_init": item["price_init"],
                "price_current": item["price_current"],
                "platforms": item["platforms"],
                "short_report": item["short_report"],
                "external_ids": item["external_ids"],
            }
            token, _ = Token.objects.get_or_create(
                chain_id=item["chain_id"],
                address=item["address"],
                defaults=raw
            )
            project.main_token = token
        for item in data["events"]:
            event, _ = Event.objects.get_or_create(
                project=project,
                event_name=item["event_name"],
                defaults={
                    "wallet": wallet,
                    "meta": item["meta"]
                }
            )

            for target_name in item["targets"]:
                target, _ = Project.objects.get_or_create(
                    name=target_name,
                    defaults={
                        "wallet": wallet
                    }
                )
                if target not in event.targets.all():
                    event.targets.add(target)
        project.save()


def handle_queue_rabbitmq(ch, method, properties, body):
    data = json.loads(body)
    queue_name = method.encode()[7].decode("utf-8")
    if queue_name == os.getenv("QUEUE_CGK_TOKEN"):
        wallet, _ = Wallet.objects.get_or_create(
            address=random.choice(list(operators.keys())),
            chain="binance-smart-chain"
        )
        handle_data_token(data, wallet)
    elif queue_name == os.getenv("QUEUE_CGK_PRICE"):
        token = Token.objects.filter(external_ids__coingecko=data.get("token_id")).first()
        if token:
            handle_data_token_price(data, token)
    elif queue_name == os.getenv("QUEUE_PROJECT_NEW"):
        handle_queue_launchpad(data)
