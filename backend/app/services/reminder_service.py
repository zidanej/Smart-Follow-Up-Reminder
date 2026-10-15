from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Contact

ACTIVE_STATUSES = ("Pending", "Replied", "No Response")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def follow_up_query(kind: str, today: Optional[date] = None, days: int = 7) -> Select:
    current_day = today or now_utc().date()
    start, end = day_bounds(current_day)
    query = select(Contact).where(Contact.status.in_(ACTIVE_STATUSES), Contact.next_follow_up_at.is_not(None))
    if kind == "due":
        return query.where(Contact.next_follow_up_at >= start, Contact.next_follow_up_at < end).order_by(Contact.next_follow_up_at)
    if kind == "overdue":
        return query.where(Contact.next_follow_up_at < start).order_by(Contact.next_follow_up_at)
    if kind == "upcoming":
        future_end = end + timedelta(days=days)
        return query.where(Contact.next_follow_up_at >= end, Contact.next_follow_up_at < future_end).order_by(Contact.next_follow_up_at)
    raise ValueError("Unknown follow-up kind")


def get_follow_ups(db: Session, kind: str, today: Optional[date] = None, days: int = 7) -> list[Contact]:
    return list(db.scalars(follow_up_query(kind, today, days)).all())
