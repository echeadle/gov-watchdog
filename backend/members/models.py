"""
Pydantic models for Congress members.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Term(BaseModel):
    """A term served by a member."""

    congress: int
    chamber: str  # "house" or "senate"
    start_year: int
    end_year: Optional[int] = None
    state: str
    district: Optional[int] = None  # House only
    party: str


class Member(BaseModel):
    """Congress member model."""

    bioguide_id: str = Field(..., description="Unique identifier from bioguide")
    name: str = Field(..., description="Full display name")
    first_name: str
    last_name: str
    party: str = Field(..., description="Party abbreviation: D, R, I, etc.")
    state: str = Field(..., description="Two-letter state code")
    district: Optional[int] = Field(None, description="House district number")
    chamber: str = Field(..., description="Current chamber: house or senate")
    image_url: Optional[str] = None
    official_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    terms: list[Term] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "bioguide_id": "P000197",
                "name": "Nancy Pelosi",
                "first_name": "Nancy",
                "last_name": "Pelosi",
                "party": "D",
                "state": "CA",
                "district": 11,
                "chamber": "house",
                "image_url": "https://bioguide.congress.gov/bioguide/photo/P/P000197.jpg",
            }
        }


class MemberSummary(BaseModel):
    """Lightweight member summary for lists."""

    bioguide_id: str
    name: str
    party: str
    state: str
    district: Optional[int] = None
    chamber: str
    image_url: Optional[str] = None


class MemberSearchParams(BaseModel):
    """Search parameters for member queries."""

    q: Optional[str] = Field(None, description="Search term for name")
    state: Optional[str] = Field(None, description="Filter by state code")
    party: Optional[str] = Field(None, description="Filter by party: D, R, I")
    chamber: Optional[str] = Field(None, description="Filter by chamber: house, senate")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    results: list
    total: int
    page: int
    page_size: int
    total_pages: int
