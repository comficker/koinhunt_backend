import requests
from utils.helpers import link_define
from bs4 import BeautifulSoup
from apps.project.models import Event
import spacy

nlp = spacy.load("en_core_web_sm")


# https://hub.gamefi.org/api/v1/home/performances
# https://hub.gamefi.org/api/v1/pools/token-type?token_type=erc20&page=1&limit=5
# https://hub.gamefi.org/api/v1/pools/upcoming-pools?token_type=erc20&limit=20&page=1&is_private=3
# https://hub.gamefi.org/api/v1/pools/complete-sale-pools?token_type=erc20&limit=10&page=1
def fetch_gafi(page):
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
    url = "https://aggregator.gamefi.org/api/v1/aggregator"
    req = requests.get(url, {
        "page": page,
        "limit": 10
    })
    data_req = req.json()
    results = data_req["data"]["data"]
    for aggregator_short in results:
        aggregator = fetch_aggregator(aggregator_short["slug"])
        project_infor = aggregator["projectInformation"]

        features = get_future(aggregator["game_features"])
        tokens = get_tokens(aggregator)
        aggregator["category"] = aggregator["category"] + ",Game"
        links, socials = get_social_link(project_infor)

        investors = get_investor(project_infor["investors"])
        events = []
        for investor in investors:
            e = {
                "name": "",
                "description": "",
                "event_name": Event.EventNameChoice.ADD_INVESTOR,
                "event_date_start": None,
                "event_date_end": None,
                "targets": [investor],
            }
            events.append(e)
        data = {
            "name": aggregator_short.get("game_name"),
            "description": aggregator_short["short_description"],
            "media": aggregator["icon_token_link"],
            "homepage": project_infor["official_website"],
            "links": links,
            "features": features,
            "socials": socials,
            "launch_date": int,
            "terms": aggregator["category"],
            "tokens": tokens,
            "events": events
        }
        print(data)
        return
    if data_req["data"]["lastPage"] != data_req["data"]["page"]:
        fetch_gafi(page + 1)


def get_social_link(aggregator):
    links = []
    socials = {
        "twitter": str,
        "facebook": str,
        "discord": str,
        "youtube": str,
        "twitch": str,
        "telegram_channel": str,
        "telegram_group": str,
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
                socials[social_field] = social_id
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
    soup = BeautifulSoup(raw, 'html.parser')
    for txt in soup.find_all("li"):
        out.append(txt.text)
    for txt in soup.find_all("p"):
        out.append(txt.text)
    return out


def get_tokens(agg):
    tnm = agg["tokenomic"]
    token_utilities = []
    if tnm.get("token_utilities"):
        soup = BeautifulSoup(tnm.get("token_utilities"), 'html.parser')
        for txt in soup.find_all("li"):
            token_utilities.append(txt.text)
        for txt in soup.find_all("p"):
            token_utilities.append(txt.text)
    out = {
        "name": agg["game_name"],
        "description": agg["short_description"],
        "media": agg["icon_token_link"],
        "chain_id": "",
        "address": tnm["token_address"],
        "symbol": tnm["ticker"],
        "decimal": "",
        "total_supply": tnm["token_supply"],
        "circulating_supply": "",
        "price_init": agg["token_price"],
        "price_current": tnm.get("price", 0),
        "platforms": "",
        "short_report": "",
        "token_utilities": token_utilities,
        "external_ids": {
            "cmc_id": tnm["cmc_id"]
        },
    }
    return [out]


def fetch_aggregator(id_string):
    url = "https://aggregator.gamefi.org/api/v1/aggregator/slug/{}".format(id_string)
    req = requests.get(url)
    if req.status_code == 200:
        return req.json().get("data")
    return {}


def fetch_perform():
    url = "https://hub.gamefi.org/api/v1/home/performances"
    req = requests.get(url)
