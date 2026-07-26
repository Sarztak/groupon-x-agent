from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def enrich_url(raw_url: str, utm_content: str = "auto_reply") -> str:
    parsed = urlparse(raw_url)
    params = parse_qsl(parsed.query) + [
        ("utm_source",   "x_organic"),
        ("utm_medium",   "social_bot"),
        ("utm_campaign", "groupon_social"),
        ("utm_content",  utm_content),
    ]
    return urlunparse(parsed._replace(query=urlencode(params)))
