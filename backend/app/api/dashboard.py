from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Contact
from app.schemas import ContactResponse, DashboardSummary
from app.services.reminder_service import ACTIVE_STATUSES, get_follow_ups

router = APIRouter(tags=["dashboard", "follow-ups"])


def active_count_query(status_value: str):
    return select(func.count()).select_from(Contact).where(Contact.status == status_value)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    total = db.scalar(select(func.count()).select_from(Contact)) or 0
    unscheduled = db.scalar(select(func.count()).select_from(Contact).where(Contact.next_follow_up_at.is_(None))) or 0
    return DashboardSummary(
        total_contacts=total,
        pending_contacts=db.scalar(active_count_query("Pending")) or 0,
        replied_contacts=db.scalar(active_count_query("Replied")) or 0,
        completed_contacts=db.scalar(active_count_query("Completed")) or 0,
        due_today=len(get_follow_ups(db, "due")),
        overdue=len(get_follow_ups(db, "overdue")),
        unscheduled=unscheduled,
    )


@router.get("/follow-ups/due", response_model=list[ContactResponse])
def due_follow_ups(day: Optional[date] = Query(None), db: Session = Depends(get_db)) -> list[Contact]:
    return get_follow_ups(db, "due", day)


@router.get("/follow-ups/overdue", response_model=list[ContactResponse])
def overdue_follow_ups(day: Optional[date] = Query(None), db: Session = Depends(get_db)) -> list[Contact]:
    return get_follow_ups(db, "overdue", day)


@router.get("/follow-ups/upcoming", response_model=list[ContactResponse])
def upcoming_follow_ups(days: int = Query(7, ge=1, le=90), day: Optional[date] = Query(None), db: Session = Depends(get_db)) -> list[Contact]:
    return get_follow_ups(db, "upcoming", day, days)


@router.get("/follow-ups/unscheduled", response_model=list[ContactResponse])
def unscheduled_follow_ups(db: Session = Depends(get_db)) -> list[Contact]:
    return list(db.scalars(select(Contact).where(Contact.next_follow_up_at.is_(None), Contact.status.in_(ACTIVE_STATUSES)).order_by(Contact.name)).all())
