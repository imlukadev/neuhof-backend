from src.api.responses import GameResponse
from fastapi import APIRouter, Depends, Request
from src.services.games_service import GamesService
from fastapi.concurrency import run_in_threadpool

router = APIRouter(tags=["games"])


def get_games_service(request: Request) -> GamesService:
    return GamesService()

@router.get("/games")
async def next_games(
    request: Request,
    service: GamesService = Depends(get_games_service),
) -> list[GameResponse]:
    return await run_in_threadpool(service.find_games)
