from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.access_log import AccessLog


async def register_access(
    db: AsyncSession,
    *,
    user_agent: str | None,
    referer: str | None,
    source_url: str,
) -> None:
    db.add(
        AccessLog(
            accessed_at=datetime.now(timezone.utc),
            user_agent=user_agent,
            referer=referer,
            source_url=source_url,
        )
    )
    await db.commit()
