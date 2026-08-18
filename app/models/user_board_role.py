from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.core.database import Base

class UserBoardRole(Base):
    __tablename__ = "user_board_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), primary_key=True)
    role: Mapped[str]