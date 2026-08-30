from datetime import datetime, timezone
import time
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.api.responses import GameResponse, TeamResponse
from src.models.game import Game
from src.models.team import Team
from src.services.sofascore_client import SofaScoreClient


SOFASCORE_IMAGE_URL = "https://img.sofascore.com/api/v1/team/{}/image"


class GamesService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sofascore = SofaScoreClient()

    async def find_games(self) -> list[GameResponse]:
        """
        Busca os jogos salvos no banco.
        """
        result = await self.db.execute(
            select(Game)
            .options(
                selectinload(Game.home_team),
                selectinload(Game.away_team),
            )
            .order_by(Game.start_at)
        )

        games = result.scalars().all()

        return [
            self._game_to_response(game)
            for game in games
        ]

    def find_games_from_source(self) -> list[GameResponse]:
        """
        Busca os jogos diretamente do SofaScore.
        Não altera o banco.
        """
        data: dict[str, Any] = self.sofascore.get_games()

        events = (
            data.get("next", {}).get("events", [])
            + data.get("live", {}).get("events", [])
            + data.get("last", {}).get("events", [])
        )

        return [
            self._event_to_response(event)
            for event in events
        ]

    async def sync_games(self) -> list[GameResponse]:
        total_start = time.perf_counter()

        games = self.find_games_from_source()

        print(
            f"[SYNC] SofaScore + conversão: "
            f"{time.perf_counter() - total_start:.2f}s"
        )
        print(f"[SYNC] Jogos: {len(games)}")

        if not games:
            return []

        # ============================================================
        # 1. Coleta todos os times únicos dos jogos
        # ============================================================

        teams_by_external_id: dict[int, TeamResponse] = {}

        for game in games:
            teams_by_external_id[game.home_team.id] = game.home_team
            teams_by_external_id[game.away_team.id] = game.away_team

        team_ids = list(teams_by_external_id.keys())

        # ============================================================
        # 2. Busca todos os times existentes em UMA query
        # ============================================================

        start = time.perf_counter()

        result = await self.db.execute(
            select(Team).where(
                Team.external_id.in_(team_ids)
            )
        )

        existing_teams = result.scalars().all()

        print(
            f"[SYNC] SELECT teams: "
            f"{time.perf_counter() - start:.2f}s "
            f"({len(existing_teams)} encontrados)"
        )

        db_teams: dict[int, Team] = {
            team.external_id: team
            for team in existing_teams
        }

        # ============================================================
        # 3. Cria/atualiza os times em memória
        # ============================================================

        for team_response in teams_by_external_id.values():
            db_team = db_teams.get(team_response.id)

            if db_team is None:
                db_team = Team(
                    external_id=team_response.id,
                    name=team_response.name,
                    color=team_response.color,
                    secondary_color=team_response.secondary_color,
                    text_color=team_response.text_color,
                    name_code=team_response.name_code,
                    image_url=team_response.image_url,
                )

                self.db.add(db_team)
                db_teams[team_response.id] = db_team

            else:
                db_team.name = team_response.name
                db_team.color = team_response.color
                db_team.secondary_color = team_response.secondary_color
                db_team.text_color = team_response.text_color
                db_team.name_code = team_response.name_code
                db_team.image_url = team_response.image_url

        # Precisamos dos IDs dos novos times antes de criar os jogos.
        start = time.perf_counter()

        await self.db.flush()

        print(
            f"[SYNC] Flush teams: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # ============================================================
        # 4. Busca todos os jogos existentes em UMA query
        # ============================================================

        game_ids = [game.id for game in games]

        start = time.perf_counter()

        result = await self.db.execute(
            select(Game).where(
                Game.external_id.in_(game_ids)
            )
        )

        existing_games = result.scalars().all()

        print(
            f"[SYNC] SELECT games: "
            f"{time.perf_counter() - start:.2f}s "
            f"({len(existing_games)} encontrados)"
        )

        db_games: dict[int, Game] = {
            game.external_id: game
            for game in existing_games
        }

        # ============================================================
        # 5. Cria/atualiza os jogos em memória
        # ============================================================

        for game in games:
            home_team = db_teams[game.home_team.id]
            away_team = db_teams[game.away_team.id]

            start_at = game.start_at_germany.astimezone(
                timezone.utc
            )

            db_game = db_games.get(game.id)

            if db_game is None:
                db_game = Game(
                    external_id=game.id,
                    season=game.season,
                    round=game.round,
                    start_at=start_at,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_score=game.home_score,
                    away_score=game.away_score,
                )

                self.db.add(db_game)
                db_games[game.id] = db_game

            else:
                db_game.season = game.season
                db_game.round = game.round
                db_game.start_at = start_at
                db_game.home_team_id = home_team.id
                db_game.away_team_id = away_team.id
                db_game.home_score = game.home_score
                db_game.away_score = game.away_score

        # ============================================================
        # 6. Commit único
        # ============================================================

        start = time.perf_counter()

        await self.db.commit()

        print(
            f"[SYNC] Commit: "
            f"{time.perf_counter() - start:.2f}s"
        )

        print(
            f"[SYNC] TOTAL: "
            f"{time.perf_counter() - total_start:.2f}s"
        )

        return games

    def _event_to_response(
        self,
        event: dict[str, Any],
    ) -> GameResponse:
        date_utc = datetime.fromtimestamp(
            event["startTimestamp"],
            tz=timezone.utc,
        )

        return GameResponse(
            id=event["id"],
            season=event["season"]["name"],
            round=(
                event["roundInfo"]["round"]
                if event.get("roundInfo")
                else None
            ),
            start_at_germany=date_utc.astimezone(
                ZoneInfo("Europe/Berlin")
            ),
            start_at_brazil=date_utc.astimezone(
                ZoneInfo("America/Sao_Paulo")
            ),
            home_team=self._get_team_response(
                event["homeTeam"]
            ),
            away_team=self._get_team_response(
                event["awayTeam"]
            ),
            home_score=(
                event["homeScore"]["current"]
                if event.get("homeScore")
                else None
            ),
            away_score=(
                event["awayScore"]["current"]
                if event.get("awayScore")
                else None
            ),
        )

    def _get_team_response(
        self,
        team: dict[str, Any],
    ) -> TeamResponse:
        team_colors = team.get("teamColors")

        return TeamResponse(
            id=team["id"],
            name=team["name"],
            color=(
                team_colors["primary"]
                if team_colors
                else None
            ),
            secondary_color=(
                team_colors["secondary"]
                if team_colors
                else None
            ),
            text_color=(
                team_colors["text"]
                if team_colors
                else None
            ),
            name_code=team.get("nameCode"),
            image_url=SOFASCORE_IMAGE_URL.format(team["id"]),
        )

    async def _upsert_game(
        self,
        game: GameResponse,
    ) -> None:
        # Busca os times pelo ID externo
        home_team = await self._upsert_team(game.home_team)
        away_team = await self._upsert_team(game.away_team)

        result = await self.db.execute(
            select(Game).where(
                Game.external_id == game.id
            )
        )

        db_game = result.scalar_one_or_none()

        if db_game is None:
            db_game = Game(
                external_id=game.id,
                season=game.season,
                round=game.round,
                start_at=game.start_at_germany.astimezone(
                    timezone.utc
                ),
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=game.home_score,
                away_score=game.away_score,
            )

            self.db.add(db_game)

        else:
            db_game.season = game.season
            db_game.round = game.round
            print(db_game.start_at, game.start_at_germany.astimezone(timezone.utc))
            db_game.start_at = game.start_at_germany.astimezone(
                    timezone.utc
            ),
            db_game.home_team_id = home_team.id
            db_game.away_team_id = away_team.id
            db_game.home_score = game.home_score
            db_game.away_score = game.away_score

    async def _upsert_team(
        self,
        team: TeamResponse,
    ) -> Team:
        result = await self.db.execute(
            select(Team).where(
                Team.external_id == team.id
            )
        )

        db_team = result.scalar_one_or_none()

        if db_team is None:
            db_team = Team(
                external_id=team.id,
                name=team.name,
                color=team.color,
                secondary_color=team.secondary_color,
                text_color=team.text_color,
                name_code=team.name_code,
                image_url=team.image_url,
            )

            self.db.add(db_team)

            # Precisamos do ID antes de criar o Game.
            await self.db.flush()

        else:
            db_team.name = team.name
            db_team.color = team.color
            db_team.secondary_color = team.secondary_color
            db_team.text_color = team.text_color
            db_team.name_code = team.name_code
            db_team.image_url = team.image_url

        return db_team

    def _game_to_response(
        self,
        game: Game,
    ) -> GameResponse:
        return GameResponse(
            id=game.external_id,
            season=game.season,
            round=game.round,
            start_at_germany=game.start_at.astimezone(
                ZoneInfo("Europe/Berlin")
            ),
            start_at_brazil=game.start_at.astimezone(
                ZoneInfo("America/Sao_Paulo")
            ),
            home_team=TeamResponse(
                id=game.home_team.external_id,
                name=game.home_team.name,
                color=game.home_team.color,
                secondary_color=game.home_team.secondary_color,
                text_color=game.home_team.text_color,
                name_code=game.home_team.name_code,
                image_url=game.home_team.image_url,
            ),
            away_team=TeamResponse(
                id=game.away_team.external_id,
                name=game.away_team.name,
                color=game.away_team.color,
                secondary_color=game.away_team.secondary_color,
                text_color=game.away_team.text_color,
                name_code=game.away_team.name_code,
                image_url=game.away_team.image_url,
            ),
            home_score=game.home_score,
            away_score=game.away_score,
        )
    
    
    async def test_db(self):
        start = time.perf_counter()
    
        result = await self.db.execute(
            text("SELECT 1")
        )
    
        print("DB:", time.perf_counter() - start)