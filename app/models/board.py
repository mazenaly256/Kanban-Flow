from sqlalchemy.orm import mapped_column, Mapped

from app.core.database import Base

class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str]