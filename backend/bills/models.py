"""
Pydantic models for congressional bills.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class BillAction(BaseModel):
    """An action taken on a bill."""

    date: Optional[date] = None
    text: str
    action_type: Optional[str] = None
    action_code: Optional[str] = None


class Bill(BaseModel):
    """Congressional bill model."""

    bill_id: str = Field(..., description="Unique ID: {type}{number}-{congress}")
    congress: int
    type: str = Field(..., description="Bill type: hr, s, hjres, sjres, etc.")
    number: int
    title: str
    short_title: Optional[str] = None
    sponsor_id: Optional[str] = Field(None, description="Sponsor's bioguide ID")
    sponsor_name: Optional[str] = None
    sponsor_party: Optional[str] = None
    sponsor_state: Optional[str] = None
    cosponsors_count: int = 0
    introduced_date: Optional[date] = None
    latest_action: Optional[str] = None
    latest_action_date: Optional[date] = None
    policy_area: Optional[str] = None
    subjects: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "bill_id": "hr1234-118",
                "congress": 118,
                "type": "hr",
                "number": 1234,
                "title": "To provide for...",
                "sponsor_id": "P000197",
                "introduced_date": "2023-03-15",
            }
        }


class BillSummary(BaseModel):
    """Lightweight bill summary for lists."""

    bill_id: str
    type: str
    number: int
    title: str
    sponsor_id: Optional[str] = None
    sponsor_name: Optional[str] = None
    introduced_date: Optional[date] = None
    latest_action: Optional[str] = None


class BillSearchParams(BaseModel):
    """Search parameters for bill queries."""

    congress: Optional[int] = Field(None, description="Filter by congress number")
    type: Optional[str] = Field(None, description="Filter by bill type")
    sponsor_id: Optional[str] = Field(None, description="Filter by sponsor")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
