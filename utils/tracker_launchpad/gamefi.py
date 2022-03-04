import requests


# https://hub.gamefi.org/api/v1/home/performances
# https://hub.gamefi.org/api/v1/pools/token-type?token_type=erc20&page=1&limit=5
# https://hub.gamefi.org/api/v1/pools/upcoming-pools?token_type=erc20&limit=20&page=1&is_private=3
# https://hub.gamefi.org/api/v1/pools/complete-sale-pools?token_type=erc20&limit=10&page=1
def fetch_gafi(page):
    url = "https://hub.gamefi.org/api/v1/pools/"
    req = requests.get(url, {
        "page": page,
        "limit": 10
    })
    data = req.json()
    results = data["data"]["data"]
    for item in results:
        print(item)


def fetch_perform():
    url = "https://hub.gamefi.org/api/v1/home/performances"
    req = requests.get(url)
