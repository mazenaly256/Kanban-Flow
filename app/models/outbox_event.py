from datetime import datetime
from sqlalchemy import DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str]
    board_id: Mapped[int]
    payload: Mapped[dict] = mapped_column(JSONB)    # for storing the broadcasted message
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # partial indexing, so only the unpublished events stay in the search space when the query involves the rows with 'published_at' is NULL (which happens in relay's polling)
        # this avoids considering all the rows in that growing-only table
        Index("ix_outbox_pending_events", "id", postgresql_where=text("published_at IS NULL")),
    )