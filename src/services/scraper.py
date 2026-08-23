import asyncio
import re
import time
from html import unescape
from threading import Lock

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.config import settings


class XbotGoScraper:
    def __init__(self) -> None:
        self._lock = Lock()

    def find_url(self) -> str | None:
        options = Options()
        if settings.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        try:
            driver.get(settings.live_source_url)
            time.sleep(settings.scraper_wait_seconds)

            html = driver.execute_script(
                "return document.documentElement.outerHTML;"
            )

            data_urls = [
                unescape(url)
                for url in re.findall(r'data-url="([^"]*)"', html)
                if "cloud.xbotgo" in url.lower()
            ]

            unique_urls = list(dict.fromkeys(data_urls))
            return unique_urls[0] if unique_urls else None
        finally:
            driver.quit()

    async def find_url_async(self) -> str | None:
        return await asyncio.to_thread(self.find_url_thread_safe)

    def find_url_thread_safe(self) -> str | None:
        # Selenium/Chrome is intentionally serialized: two simultaneous cache misses
        # should not start two browser instances.
        with self._lock:
            return self.find_url()
