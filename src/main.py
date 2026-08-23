from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.api.routes.live import router as live_router
from src.api.routes.games import router as game_router
from src.config import settings
from src.services.live_service import LiveService
from src.services.scraper import XbotGoScraper


@asynccontextmanager
async def lifespan(app: FastAPI):
    scraper = XbotGoScraper()
    app.state.live_service = LiveService(
        scraper=scraper,
        cache_seconds=settings.live_cache_seconds,
    )
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(live_router)
app.include_router(game_router)
