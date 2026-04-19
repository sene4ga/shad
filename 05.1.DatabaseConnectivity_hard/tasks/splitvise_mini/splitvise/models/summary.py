
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Numeric, ForeignKey

from .base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .trip import Trip
    from .user import User


class Summary(Base):  # type: ignore
    __tablename__ = "summaries"

    summary_id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.trip_id"))
    user_from_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user_to_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    value: Mapped[float] = mapped_column(Numeric)

    trip: Mapped["Trip"] = relationship(back_populates="summaries")
    user_from: Mapped["User"] = relationship(foreign_keys=[user_from_id])
    user_to: Mapped["User"] = relationship(foreign_keys=[user_to_id])
