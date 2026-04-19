
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Numeric, ForeignKey

from .base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event
    from .user import User

class Expense(Base):  # type: ignore
    __tablename__ = "expenses"

    expense_id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.event_id"))
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    value: Mapped[float] = mapped_column(Numeric)

    event: Mapped["Event"] = relationship(back_populates="expenses")
    payer: Mapped["User"] = relationship()
