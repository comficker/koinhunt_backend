import random
import os
import json
from datetime import datetime, timezone
from utils.wallets import operators
from utils.helpers import link_define
from apps.media.models import Media
from apps.project.models import Token, TokenPrice, Project, Term, ProjectTerm, Event, Wallet, SocialTracker

CHAIN_MAPPING = {
    "binance-smart-chain": {
        "name": "Binance Smart Chain",
        "id_string": "binance-smart-chain",
        "description": "A Parallel Binance Chain to Enable Smart Contracts"
    },
    "ronin": {
        "name": "Ronin",
        "id_string": "ronin",
        "description": "The Ronin Block Explorer is an analytics platform for Ronin, "
                       "an Ethereum side-chain built by Sky Mavis."
    },
    "ethereum": {
        "name": "Ethereum",
        "id_string": "ethereum",
        "description": "Ethereum is a decentralized, open-source blockchain with smart contract functionality. "
                       "Ether is the native cryptocurrency of the platform."
    },
    "xdai": {
        "name": "xDai Chain",
        "id_string": "xdai",
        "description": "Dai is a stablecoin cryptocurrency which aims to keep its value as close to one United States dollar as possible through an automated system of smart contracts on the Ethereum blockchain."
    },
    "polygon-pos": {
        "name": "Polygon PoS",
        "id_string": "polygon-pos",
        "description": "Polygon PoS is a layer 2 scaling solution that achieves unprecedented transaction speed and cost savings by utilizing side-chains for transaction processing..."
    },
    "huobi-token": {
        "name": "Huobi-Token",
        "id_string": "huobi-token",
        "description": "Huobi Token,HT (Huobi Token) is a blockchain-powered loyalty point system. It is the only token that Huobi officially launched. "
    },
    "optimistic-ethereum": {
        "name": "Optimism",
        "id_string": "optimistic-ethereum",
        "description": "Optimism is a Layer 2 Optimistic Rollup network designed to utilize the strong security guarantees of Ethereum while reducing its cost and latency."
    },
    "harmony-shard-0": {
        "name": "Harmony One",
        "id_string": "harmony-shard-0",
        "description": "To scale trust and create a radically fair economy. Harmony is a fast and open blockchain for decentralized applications. "
    },
    "avalanche": {
        "name": "Avalanche",
        "id_string": "avalanche",
        "description": "Avalanche is a decentralized, open-source blockchain with smart contract functionality. AVAX is the native cryptocurrency of the platform."
    },
    "arbitrum-one": {
        "name": "Arbitrum One",
        "id_string": "arbitrum-one",
        "description": "Arbitrum is an Optimistic Rollup built to scale Ethereum by @OffchainLabs"
    },
    "sora": {
        "name": "Sora",
        "id_string": "sora",
        "description": "The SORA Network excels at providing tools for decentralized applications that use digital assets, such as atomic token swaps, bridging tokens to other chains."
    },
    "fantom": {
        "name": "Fantom",
        "id_string": "fantom",
        "description": "Fantom is a highly scalable blockchain platform for DeFi, crypto dApps, and enterprise applications."
    }
}
SOCIAL_MAPPING = {
    "twitter_followers": {
        "link": "twitter_screen_name",
        "social_metric": "follower_twitter",
        "social_field": "twitter"
    },
    "telegram_channel_user_count": {
        "link": "telegram_channel_identifier",
        "social_metric": "follower_telegram",
        "social_field": "telegram_channel"
    },
    "facebook_likes": {
        "link": "facebook_username",
        "social_metric": "follower_facebook",
        "social_field": "facebook"
    }
}


# ======================== HELPER ======
def extract_links(links):
    out = []
    for key in links.keys():
        if type(links[key]) is list:
            for link in links[key]:
                if link != "" and link:
                    out.append(link_define(link))
        elif type(links[key]) is dict:
            out = out + extract_links(links[key])
        else:
            if key == "twitter_screen_name":
                link = link_define("https://twitter.com/{}".format(links[key]))
            elif key == "facebook_username":
                link = link_define("https://www.facebook.com/{}".format(links[key]))
            elif key == "telegram_channel_identifier":
                link = link_define("https://t.me/{}".format(links[key]))
            else:
                link = link_define(links[key])
            if link:
                out.append(link)
    return out


def clean_short_report(market_data):
    if type(market_data.get("ath")) is dict:
        pac = 0
        pcc = 0
        if market_data["atl"].get("usd", 0) > 0:
            pac = round(market_data["ath"].get("usd", 0) / market_data["atl"].get("usd", 0))
            pcc = round(market_data["current_price"].get("usd", 0) / market_data["atl"].get("usd", 0))
        return {
            "pac": pac,
            "pcc": pcc,
            "price_current": market_data["current_price"].get("usd", 0),
            "ath": market_data["ath"].get("usd", 0),
            "ath_date": market_data["ath_date"].get("usd", 0),
            "atl": market_data["atl"].get("usd", 0),
            "atl_date": market_data["atl_date"].get("usd", 0),
            "total_volume": market_data["total_volume"].get("usd", 0),
            "high_24h": market_data["high_24h"].get("usd", 0),
            "low_24h": market_data["low_24h"].get("usd", 0),
            "price_change_percentage_24h": market_data.get("price_change_percentage_24h", 0)
        }
    return market_data


