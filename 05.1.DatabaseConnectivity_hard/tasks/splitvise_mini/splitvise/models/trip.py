from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Table, Column, String, DateTime, ForeignKey

from .base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event
    from .user import User
    from .summary import Summary

UserTrip = Table(
    'users_trips', Base.metadata,
    Column('user_id', ForeignKey('users.user_id'), primary_key=True),
    Column('trip_id', ForeignKey('trips.trip_id'), primary_key=True)
)


class Trip(Base):  # type: ignore
    __tablename__ = "trips"

    trip_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)

    created_timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    users: Mapped[list["User"]] = relationship(secondary=UserTrip, back_populates="trips")
    events: Mapped[list["Event"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="trip", cascade="all, delete-orphan")

