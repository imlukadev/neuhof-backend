import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Any

class SofaScoreClient:
    BASE_URL = "https://www.sofascore.com"
    TEAM_ID = 323243

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()

        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        return webdriver.Chrome(options=options)

    def _get_json(self, driver: webdriver.Chrome, url: str) -> dict[str,Any]:
        driver.get(url)

        body = driver.find_element("tag name", "body").text

        return json.loads(body)

    def get_next_events(self, driver: webdriver.Chrome) -> dict[str,Any]:
        url = (
            f"{self.BASE_URL}/api/v1/team/"
            f"{self.TEAM_ID}/events/next/0"
        )

        return self._get_json(driver, url)

    def get_last_events(self, driver: webdriver.Chrome) -> dict[str,Any]:
        url = (
            f"{self.BASE_URL}/api/v1/team/"
            f"{self.TEAM_ID}/events/last/0"
        )

        return self._get_json(driver, url)

    def get_live_events(self, driver: webdriver.Chrome) -> dict[str,Any]:
        url = (
            f"{self.BASE_URL}/api/v1/sport/"
            "football/events/live"
        )

        data =  self._get_json(driver, url)
        return {"events":[
            event
            for event in data.get("events", [])
            if (
                event.get("homeTeam", {}).get("id") == self.TEAM_ID
                or event.get("awayTeam", {}).get("id") == self.TEAM_ID
            )
        ]}

    def get_games(self) -> dict[str,Any]:
        driver = self._create_driver()

        try:
            next_events = self.get_next_events(driver)
            last_events = self.get_last_events(driver)
            live_events = self.get_live_events(driver)

            return {
                "next": next_events,
                "last": last_events,
                "live": live_events,
            }

        finally:
            driver.quit()