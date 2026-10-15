from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Contact, Interaction
from app.schemas import InteractionCreate, InteractionResponse

router = APIRouter(prefix="/contacts/{contact_id}/interactions", tags=["interactions"])


@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
def create_interaction(contact_id: int, payload: InteractionCreate, db: Session = Depends(get_db)) -> Interaction:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    interaction = Interaction(contact_id=contact_id, **payload.model_dump())
    if contact.last_contacted_at is None or payload.interaction_date > contact.last_contacted_at:
        contact.last_contacted_at = payload.interaction_date
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("", response_model=list[InteractionResponse])
def list_interactions(contact_id: int, db: Session = Depends(get_db)) -> list[Interaction]:
    if db.get(Contact, contact_id) is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return list(db.scalars(select(Interaction).where(Interaction.contact_id == contact_id).order_by(Interaction.interaction_date)).all())
