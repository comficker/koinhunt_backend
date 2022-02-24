import random
import time
import os
import json
import requests
from apps.project.models import Token, TokenPrice, Project, Term, ProjectTerm, TokenLog, Event, Wallet
from datetime import datetime, timezone
from apps.media.models import Media
from apps.base.rabbitmq import channel
from utils.helpers import link_define
from utils.wallets import operators

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
ONE_DAY = 86400


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
            price_current=data["market_data"]["price_current"].get("usd", 0),
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
        if project.meta is None:
            project.meta = {}
        project.meta["social"] = data.get("community_data")
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
        for ticker in data["tickers"]:
            market, _ = Project.objects.get_or_create(
                id_string=ticker["market"]["identifier"],
                name=ticker["market"]["name"],
                defaults={
                    "wallet": wallet
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
                        "target": "WBNB",
                        "trade_url": "https://pancakeswap.finance/swap?inputCurrency=0xe8176d414560cfe1bf82fd73b986823b89e4f545&outputCurrency=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
                    }
                )
                event.targets.add(market)

        ProjectTerm.objects.filter(
            project=project,
            term__taxonomy="chain"
        ).delete()
        pta = list(map(lambda x: x.term.id, ProjectTerm.objects.filter(project=project, term__taxonomy="chain")))
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
                            "address": data["platforms"]["key"]
                        }
                    )

    if data["last_updated"]:
        for key in ["twitter_followers", "telegram_channel_user_count", "facebook_likes"]:
            if data["community_data"][key] is None:
                continue
            TokenLog.objects.get_or_create(
                time_check=data["last_updated"],
                token=token,
                field=key,
                defaults={
                    "value": data["community_data"][key]
                }
            )
        for key in ["circulating_supply", "total_supply"]:
            if data["market_data"][key] is None:
                continue
            TokenLog.objects.get_or_create(
                time_check=data["last_updated"],
                token=token,
                field=key,
                defaults={
                    "value": data["market_data"][key]
                }
            )
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


def handle_queue_rabbitmq(ch, method, properties, body):
    data = json.loads(body)
    if method.encode()[7].decode("utf-8") == os.getenv("QUEUE_CGK_TOKEN"):
        wallet, _ = Wallet.objects.get_or_create(
            address=random.choice(list(operators.keys())),
            chain="binance-smart-chain"
        )
        handle_data_token(data, wallet)
    elif method.encode()[7].decode("utf-8") == os.getenv("QUEUE_CGK_PRICE"):
        token = Token.objects.filter(external_ids__coingecko=data.get("token_id")).first()
        if token:
            handle_data_token_price(data, token)


