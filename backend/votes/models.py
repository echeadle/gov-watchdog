"""
Pydantic models for congressional votes.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class VoteTotals(BaseModel):
    """Vote count totals."""

    yea: int = 0
    nay: int = 0
    present: int = 0
    not_voting: int = 0


class MemberVote(BaseModel):
    """Individual member's vote on a roll call."""

    bioguide_id: str
    name: Optional[str] = None
    party: Optional[str] = None
    state: Optional[str] = None
    vote: str  # Yea, Nay, Present, Not Voting


class Vote(BaseModel):
    """Congressional roll call vote."""

    vote_id: str = Field(..., description="Unique ID: {chamber}{congress}-{session}-{roll}")
    chamber: str = Field(..., description="house or senate")
    congress: int
    session: int
    roll_number: int
    date: Optional[date] = None
    question: str = ""
    description: Optional[str] = None
    result: Optional[str] = None
    bill_id: Optional[str] = None
    totals: VoteTotals = Field(default_factory=VoteTotals)
    member_votes: dict[str, str] = Field(
        default_factory=dict,
        description="Map of bioguide_id -> vote (Yea/Nay/etc.)",
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "vote_id": "h118-1-123",
                "chamber": "house",
                "congress": 118,
                "session": 1,
                "roll_number": 123,
                "question": "On Passage",
                "result": "Passed",
            }
        }


class VoteSummary(BaseModel):
    """Lightweight vote summary for lists."""

    vote_id: str
    chamber: str
    date: Optional[date] = None
    question: str
    result: Optional[str] = None
    bill_id: Optional[str] = None
    totals: VoteTotals


class MemberVotingRecord(BaseModel):
    """A member's vote on a specific roll call."""

    vote_id: str
    date: Optional[date] = None
    question: str
    bill_id: Optional[str] = None
    member_vote: str  # How this member voted
    result: Optional[str] = None
