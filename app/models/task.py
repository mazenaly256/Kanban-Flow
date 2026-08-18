from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id"))
    title: Mapped[str]
    description: Mapped[str | None]
    index: Mapped[float]