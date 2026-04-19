import typing as tp
from decimal import Decimal
from sqlalchemy import select, delete
from .models.base import Session
from .models import User, Expense, Trip, Debt, Event, Summary
from .exceptions import SplitViseException

MoneyType = Decimal


def create_user(username: str, *, session: Session) -> User:
    # Проверка на уникальность
    existing_user = session.scalars(select(User).where(User.username == username)).first()
    if existing_user:
        raise SplitViseException("username already taken")

    user = User(username=username)
    session.add(user)
    session.commit()  # Обязательно commit, чтобы тест увидел изменения
    return user


def create_trip(creator_id: int, title: str, description: str, *, session: Session) -> Trip:
    if not title:
        raise SplitViseException("Title of a trip should not be empty")

    creator = session.get(User, creator_id)
    if not creator:
        raise SplitViseException("User not found by id")

    trip = Trip(title=title, description=description)
    trip.users.append(creator)

    session.add(trip)
    session.commit()
    return trip


def add_user_to_trip(guest_id: int, trip_id: int, *, session: Session) -> None:
    trip = session.get(Trip, trip_id)
    if not trip:
        raise SplitViseException("Trip not found by id")

    guest = session.get(User, guest_id)
    if not guest:
        raise SplitViseException("User not found by id")

    if guest in trip.users:
        raise SplitViseException("User already in trip")

    trip.users.append(guest)
    session.commit()


def get_trip_users(trip_id: int, *, session: Session) -> list[User]:
    trip = session.get(Trip, trip_id)
    if not trip:
        raise SplitViseException("Trip not found by id")
    return trip.users


def create_event(trip_id: int, people_debt: tp.Mapping[int, MoneyType],
                 people_payment: tp.Mapping[int, MoneyType], title: str, *, session: Session) -> Event:
    trip = session.get(Trip, trip_id)
    if not trip:
        raise SplitViseException("Trip not found by id")

    if sum(people_debt.values()) != sum(people_payment.values()):
        raise SplitViseException("Sum of debts and sum of payments are not equal")

    trip_user_ids = {u.user_id for u in trip.users}
    for uid in people_debt:
        if uid not in trip_user_ids:
            raise SplitViseException("Can not create debt for user not in trip")
    for uid in people_payment:
        if uid not in trip_user_ids:
            raise SplitViseException("Can not create payment for user not in trip")

    event = Event(trip_id=trip_id, title=title, settled_up=False)
    session.add(event)
    session.flush()  # Получаем ID для связей, но в конце всё равно commit

    for uid, amount in people_debt.items():
        session.add(Debt(event_id=event.event_id, debtor_id=uid, value=amount))
    for uid, amount in people_payment.items():
        session.add(Expense(event_id=event.event_id, payer_id=uid, value=amount))

    session.commit()
    return event


def make_summary(trip_id: int, *, session: Session) -> None:
    trip = session.get(Trip, trip_id)
    if not trip:
        raise SplitViseException("Trip not found by id")

    balances: dict[int, Decimal] = {}
    for event in trip.events:
        event.settled_up = True
        for exp in event.expenses:
            balances[exp.payer_id] = balances.get(exp.payer_id, Decimal('0')) + Decimal(str(exp.value))
        for dbt in event.debts:
            balances[dbt.debtor_id] = balances.get(dbt.debtor_id, Decimal('0')) - Decimal(str(dbt.value))

    session.execute(delete(Summary).where(Summary.trip_id == trip_id))

    debtors = [[uid, abs(bal)] for uid, bal in balances.items() if bal < Decimal('-0.0001')]
    creditors = [[uid, bal] for uid, bal in balances.items() if bal > Decimal('0.0001')]

    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        settled = min(debtors[i][1], creditors[j][1])
        session.add(Summary(
            trip_id=trip_id,
            user_from_id=creditors[j][0],
            user_to_id=debtors[i][0],
            value=settled
        ))
        debtors[i][1] -= settled
        creditors[j][1] -= settled
        if debtors[i][1] < Decimal('0.0001'):
            i += 1
        if creditors[j][1] < Decimal('0.0001'):
            j += 1

    session.commit()
