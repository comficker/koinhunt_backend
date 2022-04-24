import time
import requests
from datetime import datetime
from utils.helpers import link_define
from utils.handle_queue import TokenSchema, ProjectSchema, PriceSchema, EventSchema
from urllib.parse import urlparse

ONE_DAY = 86400
headers = {
    'authority': 'graphql-gateway.axieinfinity.com',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Microsoft Edge";v="96"',
    'accept': '*/*',
    'content-type': 'application/json',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
    'sec-ch-ua-platform': '"macOS"',
    'origin': 'https://marketplace.axieinfinity.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://marketplace.axieinfinity.com/',
    'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
}
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


def to_token(data):
    short_report = clean_short_report(data["market_data"])
    domain = urlparse(data["links"]["homepage"][0]).netloc

    tk = TokenSchema({})
    tk.project = {
        "homepage": domain,
        "name": data["name"],
    }
    tk.chain_id = data["asset_platform_id"]
    tk.address = data["platforms"][data.get("asset_platform_id")]
    tk.name = data["name"]
    tk.symbol = data["symbol"]
    tk.description = data["description"]["en"][:300]
    tk.media = data["image"]["large"]
    if data["market_data"].get("total_supply"):
        tk.total_supply = data["market_data"]["total_supply"]
    if data["market_data"]["circulating_supply"]:
        tk.circulating_supply = data["market_data"]["circulating_supply"]
    tk.external_ids = {"coingecko": data["id"]}
    short_report = short_report
    tk.price_init = short_report.get("atl", 0)
    tk.price_current = short_report.get("price_current", 0)
    tk.price_ath = short_report.get("ath", 0)
    tk.price_atl = short_report.get("atl", 0)
    tk.platforms = data.get("platforms")
    tk.push()
    project = ProjectSchema({
        "name": data["name"],
        "description": data["description"]["en"][:300],
        "media": data["image"]["large"],
        "links": extract_links(data["links"]),
        "homepage": domain,
        "categories": data.get("categories")
    })
    for key in data.get("platforms", {}).keys():
        chain_raw = CHAIN_MAPPING.get(key)
        if chain_raw:
            project.chains.append(chain_raw["name"])
    for key in ["twitter_followers", "telegram_channel_user_count", "facebook_likes"]:
        sm = SOCIAL_MAPPING.get(key, None)
        if data["community_data"][key] is None or sm is None or not data["links"].get(sm["link"]):
            continue
        if project:
            project.socials[sm["social_field"]] = {
                "id": data["links"].get(sm["link"]),
                "total": data["community_data"][key]
            }
    project.push()
    for ticker in data["tickers"]:
        event = EventSchema({
            "event_name": "listing",
            "project": {
                "homepage": domain,
                "name": data["name"],
            },
            "targets": [{
                "homepage": urlparse(ticker["trade_url"]).netloc if ticker.get("trade_url") else None,
                "id_string": ticker["market"]["identifier"],
                "name": ticker["market"]["name"]
            }],
            "meta": {
                "symbol": data["symbol"],
                "target": ticker.get("target"),
                "trade_url": ticker.get("trade_url"),
            }
        })
        event.push()


# ======================== FETCH ======
def fetch_cgk(break_wallet=-1, enable_detail=True, enable_ranges=None):
    if enable_ranges is None:
        enable_ranges = [1, 90, 180]
    now = datetime.now().timestamp()
    req = requests.get(
        "https://api.coingecko.com/api/v3/coins/list",
        headers=headers
    )
    coins = req.json()
    total = len(coins)
    index = 0
    for coin in coins:
        if coin["id"]:
            index = index + 1
            print("index: {},name: {}, percent: {}".format(index, coin["id"], (index / total) * 100))
            if break_wallet >= 0:
                if index == break_wallet:
                    break_wallet = -1
                else:
                    continue
            if coin["id"].startswith(("0-5x-", "1x-", "2x-", "3x-", "4x-", "5x-")):
                continue
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
                        to_token(coin_data)
                        break
                    except Exception as e:
                        print(e)
                        time.sleep(10)
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
                    while True:
                        try:
                            req = requests.get(
                                urls["chart"],
                                params={"vs_currency": "usd", "from": r["fr"], "to": r["to"]}
                            )
                            coin_data_price = req.json()
                            es = PriceSchema(
                                {"source": "coingecko", "id": coin["id"], "rg": "m5", "data": coin_data_price["prices"]}
                            )
                            es.push()
                            break
                        except Exception as e:
                            print(e)
                            time.sleep(10)
                            continue
