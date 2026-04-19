from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, ForeignKey

from .base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .trip import Trip
    from .expense import Expense
    from .debt import Debt

class Event(Base):  # type: ignore
    __tablename__ = "events"

    event_id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.trip_id"))
    title: Mapped[str] = mapped_column(String)
    happened_datetime: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    settled_up: Mapped[bool] = mapped_column(Boolean, default=False)

    trip: Mapped["Trip"] = relationship(back_populates="events")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    debts: Mapped[list["Debt"]] = relationship(back_populates="event", cascade="all, delete-orphan")
