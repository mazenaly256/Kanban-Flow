from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:   # to avoid circular dependency
    from app.models.board_column import BoardColumn

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("board_columns.id", ondelete="CASCADE"))
    title: Mapped[str]
    description: Mapped[str | None]
    index: Mapped[float]

    column: Mapped["BoardColumn"] = relationship(back_populates="tasks")    # navigation property to be able to traverse the related column
