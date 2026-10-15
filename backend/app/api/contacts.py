from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Contact, IdempotencyRecord
from app.schemas import STATUSES, ContactCreate, ContactDetail, ContactPage, ContactResponse, ContactUpdate
from app.services.reminder_service import get_follow_ups

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", max_length=128),
) -> Contact:
    if idempotency_key:
        existing_record = db.get(IdempotencyRecord, idempotency_key)
        if existing_record is not None:
            existing_contact = db.get(Contact, existing_record.contact_id)
            if existing_contact is not None:
                return existing_contact
    contact = Contact(**payload.model_dump())
    db.add(contact)
    try:
        db.flush()
        if idempotency_key:
            db.add(IdempotencyRecord(key=idempotency_key, contact_id=contact.id))
        db.commit()
        db.refresh(contact)
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing_record = db.get(IdempotencyRecord, idempotency_key)
            if existing_record is not None:
                existing_contact = db.get(Contact, existing_record.contact_id)
                if existing_contact is not None:
                    return existing_contact
        raise
    return contact


@router.get("", response_model=ContactPage)
def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=120),
    status_filter: Optional[str] = Query(None, alias="status"),
    follow_up: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> ContactPage:
    query = select(Contact)
    if search:
        term = "%" + search.strip() + "%"
        query = query.where(or_(Contact.name.ilike(term), Contact.company.ilike(term)))
    if status_filter:
        if status_filter not in STATUSES:
            raise HTTPException(status_code=422, detail="status must be Pending, Replied, Completed, or No Response")
        query = query.where(Contact.status == status_filter)
    if follow_up in ("due", "overdue", "upcoming"):
        contacts = get_follow_ups(db, follow_up)
        ids = [contact.id for contact in contacts]
        query = query.where(Contact.id.in_(ids)) if ids else query.where(False)
    elif follow_up == "unscheduled":
        query = query.where(Contact.next_follow_up_at.is_(None))
    elif follow_up:
        raise HTTPException(status_code=422, detail="follow_up must be due, overdue, upcoming, or unscheduled")
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Contact.next_follow_up_at.asc().nulls_last(), Contact.name).offset((page - 1) * page_size).limit(page_size)).all())
    return ContactPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{contact_id}", response_model=ContactDetail)
def get_contact(contact_id: int, db: Session = Depends(get_db)) -> Contact:
    contact = db.execute(select(Contact).options(joinedload(Contact.interactions)).where(Contact.id == contact_id)).unique().scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, payload: ContactUpdate, db: Session = Depends(get_db)) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)) -> None:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.execute(delete(IdempotencyRecord).where(IdempotencyRecord.contact_id == contact_id))
    db.delete(contact)
    db.commit()
