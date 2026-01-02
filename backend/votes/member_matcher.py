"""
Member matching utilities for linking external data to our database.

Handles matching members from various sources (Senate XML, etc.) to bioguide IDs.
"""

import logging
from typing import Optional

from config.database import get_collection

logger = logging.getLogger(__name__)


class MemberMatcher:
    """Match member records from external sources to bioguide IDs."""

    def __init__(self):
        self._member_cache = {}

    async def find_bioguide_by_name_state(
        self, first_name: str, last_name: str, state: str, chamber: str = "senate"
    ) -> Optional[str]:
        """
        Find bioguide ID by matching name and state.

        This is used for Senate votes which only provide name/state, not bioguide ID.

        Args:
            first_name: Member's first name
            last_name: Member's last name
            state: Two-letter state code
            chamber: Chamber (default: senate)

        Returns:
            Bioguide ID if found, None otherwise
        """
        # Create cache key
        cache_key = f"{last_name}_{first_name}_{state}_{chamber}".lower()

        # Check cache first
        if cache_key in self._member_cache:
            return self._member_cache[cache_key]

        try:
            collection = await get_collection("members")

            # Try exact match first
            member = await collection.find_one(
                {
                    "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
                    "last_name": {"$regex": f"^{last_name}$", "$options": "i"},
                    "state": state.upper(),
                    "chamber": chamber.lower(),
                }
            )

            if member:
                bioguide_id = member.get("bioguide_id")
                self._member_cache[cache_key] = bioguide_id
                return bioguide_id

            # Try partial match on last name (handles Jr., III, etc.)
            member = await collection.find_one(
                {
                    "last_name": {"$regex": f"^{last_name}", "$options": "i"},
                    "state": state.upper(),
                    "chamber": chamber.lower(),
                }
            )

            if member:
                bioguide_id = member.get("bioguide_id")
                logger.info(
                    f"Partial match for {first_name} {last_name} ({state}): {bioguide_id}"
                )
                self._member_cache[cache_key] = bioguide_id
                return bioguide_id

            logger.warning(
                f"Could not find bioguide ID for {first_name} {last_name} ({state})"
            )
            return None

        except Exception as e:
            logger.error(f"Error finding bioguide ID: {e}")
            return None

    async def match_senate_member(self, member_data: dict) -> Optional[str]:
        """
        Match a Senate XML member record to a bioguide ID.

        Args:
            member_data: Dict with first_name, last_name, state from XML

        Returns:
            Bioguide ID if found, None otherwise
        """
        return await self.find_bioguide_by_name_state(
            first_name=member_data.get("first_name", ""),
            last_name=member_data.get("last_name", ""),
            state=member_data.get("state", ""),
            chamber="senate",
        )

    def clear_cache(self):
        """Clear the member matching cache."""
        self._member_cache.clear()
