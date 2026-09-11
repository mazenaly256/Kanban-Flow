from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:   # to avoid circular dependency
    from app.models.task import Task

class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    title: Mapped[str]
    index: Mapped[float]

    tasks: Mapped[list["Task"]] = relationship(back_populates="column")     # navigation property to be able to traverse the related tasks