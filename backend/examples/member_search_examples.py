"""
Member Search Examples
Demonstrates optimal query patterns for searching members by name.
Uses the optimized indexes defined in backend/config/database.py
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class MemberSearchService:
    """Service class for member name search operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.members

    async def search_by_first_name(
        self, first_name: str, case_sensitive: bool = False
    ) -> List[dict]:
        """
        Search members by first name.
        Uses case-insensitive index for optimal performance.

        Args:
            first_name: First name to search for
            case_sensitive: If True, performs case-sensitive search (default: False)

        Returns:
            List of matching member documents
        """
        query = {"first_name": first_name}

        if case_sensitive:
            cursor = self.collection.find(query)
        else:
            # Use case-insensitive index with collation
            cursor = self.collection.find(query).collation(
                {"locale": "en", "strength": 2}
            )

        return await cursor.to_list(length=100)

    async def search_by_last_name(
        self, last_name: str, case_sensitive: bool = False
    ) -> List[dict]:
        """
        Search members by last name.
        Uses case-insensitive index for optimal performance.

        Args:
            last_name: Last name to search for
            case_sensitive: If True, performs case-sensitive search (default: False)

        Returns:
            List of matching member documents
        """
        query = {"last_name": last_name}

        if case_sensitive:
            cursor = self.collection.find(query)
        else:
            # Use case-insensitive index with collation
            cursor = self.collection.find(query).collation(
                {"locale": "en", "strength": 2}
            )

        return await cursor.to_list(length=100)

    async def autocomplete_last_name(
        self, prefix: str, limit: int = 10
    ) -> List[dict]:
        """
        Autocomplete search for last names starting with prefix.
        Uses case-insensitive index for fast prefix matching.

        Args:
            prefix: Starting characters of last name
            limit: Maximum number of results (default: 10)

        Returns:
            List of matching members, sorted by last name, first name
        """
        query = {"last_name": {"$regex": f"^{prefix}", "$options": "i"}}

        cursor = (
            self.collection.find(
                query,
                {"last_name": 1, "first_name": 1, "name": 1, "bioguide_id": 1},
            )
            .collation({"locale": "en", "strength": 2})
            .sort([("last_name", 1), ("first_name", 1)])
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    async def autocomplete_first_name(
        self, prefix: str, limit: int = 10
    ) -> List[dict]:
        """
        Autocomplete search for first names starting with prefix.
        Uses case-insensitive index for fast prefix matching.

        Args:
            prefix: Starting characters of first name
            limit: Maximum number of results (default: 10)

        Returns:
            List of matching members, sorted by first name, last name
        """
        query = {"first_name": {"$regex": f"^{prefix}", "$options": "i"}}

        cursor = (
            self.collection.find(
                query,
                {"first_name": 1, "last_name": 1, "name": 1, "bioguide_id": 1},
            )
            .collation({"locale": "en", "strength": 2})
            .sort([("first_name", 1), ("last_name", 1)])
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    async def search_full_text(
        self, search_term: str, limit: int = 50
    ) -> List[dict]:
        """
        Full-text search across all name fields (name, first_name, last_name).
        Best for general search when you don't know which field contains the term.

        Args:
            search_term: Search term(s) - can be first name, last name, or both
            limit: Maximum number of results (default: 50)

        Returns:
            List of matching members, sorted by relevance score
        """
        cursor = (
            self.collection.find(
                {"$text": {"$search": search_term}},
                {"score": {"$meta": "textScore"}},
            )
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    async def search_by_full_name(
        self, first_name: str, last_name: str
    ) -> Optional[dict]:
        """
        Search for a member by exact first and last name (case-insensitive).
        Uses compound index for optimal performance.

        Args:
            first_name: Member's first name
            last_name: Member's last name

        Returns:
            Matching member document or None
        """
        return await self.collection.find_one(
            {"first_name": first_name, "last_name": last_name},
            collation={"locale": "en", "strength": 2},
        )

    async def search_members_by_state_and_name(
        self, state: str, name_prefix: str, field: str = "last_name"
    ) -> List[dict]:
        """
        Combined search: filter by state and search by name prefix.
        Uses multiple indexes efficiently.

        Args:
            state: Two-letter state code (e.g., "CA")
            name_prefix: Starting characters of name
            field: Which field to search - "last_name" or "first_name"

        Returns:
            List of matching members
        """
        query = {
            "state": state,
            field: {"$regex": f"^{name_prefix}", "$options": "i"},
        }

        cursor = (
            self.collection.find(query)
            .collation({"locale": "en", "strength": 2})
            .sort([("last_name", 1), ("first_name", 1)])
        )

        return await cursor.to_list(length=100)

    async def get_members_sorted(
        self, limit: int = 100, offset: int = 0
    ) -> List[dict]:
        """
        Get members sorted alphabetically by last name, first name.
        Uses compound index for optimal sorting performance.

        Args:
            limit: Maximum number of results
            offset: Number of records to skip (for pagination)

        Returns:
            List of members sorted by name
        """
        cursor = (
            self.collection.find()
            .sort([("last_name", 1), ("first_name", 1)])
            .skip(offset)
            .limit(limit)
        )

        return await cursor.to_list(length=limit)


# Example usage
async def example_usage():
    """Example usage of the MemberSearchService."""
    from backend.config.database import get_database

    db = await get_database()
    search_service = MemberSearchService(db)

    # Example 1: Case-insensitive first name search
    print("Example 1: Search by first name 'michael' (case-insensitive)")
    results = await search_service.search_by_first_name("michael")
    for member in results[:3]:
        print(f"  - {member['name']}")

    # Example 2: Autocomplete last name
    print("\nExample 2: Autocomplete last names starting with 'Schum'")
    results = await search_service.autocomplete_last_name("Schum")
    for member in results:
        print(f"  - {member['last_name']}, {member['first_name']}")

    # Example 3: Full-text search
    print("\nExample 3: Full-text search for 'Eleanor Holmes'")
    results = await search_service.search_full_text("Eleanor Holmes")
    for member in results:
        print(f"  - {member['name']}")

    # Example 4: Exact full name match
    print("\nExample 4: Find member by exact name")
    member = await search_service.search_by_full_name("Nancy", "pelosi")
    if member:
        print(f"  - Found: {member['name']} ({member['state']})")

    # Example 5: State + name search
    print("\nExample 5: California members with last name starting with 'P'")
    results = await search_service.search_members_by_state_and_name("CA", "P")
    for member in results[:5]:
        print(f"  - {member['name']} ({member['state']})")

    # Example 6: Get sorted list with pagination
    print("\nExample 6: First 5 members alphabetically")
    results = await search_service.get_members_sorted(limit=5)
    for member in results:
        print(f"  - {member['name']}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
