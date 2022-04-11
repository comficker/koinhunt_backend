import time
import os
import json
import requests
from datetime import datetime
from apps.base.rabbitmq import channel

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

DEFAULT_PJ = {
    "meta": None,
    "name": None,
    "description": None,
    "media": None,
    "homepage": None,
    "links": None,
    "features": None,
    "socials": None,
    "launch_date": None,

    "terms": [],
    "events": [],
    "tokens": []
}


# ======================== FETCH ======
def fetch_cgk(break_wallet=-1, enable_detail=True, enable_ranges=None, push_file=False, push_mq=False):
    if enable_ranges is None:
        enable_ranges = [1, 90, 180]
    now = datetime.now().timestamp()
    req = requests.get(
        "https://api.coingecko.com/api/v3/coins/list",
        headers=headers
    )
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
            if break_wallet >= 0:
                if index == break_wallet:
                    break_wallet = -1
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
