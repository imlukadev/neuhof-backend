from src.database.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime
from typing import TYPE_CHECKING

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int] = mapped_column(unique=True, index=True)

    season: Mapped[str | None]

    round: Mapped[int | None]

    start_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
)

    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id")
    )

    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id")
    )

    home_score: Mapped[int | None]
    away_score: Mapped[int | None]

    home_team: Mapped["Team"] = relationship(
        foreign_keys=[home_team_id]
    )

    away_team: Mapped["Team"] = relationship(
        foreign_keys=[away_team_id]
    )
    
    if TYPE_CHECKING:
        from .team import Team
        away_team: Mapped["Team"]