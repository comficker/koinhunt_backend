import random
import requests
from apps.project.models import Token, TokenPrice, Project, Term, ProjectTerm, TokenLog, Event, Wallet
from datetime import datetime, timezone
from apps.media.models import Media
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
    }
}


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
        return {
            "current_price": market_data["current_price"].get("usd", 0),
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


def fetch_token_market_chart(token, token_id, fr, to):
    # NON_RANGE
    # Get historical market data include price, market cap, and 24h volume (granularity auto)
    # Minutely data will be used for duration within 1 day,
    # Hourly data will be used for duration between 1 day and 90 days,
    # Daily data will be used for duration above 90 days.

    # RANGE
    # Get historical market data include price, market cap, and 24h volume within a range of timestamp
    # Data granularity is automatic (cannot be adjusted)
    # 1 day from query time = 5 minute interval data
    # 1 - 90 days from query time = hourly data
    # above 90 days from query time = daily data (00:00 UTC)
    req = requests.get("https://api.coingecko.com/api/v3/coins/{}/market_chart/range".format(token_id), params={
        "vs_currency": "usd",
        "from": fr,
        "to": to,
    })
    data = req.json()
    if token is None:
        token = Token.objects.get(external_ids__coingecko=token_id)
    temp = 0
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


def fetch_token(token_id):
    url = "https://api.coingecko.com/api/v3/coins/{}".format(token_id)
    req = requests.get(url)
    wallet, _ = Wallet.objects.get_or_create(
        address=random.choice(list(operators.keys())),
        chain="binance-smart-chain"
    )
    data = req.json()
    if data.get("asset_platform_id") is None or data["platforms"][data["asset_platform_id"]] == "" or data["image"]["large"] == "missing_large.png" \
        or data["symbol"] is None or len(data["symbol"]) > 42:
        return None
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
            circulating_supply=data["market_data"]["circulating_supply"] if data["market_data"]["circulating_supply"] else 0,
            current_price=data["market_data"]["current_price"].get("usd", 0),
            init_price=short_report.get("atl", 0),
            short_report=short_report,
            external_ids={
                "coingecko": data["id"]
            },
            wallet=wallet
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

        for key in data.get("platforms").keys():
            chain_raw = CHAIN_MAPPING.get(key)
            if chain_raw:
                term, _ = Term.objects.get_or_create(
                    taxonomy="chain",
                    defaults={
                        "name": chain_raw.get("name"),
                        "description": chain_raw.get("description")
                    }
                )
                if term not in project.terms.all():
                    ProjectTerm.objects.create(
                        project=project,
                        term=term,
                        meta={
                            "address": data.get("platforms").get(key)
                        }
                    )
    else:
        token.short_report = short_report
        token.current_price = short_report.get("current_price", 0)
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


x = {
    "id": "step-hero",
    "symbol": "hero",
    "name": "Step Hero",
    "asset_platform_id": "ethereum",
    "platforms": {
        "ethereum": "0xa2881f7f441267042f9778ffa0d4f834693426be",
        "binance-smart-chain": "0x284ac5af363bde6ef5296036af8fb0e9cc347b41"
    },
    "categories": [
        "Music",
        "Non-Fungible Tokens (NFT)",
        "Binance Smart Chain Ecosystem"
    ],
    "description": {
        "en": "Step Hero ecosystem is the perfect combination of NFT gaming and DeFi that "
              "enables users to have fun and earn profit simultaneously. "
              "The comprehensive ecosystem comprises Step Hero RPG game, Heroes Farming, and NFT Marketplace. "
              "More than a game, Step Hero also has a strong community "
              "helping players on investing activites to earn money from game."
    },
    "links": {
        "homepage": [
            "https://stephero.io/",
            "",
            ""
        ],
        "blockchain_site": [
            "https://bscscan.com/token/0xE8176d414560cFE1Bf82Fd73B986823B89E4F545",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ],
        "official_forum_url": [
            "",
            "",
            ""
        ],
        "chat_url": [
            "https://www.facebook.com/StepHeroNFTs",
            "https://discord.com/invite/A5guPpQcdu",
            ""
        ],
        "announcement_url": [
            "https://stephero.medium.com/",
            ""
        ],
        "twitter_screen_name": "StepHeroNFTs",
        "facebook_username": "",
        "telegram_channel_identifier": "stephero_chat",
        "subreddit_url": "https://www.reddit.com/r/StepHero/",
        "repos_url": {
            "github": [],
            "bitbucket": []
        }
    },
    "image": {
        "large": "https://assets.coingecko.com/coins/images/17700/large/stephero.PNG?1629072670"
    },
    "contract_address": "0xe8176d414560cfe1bf82fd73b986823b89e4f545",
    "market_data": {
        "current_price": {
            "usd": 0.089745,
        },
        "ath": {
            "usd": 3.14,
        },
        "ath_date": {
            "usd": "2021-08-26T01:42:29.038Z",
        },
        "market_cap_rank": None,
        "fully_diluted_valuation": {},
        "total_volume": {
            "usd": 27674,
        },
        "high_24h": {
            "usd": 0.099119,
        },
        "low_24h": {
            "usd": 0.088258,
        },
        "price_change_24h": -0.00835868861,
        "price_change_percentage_24h": -8.5203,
        "price_change_percentage_7d": -11.17947,
        "price_change_percentage_14d": -22.70633,
        "price_change_percentage_30d": -60.72447,
        "price_change_percentage_60d": -84.70042,
        "price_change_percentage_200d": 0.0,
        "price_change_percentage_1y": 0.0,
        "market_cap_change_24h": 0.0,
        "market_cap_change_percentage_24h": 0.0,
        "total_supply": 100000000.0,
        "max_supply": None,
        "circulating_supply": 0.0,
        "last_updated": "2022-02-11T17:00:39.788Z"
    },
    "community_data": {
        "facebook_likes": None,
        "twitter_followers": 266251,
        "reddit_average_posts_48h": 0.0,
        "reddit_average_comments_48h": 0.0,
        "reddit_subscribers": 197,
        "reddit_accounts_active_48h": 8,
        "telegram_channel_user_count": 137018
    },
    "last_updated": "2022-02-11T17:00:39.788Z",
    "tickers": [
        {
            "base": "0XE8176D414560CFE1BF82FD73B986823B89E4F545",
            "target": "WBNB",
            "market": {
                "name": "PancakeSwap (v2)",
                "identifier": "pancakeswap_new",
            },
            "last": 0.0002162766588510402,
            "volume": 306430.5296362685,
            "trade_url": "https://pancakeswap.finance/swap?inputCurrency=0xe8176d414560cfe1bf82fd73b986823b89e4f545&outputCurrency=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
            "coin_id": "step-hero",
            "target_coin_id": "wbnb"
        }
    ]
}
