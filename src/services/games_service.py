from datetime import timezone
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from src.api.responses import GameResponse, TeamResponse
from src.services.sofascore_client import SofaScoreClient
import json

SOFASCORE_URL = "https://www.sofascore.com/api/v1/"

class GamesService:
    def __init__(self) -> None:
        self._base_url = SOFASCORE_URL
        self.sofascore = SofaScoreClient()

    def find_games(self):
        next_games: list[GameResponse]= []
        data:dict[str,Any] = self.sofascore.get_games()
        data = data["next"]["events"] + data["live"]["events"]  + data["last"]["events"] 
        print(json.dumps(data))
        for i in data:
            date_utc = datetime.fromtimestamp(i["startTimestamp"], tz=timezone.utc)

            date_germany = date_utc.astimezone(ZoneInfo("Europe/Berlin"))
            date_brazil = date_utc.astimezone(ZoneInfo("America/Sao_Paulo"))
            
            next_games.append(GameResponse(
                id=i["id"],
                season=i["season"]["name"],
                round=i["roundInfo"]["round"] if i.get("roundInfo") else None,
                start_at_germany=date_germany,
                start_at_brazil=date_brazil,
                home_team=self._get_team_response(i["homeTeam"]),
                away_team=self._get_team_response(i["awayTeam"]),
                home_score=i["homeScore"]["current"] if i.get("homeScore") else None,
                away_score=i["awayScore"]["current"] if i.get("awayScore") else None
            ))
            
        return next_games
                              
    def _get_team_response(self, team:dict[str,Any]) -> TeamResponse:
        return TeamResponse(
                    id=team["id"],
                    name=team["name"],
                    color=team["teamColors"]["primary"] if team.get("teamColors") else None,
                    secondary_color=team["teamColors"]["secondary"] if team.get("teamColors") else None,
                    text_color=team["teamColors"]["text"] if team.get("teamColors") else None,
                    name_code=team["nameCode"],
                    image_url= f"https://img.sofascore.com/api/v1/team/{team["id"]}/image"
        )