# ======================== HANDLE ======
def handle_data_token(data, wallet):
    if data.get("asset_platform_id") is None or data["symbol"] is None or len(data["symbol"]) > 42:
        return None
    if data["platforms"][data["asset_platform_id"]] == "" or data["image"]["large"] == "missing_large.png":
        return
    token = Token.objects.filter(
        chain_id=data["asset_platform_id"],
        address=data["platforms"][data.get("asset_platform_id")]
    ).first()
    project = None
    short_report = clean_short_report(data["market_data"])
    if token is None:
        media = Media.objects.save_url(data["image"]["large"])
        token = Token.objects.create(
            chain_id=data["asset_platform_id"],
            address=data["platforms"][data.get("asset_platform_id")],
            name=data["name"],
            symbol=data["symbol"],
            description=data["description"]["en"][:300],
            media=media,
            total_supply=data["market_data"]["total_supply"] if data["market_data"]["total_supply"] else 0,
            circulating_supply=data["market_data"]["circulating_supply"] if data["market_data"][
                "circulating_supply"] else 0,
            external_ids={"coingecko": data["id"]},
            wallet=wallet,

            short_report=short_report,
            price_init=short_report.get("atl", 0),
            price_current=short_report.get("price_current", 0),
            price_ath=short_report.get("ath", 0),
            price_atl=short_report.get("atl", 0),
            platforms=data.get("platforms")
        )
        raw_project = {
            "name": data["name"],
            "description": data["description"]["en"][:300],
            "media": media,
            "main_token": token,
            "id_string": data["id"],
            "links": extract_links(data["links"]),
            "wallet": wallet
        }
        if data["links"]["homepage"][0]:
            project, _ = Project.objects.get_or_create(
                homepage=data["links"]["homepage"][0],
                defaults=raw_project
            )
        else:
            project, _ = Project.objects.get_or_create(
                id_string=data["id"],
                defaults=raw_project
            )
        project.save()
        if token not in project.tokens.all():
            project.tokens.add(token)

        for cat in data.get("categories"):
            if cat is None:
                continue
            term, _ = Term.objects.get_or_create(
                name=cat,
                taxonomy="category"
            )
            if term not in project.terms.all():
                ProjectTerm.objects.create(
                    project=project,
                    term=term
                )
    else:
        if token.external_ids is None:
            token.external_ids = {}
        if not token.external_ids.get("coingecko"):
            token.external_ids["coingecko"] = data["id"]

        token.short_report = short_report
        token.price_current = short_report.get("price_current", 0)
        token.price_ath = short_report.get("ath", 0)
        token.price_atl = short_report.get("atl", 0)
        token.platforms = data.get("platforms")
        token.save()

    if project is None:
        project = token.projects.first()
    if project:
        if project.socials is None:
            project.socials = {}
        for ticker in data["tickers"]:
            market, _ = Project.objects.get_or_create(
                id_string=ticker["market"]["identifier"],
                defaults={
                    "wallet": wallet,
                    "name": ticker["market"]["name"]
                }
            )
            if not Event.objects.filter(
                project=project,
                event_name=Event.EventNameChoice.LISTING,
                targets=market
            ).exists():
                event = Event.objects.create(
                    project=project,
                    event_name=Event.EventNameChoice.LISTING,
                    wallet=wallet,
                    meta={
                        "symbol": token.symbol,
                        "target": ticker.get("target"),
                        "trade_url": ticker.get("trade_url"),
                    }
                )
                event.targets.add(market)
            else:
                x = Event.objects.filter(
                    project=project,
                    event_name=Event.EventNameChoice.LISTING,
                    targets=market
                ).first()
                if x.meta is None:
                    x.meta = {}
                x.meta = {
                    **x.meta,
                    "symbol": token.symbol,
                    "target": ticker.get("target"),
                    "trade_url": ticker.get("trade_url"),
                }
                x.save()
        project.make_partners()
        ProjectTerm.objects.filter(
            project=project,
            term__taxonomy="chain"
        ).delete()
        pta = list(
            map(
                lambda t: t.term.id,
                ProjectTerm.objects.filter(project=project, term__taxonomy="chain")
            )
        )
        for key in data.get("platforms", {}).keys():
            chain_raw = CHAIN_MAPPING.get(key)
            if chain_raw:
                term, _ = Term.objects.get_or_create(
                    taxonomy="chain",
                    name=chain_raw.get("name"),
                    defaults={
                        "description": chain_raw.get("description")
                    }
                )
                if term.id not in pta:
                    ProjectTerm.objects.create(
                        project=project,
                        term=term,
                        meta={
                            "address": data["platforms"][key]
                        }
                    )
    if data["last_updated"]:
        token.time_check = data["last_updated"]
        for key in ["twitter_followers", "telegram_channel_user_count", "facebook_likes"]:
            sm = SOCIAL_MAPPING.get(key, None)
            if data["community_data"][key] is None or sm is None or not data["links"].get(sm["link"]):
                continue
            SocialTracker.objects.get_or_create(
                time_check=data["last_updated"],
                social_metric=sm["social_metric"],
                social_id=data["links"].get(sm["link"]),
                value=data["community_data"][key]
            )
            if project:
                project.socials[sm["social_field"]] = {
                    "id": data["links"].get(sm["link"]),
                    "total": data["community_data"][key]
                }
        if project:
            project.save()
    return token


def handle_data_token_price(data, token):
    for item in data["prices"]:
        TokenPrice.objects.get_or_create(
            token=token,
            time_check=datetime.fromtimestamp(item[0] / 1000, timezone.utc),
            defaults={
                "price_open": item[1],
                "price_close": item[1],
                "price_avg": item[1],
            }
        )


# ======================== HANDLE QUEUE ======
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
