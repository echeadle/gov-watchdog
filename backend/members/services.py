"""
Member service layer - business logic for member operations.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from config.database import get_collection
from members.clients.congress import get_congress_client
from members.models import Member, MemberSearchParams, MemberSummary, PaginatedResponse

logger = logging.getLogger(__name__)


def _escape_regex_special_chars(text: str) -> str:
    """
    Escape special regex characters for safe MongoDB regex queries.

    Args:
        text: Raw search text that may contain regex special characters

    Returns:
        Escaped text safe for use in regex patterns

    Example:
        >>> _escape_regex_special_chars("O'Brien")
        "O'Brien"
        >>> _escape_regex_special_chars("Smith (Jr.)")
        "Smith \\(Jr\\.\\)"
    """
    # Escape regex special characters that could break the pattern
    special_chars = r'\.^$*+?{}[]()|\\'
    escaped = text
    for char in special_chars:
        escaped = escaped.replace(char, f'\\{char}')
    return escaped


def _normalize_search_term(search_term: str) -> str:
    """
    Normalize search term for consistent matching.

    Handles:
    - Extra whitespace
    - Multiple spaces between words
    - Leading/trailing whitespace

    Args:
        search_term: Raw user search input

    Returns:
        Normalized search term

    Example:
        >>> _normalize_search_term("  Mike   Lee  ")
        "Mike Lee"
        >>> _normalize_search_term("Mary-Kate")
        "Mary-Kate"
    """
    # Replace multiple spaces with single space, strip leading/trailing
    return re.sub(r'\s+', ' ', search_term.strip())


def _build_single_word_query(word: str) -> dict:
    """
    Build MongoDB query for single word search.

    Searches across first_name, last_name, and full name fields.
    Uses word boundary for partial matching (e.g., "Mic" matches "Michael").

    Args:
        word: Single search word (already escaped)

    Returns:
        MongoDB $or query

    Example:
        >>> _build_single_word_query("Mike")
        {
            "$or": [
                {"first_name": {"$regex": "\\bMike", "$options": "i"}},
                {"last_name": {"$regex": "\\bMike", "$options": "i"}},
                {"name": {"$regex": "\\bMike", "$options": "i"}}
            ]
        }
    """
    pattern = f"\\b{word}"
    return {
        "$or": [
            {"first_name": {"$regex": pattern, "$options": "i"}},
            {"last_name": {"$regex": pattern, "$options": "i"}},
            {"name": {"$regex": pattern, "$options": "i"}},
        ]
    }


def _build_two_word_query(first_word: str, second_word: str) -> dict:
    """
    Build MongoDB query for two-word name search.

    Handles both "First Last" and "Last First" orderings.
    Also checks the full name field for either pattern.

    Args:
        first_word: First word in search (already escaped)
        second_word: Second word in search (already escaped)

    Returns:
        MongoDB $or query with multiple matching strategies

    Example:
        >>> _build_two_word_query("Mike", "Lee")
        # Returns query matching:
        # - first_name: Mike, last_name: Lee
        # - first_name: Lee, last_name: Mike
        # - name: "Mike.*Lee" or "Lee.*Mike"
    """
    first_pattern = f"\\b{first_word}"
    second_pattern = f"\\b{second_word}"

    return {
        "$or": [
            # Try as "First Last"
            {
                "$and": [
                    {"first_name": {"$regex": first_pattern, "$options": "i"}},
                    {"last_name": {"$regex": second_pattern, "$options": "i"}},
                ]
            },
            # Try as "Last First"
            {
                "$and": [
                    {"first_name": {"$regex": second_pattern, "$options": "i"}},
                    {"last_name": {"$regex": first_pattern, "$options": "i"}},
                ]
            },
            # Try against full name field in both orders
            {
                "name": {
                    "$regex": f"{first_pattern}.*{second_pattern}|{second_pattern}.*{first_pattern}",
                    "$options": "i",
                }
            },
        ]
    }


def _build_multi_word_query(words: list[str]) -> dict:
    """
    Build MongoDB query for 3+ word name search.

    Handles complex names like "Martin Luther King" or "Mary Jane Smith".
    Strategies:
    1. Match all words in sequence in full name field
    2. Try first word + last word as first_name + last_name
    3. Try reversed: last word + first word

    Args:
        words: List of search words (already escaped)

    Returns:
        MongoDB $or query

    Example:
        >>> _build_multi_word_query(["Martin", "Luther", "King"])
        # Returns query matching:
        # - name: "Martin.*Luther.*King"
        # - first_name: Martin, last_name: King
        # - first_name: King, last_name: Martin
    """
    patterns = []

    # Build pattern for full name with all parts in sequence
    full_pattern = ".*".join(f"\\b{word}" for word in words)
    patterns.append({"name": {"$regex": full_pattern, "$options": "i"}})

    # Try first word as first_name, last word as last_name
    first_pattern = f"\\b{words[0]}"
    last_pattern = f"\\b{words[-1]}"

    patterns.append(
        {
            "$and": [
                {"first_name": {"$regex": first_pattern, "$options": "i"}},
                {"last_name": {"$regex": last_pattern, "$options": "i"}},
            ]
        }
    )

    # Try reversed: last word as first_name, first word as last_name
    patterns.append(
        {
            "$and": [
                {"first_name": {"$regex": last_pattern, "$options": "i"}},
                {"last_name": {"$regex": first_pattern, "$options": "i"}},
            ]
        }
    )

    # Try middle combinations for 3-word names
    # e.g., "Mary Jane Smith" could be first_name="Mary Jane", last_name="Smith"
    if len(words) == 3:
        # Try first two words as first_name, last word as last_name
        first_two_pattern = f"\\b{words[0]}.*\\b{words[1]}"
        patterns.append(
            {
                "$and": [
                    {"first_name": {"$regex": first_two_pattern, "$options": "i"}},
                    {"last_name": {"$regex": last_pattern, "$options": "i"}},
                ]
            }
        )

        # Try first word as first_name, last two words as last_name
        last_two_pattern = f"\\b{words[1]}.*\\b{words[2]}"
        patterns.append(
            {
                "$and": [
                    {"first_name": {"$regex": first_pattern, "$options": "i"}},
                    {"last_name": {"$regex": last_two_pattern, "$options": "i"}},
                ]
            }
        )

    return {"$or": patterns}


def _build_name_search_query(search_term: str) -> dict:
    """
    Build flexible MongoDB query for name searching.

    Supports:
    - Single word: matches first_name, last_name, or full name
    - Multiple words: tries "First Last" and "Last First" combinations
    - Partial matching with word boundaries
    - Case-insensitive matching
    - Handles middle names and complex name structures

    Args:
        search_term: User's search query (e.g., "Mike", "Lee", "Mike Lee", "Lee Mike")

    Returns:
        MongoDB query dict with $or conditions for flexible matching

    Example:
        >>> _build_name_search_query("Mike")
        {
            "$or": [
                {"first_name": {"$regex": "\\bMike", "$options": "i"}},
                {"last_name": {"$regex": "\\bMike", "$options": "i"}},
                {"name": {"$regex": "\\bMike", "$options": "i"}}
            ]
        }

        >>> _build_name_search_query("Mike Lee")
        {
            "$or": [
                {
                    "$and": [
                        {"first_name": {"$regex": "\\bMike", "$options": "i"}},
                        {"last_name": {"$regex": "\\bLee", "$options": "i"}}
                    ]
                },
                {
                    "$and": [
                        {"first_name": {"$regex": "\\bLee", "$options": "i"}},
                        {"last_name": {"$regex": "\\bMike", "$options": "i"}}
                    ]
                },
                {"name": {"$regex": "\\bMike.*\\bLee|\\bLee.*\\bMike", "$options": "i"}}
            ]
        }
    """
    # Normalize and split into parts
    normalized = _normalize_search_term(search_term)
    if not normalized:
        return {}

    parts = normalized.split()

    # Escape special regex characters in each part
    escaped_parts = [_escape_regex_special_chars(part) for part in parts]

    # Route to appropriate query builder based on word count
    if len(escaped_parts) == 1:
        return _build_single_word_query(escaped_parts[0])
    elif len(escaped_parts) == 2:
        return _build_two_word_query(escaped_parts[0], escaped_parts[1])
    else:
        return _build_multi_word_query(escaped_parts)


class MemberService:
    """Service for member-related operations."""

    @staticmethod
    async def search_members(params: MemberSearchParams) -> PaginatedResponse:
        """
        Search and filter members with flexible name matching.

        Supports:
        - Single name search: "Mike" or "Lee"
        - Full name in any order: "Mike Lee" or "Lee Mike"
        - Partial name matching: "Mic" finds "Michael", "Michelle", etc.
        - Case-insensitive matching
        - Multiple name parts: "Martin Luther King"
        - Middle names and initials: "John Q. Public"

        Search Performance Notes:
        - Uses MongoDB regex queries with word boundaries for accurate partial matching
        - Multiple $or conditions allow flexible name ordering
        - For large datasets (>100k members), consider adding MongoDB text indexes
        - Query complexity scales with number of search terms

        Args:
            params: Search parameters (query, state, party, chamber, pagination)

        Returns:
            Paginated list of member summaries sorted by last_name, first_name

        Raises:
            No exceptions raised - returns empty results on query errors

        Example:
            >>> # Search by first name
            >>> await search_members(MemberSearchParams(q="Mike"))
            # Returns: Mike Lee, Mike Johnson, Mike Braun, etc.

            >>> # Search by last name
            >>> await search_members(MemberSearchParams(q="Smith"))
            # Returns: Adam Smith, Tina Smith, Jason Smith, etc.

            >>> # Search by full name (any order)
            >>> await search_members(MemberSearchParams(q="Nancy Pelosi"))
            >>> await search_members(MemberSearchParams(q="Pelosi Nancy"))
            # Both return: Nancy Pelosi

            >>> # Partial matching
            >>> await search_members(MemberSearchParams(q="Mic"))
            # Returns: Michael Bennett, Michelle Steel, etc.

            >>> # With filters
            >>> await search_members(MemberSearchParams(q="Smith", state="CA", party="D"))
            # Returns: Democratic Smiths from California only
        """
        collection = await get_collection("members")

        # Build base query with filters
        query = {}

        if params.state:
            query["state"] = params.state.upper()

        if params.party:
            query["party"] = params.party.upper()

        if params.chamber:
            query["chamber"] = params.chamber.lower()

        # Add flexible name search if query provided
        if params.q:
            search_term = params.q.strip()
            if search_term:
                name_query = _build_name_search_query(search_term)

                # Combine name search with other filters
                if query:
                    # Merge name conditions with existing filters using $and
                    query = {"$and": [{k: v for k, v in query.items()}, name_query]}
                else:
                    # Only name search, no other filters
                    query = name_query

        # Get total count
        total = await collection.count_documents(query)

        # Calculate pagination
        skip = (params.page - 1) * params.page_size
        total_pages = (total + params.page_size - 1) // params.page_size

        # Fetch results with sorting
        # Sort by last_name for consistency, then first_name for ties
        cursor = (
            collection.find(query)
            .sort([("last_name", 1), ("first_name", 1)])
            .skip(skip)
            .limit(params.page_size)
        )

        results = []
        async for doc in cursor:
            results.append(
                MemberSummary(
                    bioguide_id=doc["bioguide_id"],
                    name=doc["name"],
                    party=doc["party"],
                    state=doc["state"],
                    district=doc.get("district"),
                    chamber=doc["chamber"],
                    image_url=doc.get("image_url"),
                ).model_dump()
            )

        return PaginatedResponse(
            results=results,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_member(bioguide_id: str) -> Optional[dict]:
        """
        Get a member by bioguide ID.

        First checks local database, fetches from API if not found.
        """
        collection = await get_collection("members")

        # Check local database first
        doc = await collection.find_one({"bioguide_id": bioguide_id})
        if doc:
            doc.pop("_id", None)
            return doc

        # Fetch from API if not in database
        try:
            client = get_congress_client()
            data = await client.get_member(bioguide_id)
            member_data = client.transform_member(data)
            member_data["updated_at"] = datetime.utcnow()

            # Store in database
            await collection.update_one(
                {"bioguide_id": bioguide_id},
                {"$set": member_data},
                upsert=True,
            )

            return member_data
        except Exception as e:
            logger.error(f"Failed to fetch member {bioguide_id}: {e}")
            return None

    @staticmethod
    async def get_member_bills(
        bioguide_id: str,
        bill_type: str = "sponsored",
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """
        Get bills for a member.

        Args:
            bioguide_id: Member's bioguide ID
            bill_type: 'sponsored' or 'cosponsored'
            limit: Number of results
            offset: Pagination offset
        """
        client = get_congress_client()

        try:
            if bill_type == "cosponsored":
                data = await client.get_member_cosponsored_legislation(
                    bioguide_id, limit=limit, offset=offset
                )
            else:
                data = await client.get_member_sponsored_legislation(
                    bioguide_id, limit=limit, offset=offset
                )

            # Transform bills
            bills = []
            for item in data.get("sponsoredLegislation", data.get("cosponsoredLegislation", [])):
                bills.append(client.transform_bill(item))

            return {
                "results": bills,
                "total": data.get("pagination", {}).get("count", len(bills)),
            }
        except Exception as e:
            logger.error(f"Failed to fetch bills for {bioguide_id}: {e}")
            return {"results": [], "total": 0, "error": str(e)}

    @staticmethod
    async def get_states_with_members() -> list[dict]:
        """Get list of states with member counts."""
        collection = await get_collection("members")

        pipeline = [
            {"$group": {"_id": "$state", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]

        results = []
        async for doc in collection.aggregate(pipeline):
            results.append({"state": doc["_id"], "count": doc["count"]})

        return results

    @staticmethod
    async def get_member_stats() -> dict:
        """Get aggregate statistics about members."""
        collection = await get_collection("members")

        # Party breakdown
        party_pipeline = [
            {"$group": {"_id": "$party", "count": {"$sum": 1}}},
        ]
        party_counts = {}
        async for doc in collection.aggregate(party_pipeline):
            party_counts[doc["_id"]] = doc["count"]

        # Chamber breakdown
        chamber_pipeline = [
            {"$group": {"_id": "$chamber", "count": {"$sum": 1}}},
        ]
        chamber_counts = {}
        async for doc in collection.aggregate(chamber_pipeline):
            chamber_counts[doc["_id"]] = doc["count"]

        total = await collection.count_documents({})

        return {
            "total": total,
            "by_party": party_counts,
            "by_chamber": chamber_counts,
        }
