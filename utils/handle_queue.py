import random
import os
import json
from datetime import datetime, timezone
from utils.wallets import operators
from apps.media.models import Media
from apps.project.models import Token, TokenPrice, Project, Term, ProjectTerm, Event, Wallet
from kafka import KafkaProducer, KafkaConsumer
from urllib.parse import urlparse
from django.utils.text import slugify

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKERS"),
    sasl_plain_username=os.getenv("KAFKA_USERNAME"),
    sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
    security_protocol="SASL_SSL",
    sasl_mechanism="PLAIN",
)


def make_project(raw, wallet):
    project = None
    if raw.get("homepage"):
        homepage = raw["homepage"].strip()
        if homepage.startswith("http") or homepage.startswith("https"):
            homepage = urlparse(homepage).netloc
        print(homepage)
        project, _ = Project.objects.get_or_create(
            homepage=homepage,
            defaults={
                "name": raw["name"],
                "wallet": wallet
            }
        )
    elif raw.get("id_string"):
        project, is_created = Project.objects.get_or_create(
            id_string=raw["id_string"],
            defaults={
                "name": raw["name"],
                "wallet": wallet
            }
        )
        if not is_created and project.homepage is None:
            project.homepage = raw["homepage"]
            project.save()
    elif raw.get("name"):
        project, _ = Project.objects.get_or_create(
            id_string=slugify(raw["name"]),
            defaults={
                "name": raw["name"],
                "wallet": wallet
            }
        )
    return project


