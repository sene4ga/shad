from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event
    from .user import User


class Debt(Base):  # type: ignore
    __tablename__ = "debts"

    debt_id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.event_id"))
    debtor_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    value: Mapped[float] = mapped_column(Numeric)

    event: Mapped["Event"] = relationship(back_populates="debts")
    debtor: Mapped["User"] = relationship()
