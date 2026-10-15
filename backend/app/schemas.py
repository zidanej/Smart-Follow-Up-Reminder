from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

STATUSES = ("Pending", "Replied", "Completed", "No Response")
INTERACTION_TYPES = ("Email", "Call", "Meeting", "Message", "Note")


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """Store every timestamp as a naive UTC value for SQLite consistency."""
    if value is None:
        return None
    utc_value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return utc_value.replace(tzinfo=None)


def serialize_datetime(value: datetime) -> datetime:
    """Expose SQLite's naive UTC timestamps as explicit UTC timestamps."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class ContactBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    company: Optional[str] = Field(default=None, max_length=160)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=40)
    purpose: str = Field(min_length=1, max_length=240)
    status: str = Field(default="Pending")
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("name", "purpose", "company", "phone", "notes", mode="before")
    @classmethod
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        return clean_text(value)

    @field_validator("last_contacted_at", "next_follow_up_at")
    @classmethod
    def normalize_timestamps(cls, value: Optional[datetime]) -> Optional[datetime]:
        return normalize_datetime(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in STATUSES:
            raise ValueError("status must be Pending, Replied, Completed, or No Response")
        return value


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    company: Optional[str] = Field(default=None, max_length=160)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=40)
    purpose: Optional[str] = Field(default=None, min_length=1, max_length=240)
    status: Optional[str] = None
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("name", "purpose", "company", "phone", "notes", mode="before")
    @classmethod
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        return clean_text(value)

    @field_validator("last_contacted_at", "next_follow_up_at")
    @classmethod
    def normalize_timestamps(cls, value: Optional[datetime]) -> Optional[datetime]:
        return normalize_datetime(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in STATUSES:
            raise ValueError("status must be Pending, Replied, Completed, or No Response")
        return value


class InteractionCreate(BaseModel):
    interaction_type: str
    interaction_date: datetime
    description: str = Field(min_length=1, max_length=5000)
    outcome: Optional[str] = Field(default=None, max_length=240)

    @field_validator("interaction_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in INTERACTION_TYPES:
            raise ValueError("interaction_type must be Email, Call, Meeting, Message, or Note")
        return value

    @field_validator("interaction_date")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        normalized = normalize_datetime(value)
        assert normalized is not None
        return normalized

    @field_validator("description", "outcome", mode="before")
    @classmethod
    def strip_fields(cls, value: Optional[str]) -> Optional[str]:
        return clean_text(value)


class InteractionResponse(InteractionCreate):
    id: int
    contact_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("interaction_date", "created_at")
    def serialize_timestamps(self, value: datetime) -> datetime:
        return serialize_datetime(value)


class ContactResponse(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("last_contacted_at", "next_follow_up_at", "created_at", "updated_at")
    def serialize_timestamps(self, value: Optional[datetime]) -> Optional[datetime]:
        return serialize_datetime(value) if value is not None else None


class ContactDetail(ContactResponse):
    interactions: list[InteractionResponse] = Field(default_factory=list)


class ContactPage(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int


class DashboardSummary(BaseModel):
    total_contacts: int
    pending_contacts: int
    replied_contacts: int
    completed_contacts: int
    due_today: int
    overdue: int
    unscheduled: int
