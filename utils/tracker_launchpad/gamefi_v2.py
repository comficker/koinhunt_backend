import datetime
import requests
from utils.helpers import link_define
from bs4 import BeautifulSoup
from apps.project.models import Event
from utils.handle_queue import TokenSchema, ProjectSchema, PriceSchema, EventSchema
from urllib.parse import urlparse


# https://gamefi.org/_next/data/j2IBBPgfewVJN3U6gZr3C/hub/aspo-world.json?slug=aspo-world
# https://gamefi.org/_next/data/j2IBBPgfewVJN3U6gZr3C/hub.json?page=1&per_page=10&sort_by=created_at&sort_order=desc
# https://v2.gamefi.org/api/v1/pools/complete-sale-pools?token_type=erc20&limit=10&page=1
def fetch(key, page):
    url = "https://gamefi.org/_next/data/{key}/hub.json".format(
        key=key,
        page=page
    )
    req = requests.get(url, {
        "page": page,
        "per_page": 10,
        "sort_by": "created_at"
    })
    data_req = req.json()
    results = data_req["pageProps"]["data"]["data"]
    for aggregator_short in results:
        if not aggregator_short["official_website"]:
            continue
        aggregator = fetch_aggregator(key, aggregator_short["slug"])
        tokens = get_tokens(aggregator, aggregator_short)
        for token in tokens:
            t = TokenSchema(token)
            t.push()
        # PROJECT
        project_infor = aggregator["projectInformation"]
        features = get_future(aggregator["game_features"])
        links, socials = get_social_link(project_infor)
        aggregator["category"] = aggregator["category"] + ",Game"
        investors = get_investor(project_infor["investors"])
        for investor in investors:
            e = EventSchema({
                "project": {
                    "name": aggregator_short.get("game_name"),
                    "homepage": project_infor["official_website"],
                },
                "event_name": Event.EventNameChoice.ADD_INVESTOR,
                "targets": [{
                    "name": investor
                }],
            })
            e.push()
        p = ProjectSchema({
            "homepage": urlparse(project_infor["official_website"]).netloc,
            "name": aggregator_short.get("game_name"),
            "description": aggregator_short["short_description"],
            "media": aggregator["icon_token_link"],
            "links": links,
            "features": features,
            "socials": socials,
            "categories": aggregator["category"].split(","),
        })
        p.push()
    if data_req["pageProps"]["data"] and data_req["pageProps"]["data"]["lastPage"] > page:
        print(page)
        fetch(key, page + 1)


def get_social_link(aggregator):
    links = []
    socials = {
        "twitter": None,
        "facebook": None,
        "discord": None,
        "youtube": None,
        "twitch": None,
        "telegram_channel": None,
        "telegram_group": None,
    }
    for field in [
        "discord_link",
        "facebook_link",
        "instagram_link",
        "official_telegram_link",
        "official_website",
        "tiktok_link",
        "twitch_link",
        "twitter_link",
        "youtube_link",
        "reddit_link",
        "medium_link",
        "announcement_telegram_link",
        "coinmartketcap_link",
    ]:
        link = aggregator[field]
        if link:
            link_dict = link_define(aggregator[field])
            if link_dict:
                links.append(link_dict)
            social_field = None
            social_id = None
            if field == "official_telegram_link":
                social_field = "telegram_group"
                social_id = link.replace("https://t.me/", "")
            elif field == "announcement_telegram_link":
                social_field = "telegram_channel"
                social_id = link.replace("https://t.me/", "")
            elif field == "facebook_link":
                social_field = "facebook"
                social_id = link.replace("https://www.facebook.com/", "")
            elif field == "discord_link":
                social_field = "discord"
                social_id = link.replace("https://discord.com/invite/", "")
            elif field == "twitter_link":
                social_field = "twitter"
                social_id = link.replace("https://twitter.com/", "")
            elif field == "twitch_link":
                social_field = "twitch"
                social_id = link.replace("", "")
            elif field == "youtube_link":
                social_field = "youtube"
                social_id = link.replace("https://www.youtube.com/channel/", "")
            if social_field:
                socials[social_field] = {
                    "id": social_id,
                    "total": 0
                }
    return links, socials


def get_investor(raw):
    excluded = [
        "As a leading producer",
        "distribute",
        "With over 95",
        "etc",
        "and many others.",
    ]
    results = []
    if raw:
        soup = BeautifulSoup(raw, 'html.parser')
        for item in soup.find_all("li"):
            if item.text:
                item.text.replace(" and many others", "")
                results.append(item.text)
        for item in soup.find_all("p"):
            if item.text:
                for txt2 in item.text.split(","):
                    for txt3 in txt2.split(": "):
                        arr = txt3.split(" - ")
                        text = arr[0].strip()
                        if 0 < len(text) < 26 and text not in excluded:
                            out = text.replace("etc.", "")
                            if len(out) > 0:
                                if out[-1] == ".":
                                    out = out[:-1]
                                results.append(out)
    return results


