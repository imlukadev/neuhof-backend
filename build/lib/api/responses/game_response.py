from datetime import datetime
from pydantic import BaseModel


class TeamResponse(BaseModel):
    id: int
    name: str
    color:str | None = None
    secondary_color:str | None = None
    text_color:str | None = None
    name_code:str | None = None
    image_url: str | None  = None


class GameResponse(BaseModel):
    id: int | None = None
    season: str | None = None
    round: int | None = None
    start_at_germany: datetime
    start_at_brazil: datetime
    home_team: TeamResponse
    away_team: TeamResponse
    home_score: int | None = None
    away_score: int | None = None