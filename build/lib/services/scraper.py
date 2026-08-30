import asyncio
import re
import time
from html import unescape
from threading import Lock

from fastapi import HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.config import settings


class NoTransmissionAvailableError(HTTPException):
    """Raised when no active XbotGo transmission is available."""


class XbotGoScraper:
    TRANSMISSION_ENDED_TEXT = "Übertragung beendet."

    def __init__(self) -> None:
        self._lock = Lock()

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()

        if settings.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        return webdriver.Chrome(options=options)

    def _find_urls(self, html: str) -> list[str]:
        data_urls = [
            unescape(url)
            for url in re.findall(r'data-url="([^"]*)"', html)
            if "cloud.xbotgo" in url.lower()
        ]

        return list(dict.fromkeys(data_urls))

    def _has_active_transmission(self, driver: webdriver.Chrome) -> bool:
        page_text = driver.find_element("tag name", "body").text

        return self.TRANSMISSION_ENDED_TEXT not in page_text

    def find_url(self) -> str:
        driver = self._create_driver()

        try:
            driver.get(settings.live_source_url)
            time.sleep(settings.scraper_wait_seconds)

            html = driver.execute_script(
                "return document.documentElement.outerHTML;"
            )

            urls = self._find_urls(html)

            if not urls:
                raise NoTransmissionAvailableError(
                    "Nenhuma transmissão XbotGo foi encontrada."
                )

            for url in urls:
                driver.get(url)
                time.sleep(settings.scraper_wait_seconds)

                if self._has_active_transmission(driver):
                    return url

            raise NoTransmissionAvailableError(
                "Não há transmissão disponível no momento."
            )

        finally:
            driver.quit()

    async def find_url_async(self) -> str:
        return await asyncio.to_thread(self.find_url_thread_safe)

    def find_url_thread_safe(self) -> str:
        # Selenium/Chrome is intentionally serialized: two simultaneous cache
        # misses should not start multiple browser instances.
        with self._lock:
            return self.find_url()