class ProjectSchema:
    name = None
    description = None
    media = None
    homepage = None
    links = [
        # url
        # title
    ]
    features = []
    categories = []
    chains = []
    socials = {
        # "twitter": {
        #     "id": null,
        #     "total": 0
        # },
        # "telegram_channel": {},
        # "telegram_group": {},
        # "facebook": {}
    }
    meta = {}

    def __init__(self, kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def push(self):
        out = {
            "name": self.name,
            "description": self.description,
            "media": self.media,
            "homepage": self.homepage,
            "links": self.links,
            "features": self.features,
            "categories": self.categories,
            "chains": self.chains,
            "socials": self.socials,
            "meta": self.meta
        }
        producer.send(os.getenv("KAFKA_QUEUE_PROJECT"), json.dumps(out).encode("utf-8"))

    def transform(self):
        wallet, _ = Wallet.objects.get_or_create(
            address=random.choice(list(operators.keys())),
            chain="binance-smart-chain"
        )
        instance = make_project({
            "homepage": self.homepage,
            "name": self.name,
        }, wallet)
        if self.description:
            instance.description = self.description
        if self.media and instance.media is None:
            instance.media = Media.objects.save_url(self.media)
        if self.socials:
            instance.socials = {**self.socials}
        if self.links:
            instance.links = self.links
        if self.features:
            instance.features = self.features
        if self.meta:
            instance.meta = {**self.meta}
        if instance.terms.count() == 0:
            for item in self.categories:
                term, _ = Term.objects.get_or_create(name=item, taxonomy="category")
                if term not in instance.terms.all():
                    ProjectTerm.objects.create(project=instance, term=term)
            for item in self.chains:
                term, _ = Term.objects.get_or_create(name=item, taxonomy="chain")
                if term not in instance.terms.all():
                    ProjectTerm.objects.create(project=instance, term=term)
        instance.save()


class TokenSchema:
    project = {
        # "homepage": null,
        # "name": 0,
    }
    address = None
    chain_id = None
    name = None
    description = None
    media = None
    symbol = None
    decimal = 18
    total_supply = 0
    circulating_supply = 0
    price_init = 0
    price_current = 0
    price_ath = 0
    price_atl = 0
    tokenomics = None
    platforms = {
        # "ethereum": null,
        # "polygon-pos": null
    }
    short_report = {
        "ath": 0,
        "atl": 0,
        "pac": 0,
        "pcc": 0,
        "low_24h": 0,
        "ath_date": "2021-05-26T05:32:15.598Z",
        "atl_date": "2022-01-24T17:21:30.016Z",
        "high_24h": 0,
        "total_volume": 0,
        "price_current": 0,
        "price_change_percentage_24h": 0
    }
    external_ids = {
        # "coingecko": "aloha"
    }

    def __init__(self, kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def push(self):
        out = {
            "project": self.project,
            "name": self.name,
            "description": self.description,
            "chain_id": self.chain_id,
            "media": self.media,
            "symbol": self.symbol,
            "address": self.address,
            "decimal": self.decimal,
            "total_supply": self.total_supply,
            "circulating_supply": self.circulating_supply,
            "price_init": self.price_init,
            "price_current": self.price_current,
            "price_ath": self.price_ath,
            "price_atl": self.price_atl,
            "tokenomics": self.tokenomics,
            "platforms": self.platforms,
            "short_report": self.short_report,
            "external_ids": self.external_ids
        }
        producer.send(os.getenv("KAFKA_QUEUE_TOKEN"), json.dumps(out).encode("utf-8"))

    def transform(self):
        if self.chain_id is None or self.address is None:
            return
        wallet, _ = Wallet.objects.get_or_create(
            address=random.choice(list(operators.keys())),
            chain="binance-smart-chain"
        )
        project = make_project(self.project, wallet)
        token, is_created = Token.objects.get_or_create(
            chain_id=self.chain_id,
            address=self.address,
            defaults={
                "name": self.name,
                "symbol": self.symbol,
                "wallet": wallet
            }
        )
        if self.description:
            token.description = self.description
        if self.media and token.media is None:
            token.media = Media.objects.save_url(self.media)
        if self.total_supply:
            token.total_supply = self.total_supply
        if self.circulating_supply:
            token.circulating_supply = self.circulating_supply
        if self.external_ids:
            token.external_ids = {**self.external_ids}
        if self.short_report:
            token.short_report = {**self.short_report}
        if self.price_init:
            token.price_init = self.price_init
        if self.price_current:
            token.price_current = self.price_current
        if self.price_ath:
            token.price_ath = self.price_ath
        if self.price_atl:
            token.price_atl = self.price_atl
        if self.platforms:
            token.platforms = {**self.platforms}
        token.save()
        if project:
            if token not in project.tokens.all():
                project.tokens.add(token)
            if project.main_token is None:
                project.main_token = token
                project.save()


class EventSchema:
    source = None
    id = None
    event_name = None
    name = None
    description = None
    media = None
    meta = {}
    date_start_y = None
    date_start_mo = None
    date_start_d = None
    date_start_h = None
    date_start_m = None
    date_end_y = None
    date_end_mo = None
    date_end_d = None
    date_end_h = None
    date_end_m = None
    project = {
        # "homepage": null,
        # "name": 0,
    }
    targets = [
        # {
        #     "homepage": null,
        #     "name": 0,
        #     "id_string": 0
        # }
    ]

    def __init__(self, kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def push(self):
        out = {
            "source": self.source,
            "id": self.id,
            "event_name": self.event_name,
            "name": self.name,
            "description": self.description,
            "media": self.media,
            "date_start_y": self.date_start_y,
            "date_start_mo": self.date_start_mo,
            "date_start_d": self.date_start_d,
            "date_start_h": self.date_start_h,
            "date_start_m": self.date_start_m,
            "date_end_y": self.date_end_y,
            "date_end_mo": self.date_end_mo,
            "date_end_d": self.date_end_d,
            "date_end_h": self.date_end_h,
            "date_end_m": self.date_end_m,
            "project": self.project,
            "targets": self.targets,
            "meta": self.meta
        }
        producer.send(os.getenv("KAFKA_QUEUE_EVENT"), json.dumps(out).encode("utf-8"))

    def transform(self):
        wallet, _ = Wallet.objects.get_or_create(
            address=random.choice(list(operators.keys())),
            chain="binance-smart-chain"
        )
        project = make_project(self.project, wallet)
        if not project:
            return
        instance = None
        field_name = "meta__source__{}".format(self.source)
        if self.source and self.id:
            instance = Event.objects.filter(**{field_name: self.id}).first()
        if instance is None:
            instance, is_created = Event.objects.get_or_create(
                event_name=self.event_name,
                project=project,
                date_start_y=self.date_start_y,
                date_start_mo=self.date_start_mo,
                date_start_d=self.date_start_d,
                date_start_h=self.date_start_h,
                date_start_m=self.date_start_m,
                defaults={
                    "name": self.name,
                    "description": self.description[:600] if self.description else None,
                    "date_end_y": self.date_end_y,
                    "date_end_mo": self.date_end_mo,
                    "date_end_d": self.date_end_d,
                    "date_end_h": self.date_end_h,
                    "date_end_m": self.date_end_m,
                    "wallet": wallet,
                    "meta": {
                        **self.meta,
                        **{"meta__source__{}".format(self.source): self.id}
                    }
                }
            )
            if is_created:
                if self.media:
                    instance.media = Media.objects.save_url(self.media)
                    instance.save()
                if len(self.targets):
                    for item in self.targets:
                        target = make_project(item, wallet)
                        instance.targets.add(target)
        else:
            instance.date_start_y = self.date_start_y
            instance.date_start_mo = self.date_start_mo
            instance.date_start_d = self.date_start_d
            instance.date_start_h = self.date_start_h
            instance.date_start_m = self.date_start_m
            instance.date_end_y = self.date_end_y
            instance.date_end_mo = self.date_end_mo
            instance.date_end_d = self.date_end_d
            instance.date_end_h = self.date_end_h
            instance.date_end_m = self.date_end_m
            instance.save()


class PriceSchema:
    source = None
    id = None
    data = [
        # [1641297635870, 46803.15078633856]
    ]
    rg = TokenPrice.RangeChoice.M5

    def __init__(self, kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def push(self):
        out = {
            "source": self.source,
            "id": self.id,
            "data": self.data,
            "rg": self.rg
        }
        producer.send(os.getenv("KAFKA_QUEUE_PRICE"), json.dumps(out).encode("utf-8"))

    def transform(self):
        field_name = "external_ids__{}".format(self.source)
        token = Token.objects.filter(**{field_name: self.id}).first()
        if token is None:
            return
        for item in self.data:
            TokenPrice.objects.get_or_create(
                token=token,
                time_check=datetime.fromtimestamp(item[0] / 1000, timezone.utc),
                defaults={
                    "price_open": item[1],
                    "price_close": item[1],
                    "price_avg": item[1],
                    "range": self.rg
                }
            )


def handle_queue(queue_name):
    topic = os.getenv(queue_name)
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv("KAFKA_BROKERS"),
        sasl_plain_username=os.getenv("KAFKA_USERNAME"),
        sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
        auto_offset_reset="earliest",
        security_protocol="SASL_SSL",
        sasl_mechanism="PLAIN",
        request_timeout_ms=100000,
        session_timeout_ms=99000,
        max_poll_records=100,
    )
    for msg in consumer:
        data = json.loads(msg.value)
        if queue_name == "KAFKA_QUEUE_TOKEN":
            instance = TokenSchema(data)
            instance.transform()
        elif queue_name == "KAFKA_QUEUE_PRICE":
            instance = PriceSchema(data)
            instance.transform()
        elif queue_name == "KAFKA_QUEUE_EVENT":
            instance = EventSchema(data)
            instance.transform()
        elif queue_name == "KAFKA_QUEUE_PROJECT":
            instance = ProjectSchema(data)
            instance.transform()
    consumer.close()
