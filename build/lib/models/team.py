from src.database.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    color: Mapped[str | None]
    secondary_color: Mapped[str | None]
    text_color: Mapped[str | None]
    name_code: Mapped[str | None]
    image_url: Mapped[str | None]