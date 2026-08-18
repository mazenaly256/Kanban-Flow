from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.core.database import Base

class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"))
    title: Mapped[str]
    index: Mapped[float]