# ======================== FETCH ======
def fetch_cgk(break_wallet=None, enable_detail=True, enable_ranges=None, push_file=False, push_mq=False):
    if enable_ranges is None:
        enable_ranges = [1, 90, 180]
    now = datetime.now().timestamp()
    req = requests.get("https://api.coingecko.com/api/v3/coins/list")
    coins = req.json()
    if not os.path.exists("data/coingecko"):
        os.makedirs("data/coingecko")
    with open('data/coingecko/0_coins.json', 'w') as f:
        json.dump(coins, f, ensure_ascii=False, indent=2)
    total = len(coins)
    index = 0
    for coin in coins:
        if coin["id"]:
            index = index + 1
            print("index: {},name: {}, percent: {}".format(index, coin["id"], (index / total) * 100))
            # START CHECK AND SKIP
            if break_wallet:
                if coin["id"] == break_wallet:
                    break_wallet = None
                else:
                    continue
            if coin["id"].startswith(("0-5x-", "1x-", "2x-", "3x-", "4x-", "5x-")):
                continue
            # END CHECK AND SKIP
            path_token = "data/coingecko/{}/".format(coin["id"])
            path_prices = "{}/prices".format(path_token)
            if not os.path.exists(path_token):
                os.makedirs(path_token)
                os.makedirs(path_prices)
            urls = {
                "detail": "https://api.coingecko.com/api/v3/coins/{}".format(coin["id"]),
                "chart": "https://api.coingecko.com/api/v3/coins/{}/market_chart/range".format(coin["id"]),
            }
            # ======================= SEND TOKEN
            if enable_detail:
                while True:
                    try:
                        req = requests.get(urls["detail"])
                        coin_data = req.json()
                        if push_file:
                            with open("{path_token}/{timestamp}.json".format(
                                path_token=path_token,
                                timestamp=datetime.now().timestamp()
                            ), "w") as f:
                                json.dump(coin_data, f, ensure_ascii=False, indent=2)
                        if push_mq and os.getenv("QUEUE_CGK_TOKEN"):
                            channel.basic_publish(
                                exchange='',
                                routing_key=os.getenv("QUEUE_CGK_TOKEN"),
                                body=json.dumps(coin_data).encode("utf-8")
                            )
                        break

                    except Exception as e:
                        time.sleep(10)
                        print(e)
                        continue
            # ======================= SEND_PRICE
            data_ranges = [
                {"range": 180, "fr": now - ONE_DAY * 180, "to": now - ONE_DAY * 90},
                {"range": 90, "fr": now - ONE_DAY * 90, "to": now - ONE_DAY},
                {"range": 1, "fr": now - ONE_DAY, "to": now},
            ]
            if len(enable_ranges) > 0:
                for r in data_ranges:
                    if r["range"] not in enable_ranges:
                        continue
                    p = "{path_prices}/{range}.json".format(
                        path_prices=path_prices,
                        range=datetime.now().timestamp() if r["range"] == 1 else r["range"]
                    )
                    if not os.path.exists(p):
                        while True:
                            try:
                                req = requests.get(
                                    urls["chart"],
                                    params={
                                        "vs_currency": "usd",
                                        "from": r["fr"],
                                        "to": r["to"],
                                    }
                                )
                                coin_data_price = req.json()
                                if push_file:
                                    with open(p, "w") as f:
                                        json.dump(coin_data_price, f, ensure_ascii=False, indent=2)
                                if push_mq and os.getenv("QUEUE_CGK_PRICE"):
                                    channel.basic_publish(
                                        exchange='',
                                        routing_key=os.getenv("QUEUE_CGK_PRICE"),
                                        body=json.dumps({
                                            **coin_data_price,
                                            "token_id": coin["id"],
                                        }).encode("utf-8")
                                    )
                                break
                            except Exception as e:
                                time.sleep(10)
                                print(e)
                                continue


# ======================== READ ======

def read_data_local():
    index = 0
    root_data = "data/coingecko"
    dir_list = os.listdir("data/coingecko")
    dir_list.sort()
    for dir_name in dir_list:
        index = index + 1
        print(index)
        if index <= 5503:
            continue
        full_dir = "{}/{}".format(root_data, dir_name)
        if os.path.isdir(full_dir):
            files = []
            for sub_dir in os.listdir(full_dir):
                full_sub_dir = "{}/{}".format(full_dir, sub_dir)
                if os.path.isfile(full_sub_dir):
                    files.append(sub_dir)
            files.sort()
            for fn in files:
                if fn == ".DS_Store":
                    continue
                full_sub_dir = "{}/{}".format(full_dir, fn)
                with open(full_sub_dir, 'r') as j:
                    channel.basic_publish(
                        exchange='',
                        routing_key=os.getenv("QUEUE_CGK_TOKEN"),
                        body=json.dumps(json.loads(j.read()))
                    )

            full_dir_prices = "{}/{}".format(full_dir, "prices")
            if os.path.exists(full_dir_prices):
                for price_dir_name in os.listdir(full_dir_prices):
                    full_price_dir_name = "{}/{}".format(full_dir_prices, price_dir_name)
                    with open(full_price_dir_name, 'r') as j:
                        channel.basic_publish(
                            exchange='',
                            routing_key=os.getenv("QUEUE_CGK_PRICE"),
                            body=json.dumps({
                                **json.loads(j.read()),
                                "token_id": dir_name,
                            }).encode("utf-8")
                        )
