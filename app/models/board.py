from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.core.database import Base


if TYPE_CHECKING:   # to avoid circular dependency
    from app.models.board_column import BoardColumn


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str]

    columns: Mapped[list["BoardColumn"]] = relationship(back_populates="board")