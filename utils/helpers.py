def link_define(url):
    if url is None or type(url) is not str:
        return None
    # []
    if "facebook" in url:
        title = "Facebook"
    elif "twitter" in url:
        title = "Twitter"
    elif "telegram" in url:
        title = "Telegram"
    elif "t.me" in url:
        title = "Telegram"
    elif "youtube" in url:
        title = "Youtube"
    elif "tiktok" in url:
        title = "Tiktok"
    elif "reddit" in url:
        title = "Reddit"
    elif "medium" in url:
        title = "Medium"
    elif "discord" in url:
        title = "Discord"
    else:
        title = "Website"
    return {
        "url": url,
        "title": title
    }