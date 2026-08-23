from src.services.scraper import re, unescape


def extract_urls(html: str) -> list[str]:
    return [
        unescape(url)
        for url in re.findall(r'data-url="([^"]*)"', html)
        if "cloud.xbotgo" in url.lower()
    ]


def test_extract_xbotgo_data_url():
    html = '''<div data-url="https://cloud.xbotgo.net/live?userId=123&amp;language=de_DE&amp;region=EU"></div>'''
    assert extract_urls(html) == [
        "https://cloud.xbotgo.net/live?userId=123&language=de_DE&region=EU"
    ]
