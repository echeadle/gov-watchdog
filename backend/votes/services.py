"""
Vote service layer - business logic for vote operations.
"""

import logging
from datetime import datetime
from typing import Optional

from config.database import get_collection
from members.clients.congress import get_congress_client

logger = logging.getLogger(__name__)


class VoteService:
    """Service for vote-related operations."""

    @staticmethod
    async def get_vote(vote_id: str) -> Optional[dict]:
        """
        Get a vote by ID.

        First checks local database, fetches from API if not found.

        Args:
            vote_id: Vote ID in format {chamber}{congress}-{session}-{roll}
        """
        collection = await get_collection("votes")

        # Check local database first
        doc = await collection.find_one({"vote_id": vote_id})
        if doc:
            doc.pop("_id", None)
            return doc

        # Parse vote_id
        try:
            # Format: h118-1-123 or s118-2-456
            parts = vote_id.split("-")
            if len(parts) != 3:
                return None

            chamber_congress = parts[0]
            session = int(parts[1])
            roll_number = int(parts[2])

            if chamber_congress.startswith("h"):
                chamber = "house"
                congress = int(chamber_congress[1:])
            elif chamber_congress.startswith("s"):
                chamber = "senate"
                congress = int(chamber_congress[1:])
            else:
                return None
        except (ValueError, IndexError):
            return None

        # Fetch from API
        try:
            client = get_congress_client()
            if chamber == "house":
                data = await client.get_house_vote(congress, session, roll_number)
            else:
                data = await client.get_senate_vote(congress, session, roll_number)

            vote_data = VoteService._transform_vote(data, chamber, congress, session, roll_number)
            vote_data["updated_at"] = datetime.utcnow()

            # Store in database
            await collection.update_one(
                {"vote_id": vote_id},
                {"$set": vote_data},
                upsert=True,
            )

            return vote_data
        except Exception as e:
            logger.error(f"Failed to fetch vote {vote_id}: {e}")
            return None

    @staticmethod
    def _transform_vote(
        data: dict,
        chamber: str,
        congress: int,
        session: int,
        roll_number: int,
    ) -> dict:
        """Transform API vote data to our schema."""
        vote = data.get("vote", data)

        vote_id = f"{'h' if chamber == 'house' else 's'}{congress}-{session}-{roll_number}"

        # Parse totals
        totals = vote.get("count", {})

        return {
            "vote_id": vote_id,
            "chamber": chamber,
            "congress": congress,
            "session": session,
            "roll_number": roll_number,
            "date": vote.get("date"),
            "question": vote.get("question", ""),
            "description": vote.get("description"),
            "result": vote.get("result"),
            "bill_id": VoteService._extract_bill_id(vote),
            "totals": {
                "yea": totals.get("yea", 0) or totals.get("yes", 0),
                "nay": totals.get("nay", 0) or totals.get("no", 0),
                "present": totals.get("present", 0),
                "not_voting": totals.get("notVoting", 0) or totals.get("not_voting", 0),
            },
            "member_votes": {},  # Member votes need separate fetch
        }

    @staticmethod
    def _extract_bill_id(vote: dict) -> Optional[str]:
        """Extract bill ID from vote data if present."""
        bill = vote.get("bill")
        if bill:
            bill_type = bill.get("type", "").lower()
            bill_number = bill.get("number")
            congress = bill.get("congress")
            if bill_type and bill_number and congress:
                return f"{bill_type}{bill_number}-{congress}"
        return None

    @staticmethod
    async def get_member_votes(
        bioguide_id: str,
        chamber: Optional[str] = None,
        congress: int = 118,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """
        Get voting record for a member.

        Note: Congress.gov API doesn't have a direct endpoint for member votes.
        This queries our local cache of votes.
        """
        collection = await get_collection("votes")

        query = {f"member_votes.{bioguide_id}": {"$exists": True}}
        if chamber:
            query["chamber"] = chamber.lower()

        total = await collection.count_documents(query)

        cursor = (
            collection.find(query)
            .sort("date", -1)
            .skip(offset)
            .limit(limit)
        )

        results = []
        async for doc in cursor:
            member_vote = doc.get("member_votes", {}).get(bioguide_id, "Unknown")
            results.append(
                {
                    "vote_id": doc["vote_id"],
                    "date": doc.get("date"),
                    "question": doc.get("question", ""),
                    "bill_id": doc.get("bill_id"),
                    "member_vote": member_vote,
                    "result": doc.get("result"),
                }
            )

        return {
            "results": results,
            "total": total,
        }

    @staticmethod
    async def get_recent_votes(
        chamber: Optional[str] = None,
        congress: int = 118,
        session: int = 1,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Get recent votes, optionally filtered by chamber."""
        # Fetch from API to get fresh data
        try:
            client = get_congress_client()
            if chamber == "house":
                data = await client.get_house_votes(congress, session, limit=limit, offset=offset)
            elif chamber == "senate":
                data = await client.get_senate_votes(congress, session, limit=limit, offset=offset)
            else:
                # Get both chambers
                house_data = await client.get_house_votes(
                    congress, session, limit=limit // 2, offset=offset
                )
                senate_data = await client.get_senate_votes(
                    congress, session, limit=limit // 2, offset=offset
                )

                votes = []
                for v in house_data.get("votes", []):
                    votes.append(VoteService._transform_vote(v, "house", congress, session, v.get("rollNumber", 0)))
                for v in senate_data.get("votes", []):
                    votes.append(VoteService._transform_vote(v, "senate", congress, session, v.get("rollNumber", 0)))

                # Sort by date
                votes.sort(key=lambda x: x.get("date", ""), reverse=True)

                return {
                    "results": votes[:limit],
                    "total": len(votes),
                }

            votes = []
            for v in data.get("votes", []):
                votes.append(
                    VoteService._transform_vote(
                        v, chamber, congress, session, v.get("rollNumber", 0)
                    )
                )

            return {
                "results": votes,
                "total": data.get("pagination", {}).get("count", len(votes)),
            }

        except Exception as e:
            logger.error(f"Failed to fetch recent votes: {e}")
            return {"results": [], "total": 0, "error": str(e)}
