from src.database.connection import get_db
from src.api.responses import GameResponse
from fastapi import APIRouter, Depends, Request
from src.services.games_service import GamesService
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter(tags=["games"])


def get_games_service(request: Request,db:AsyncSession = Depends(get_db)) -> GamesService:
    return GamesService(db)

@router.get("/games")
async def fetch_games(
    request: Request,
    service: GamesService = Depends(get_games_service),
) -> list[GameResponse]:
    return await service.find_games()



@router.get("/sync-games")
async def sync_sofascore_games(
    request: Request,
    service: GamesService = Depends(get_games_service),
):
    await service.sync_games()