def get_future(raw):
    out = []
    if raw:
        soup = BeautifulSoup(raw, 'html.parser')
        for txt in soup.find_all("li"):
            out.append(txt.text)
        for txt in soup.find_all("p"):
            out.append(txt.text)
    return out


def get_tokens(agg, short_agg):
    tnm = agg["tokenomic"]
    token_utilities = []
    if tnm.get("token_utilities"):
        soup = BeautifulSoup(tnm.get("token_utilities"), 'html.parser')
        for txt in soup.find_all("li"):
            if txt != "":
                token_utilities.append(txt.text)
        for txt in soup.find_all("p"):
            if txt != "":
                token_utilities.append(txt.text)
    out = {
        "name": agg["game_name"],
        "description": short_agg["short_description"],
        "media": agg["icon_token_link"],
        "chain_id": tnm["network_chain"],
        "address": tnm["token_address"],
        "symbol": tnm["ticker"],
        "total_supply": float(tnm["token_supply"]) if tnm["token_supply"] else 0,
        "price_init": float(agg["token_price"]) if agg["token_price"] else 0,
        "price_current": float(tnm.get("price", 0)) if tnm.get("price", 0) else 0,
        "short_report": {
            "ath": 0,
            "atl": 0,
            "pac": 0,
            "pcc": 0,
            "low_24h": 0,
            "ath_date": None,
            "atl_date": None,
            "high_24h": 0,
            "total_volume": 0,
            "price_current": 0,
            "price_change_percentage_24h": 0
        },
        "meta": {
            "token_utilities": token_utilities,
        },
        "external_ids": {
            "cmc_id": tnm["cmc_id"]
        },
    }
    return [out]


def fetch_aggregator(key, id_string):
    url = "https://gamefi.org/_next/data/{key}/hub/{slug}.json?slug={slug}".format(
        key=key,
        slug=id_string
    )
    req = requests.get(url)
    if req.status_code == 200:
        return req.json().get("pageProps").get("data")
    return {}


def fetch_igo(tp="complete-sale-pools", page=1):
    # complete-sale-pools / mysterious-box
    url = "https://v2.gamefi.org/api/v1/pools/{}".format(tp)
    params = {
        "token_type": "erc20",
        "limit": 10,
        "page": page
    }
    req = requests.get(url, params)
    data_req = req.json()
    results = data_req["data"]["data"]
    for item in results:
        if item["start_join_pool_time"] and item["start_join_pool_time"] != "":
            date_start = datetime.datetime.fromtimestamp(int(item["start_join_pool_time"]))
        elif item["start_time"]:
            date_start = datetime.datetime.fromtimestamp(int(item["start_time"]))
        else:
            date_start = None
        if item["end_join_pool_time"] and item["end_join_pool_time"] != "":
            date_end = datetime.datetime.fromtimestamp(int(item["end_join_pool_time"]))
        elif item["finish_time"]:
            date_end = datetime.datetime.fromtimestamp(int(item["finish_time"]))
        else:
            date_end = None
        project_name = " ".join(item["title"].split(" ")[:-1])
        raw = {
            "source": "gamefi",
            "id": item["id"],
            "event_name": "igo",
            "name": item["title"],
            "description": item["description"],
            "media": item.get("banner"),
            "project": {
                "homepage": urlparse(item["website"]).netloc,
                "name": project_name
            },
            "targets": [{
                "homepage": "gamefi.org",
                "name": "GameFi"
            }],
            "meta": {
                "url": "https://gamefi.org/igo/{}".format(item["id"])
            }
        }
        if date_start:
            raw = {
                **raw,
                "date_start_y": date_start.year,
                "date_start_mo": date_start.month,
                "date_start_d": date_start.day,
                "date_start_h": date_start.hour,
                "date_start_m": date_start.minute,
            }
        if date_end:
            raw = {
                **raw,
                "date_end_y": date_end.year,
                "date_end_mo": date_end.month,
                "date_end_d": date_end.day,
                "date_end_h": date_end.hour,
                "date_end_m": date_end.minute,
            }
        e = EventSchema(raw)
        e.push()
        if item["release_time"]:
            date_start = datetime.datetime.fromtimestamp(int(item["release_time"]))
            raw = {
                **raw,
                "event_name": "release_token",
                "date_start_y": date_start.year,
                "date_start_mo": date_start.month,
                "date_start_d": date_start.day,
                "date_start_h": date_start.hour,
                "date_start_m": date_start.minute,
                "date_end_y": None,
                "date_end_mo": None,
                "date_end_d": None,
                "date_end_h": None,
                "date_end_m": None,
            }
            e = EventSchema(raw)
            e.push()
    if data_req["data"]["lastPage"] > page:
        fetch_igo(tp, page + 1)
