from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.services.access_service import register_access
from src.services.live_service import LiveService

router = APIRouter(tags=["live"])


def get_live_service(request: Request) -> LiveService:
    return request.app.state.live_service


@router.get("/live")
async def live(
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: LiveService = Depends(get_live_service),
):
    url = await service.get_current_url()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Livestream indisponível no momento.",
        )

    await register_access(
        db,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
        source_url=url,
    )

    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/live/url")
async def live_url(
    request: Request,
    service: LiveService = Depends(get_live_service),
):
    url = await service.get_current_url()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Livestream indisponível no momento.",
        )
    return {"url": url}
