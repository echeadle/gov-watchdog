"""
Bill service layer - business logic for bill operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from config.database import get_collection
from members.clients.congress import get_congress_client

logger = logging.getLogger(__name__)

# Sync tracking - tracks which congresses have been synced
_synced_congresses = set()


class BillService:
    """Service for bill-related operations."""

    @staticmethod
    async def get_bill(bill_id: str) -> Optional[dict]:
        """
        Get a bill by ID.

        First checks local database, fetches from API if not found.

        Args:
            bill_id: Bill ID in format {type}{number}-{congress} (e.g., hr1234-118)
        """
        collection = await get_collection("bills")

        # Check local database first
        doc = await collection.find_one({"bill_id": bill_id})
        if doc:
            doc.pop("_id", None)
            return doc

        # Parse bill_id
        try:
            parts = bill_id.rsplit("-", 1)
            if len(parts) != 2:
                return None

            type_and_number = parts[0]
            congress = int(parts[1])

            # Extract type and number
            import re

            match = re.match(r"([a-z]+)(\d+)", type_and_number)
            if not match:
                return None

            bill_type = match.group(1)
            bill_number = int(match.group(2))
        except (ValueError, AttributeError):
            return None

        # Fetch from API
        try:
            client = get_congress_client()
            data = await client.get_bill(congress, bill_type, bill_number)
            bill_data = client.transform_bill(data)
            bill_data["updated_at"] = datetime.utcnow()

            # Store in database
            await collection.update_one(
                {"bill_id": bill_id},
                {"$set": bill_data},
                upsert=True,
            )

            return bill_data
        except Exception as e:
            logger.error(f"Failed to fetch bill {bill_id}: {e}")
            return None

    @staticmethod
    async def get_bill_actions(bill_id: str, limit: int = 20) -> dict:
        """Get actions for a bill."""
        # Parse bill_id
        try:
            parts = bill_id.rsplit("-", 1)
            if len(parts) != 2:
                return {"results": [], "error": "Invalid bill ID format"}

            type_and_number = parts[0]
            congress = int(parts[1])

            import re

            match = re.match(r"([a-z]+)(\d+)", type_and_number)
            if not match:
                return {"results": [], "error": "Invalid bill ID format"}

            bill_type = match.group(1)
            bill_number = int(match.group(2))
        except (ValueError, AttributeError):
            return {"results": [], "error": "Invalid bill ID format"}

        try:
            client = get_congress_client()
            data = await client.get_bill_actions(congress, bill_type, bill_number, limit)

            actions = []
            for item in data.get("actions", []):
                actions.append(
                    {
                        "date": item.get("actionDate"),
                        "text": item.get("text", ""),
                        "action_type": item.get("type"),
                        "action_code": item.get("actionCode"),
                    }
                )

            return {"results": actions}
        except Exception as e:
            logger.error(f"Failed to fetch actions for {bill_id}: {e}")
            return {"results": [], "error": str(e)}

    @staticmethod
    async def fetch_bill_complete(
        congress: int, bill_type: str, bill_number: int
    ) -> Optional[dict]:
        """
        Fetch a complete bill with summaries and subjects from Congress.gov API.

        Makes 3 API calls:
        1. /bill/{congress}/{type}/{number} - Basic bill info
        2. /bill/{congress}/{type}/{number}/summaries - Bill summaries
        3. /bill/{congress}/{type}/{number}/subjects - Legislative subjects

        Returns:
            Complete bill data or None if not found
        """
        client = get_congress_client()

        try:
            # Fetch all three endpoints concurrently
            import asyncio

            bill_data, summaries_data, subjects_data = await asyncio.gather(
                client.get_bill(congress, bill_type, bill_number),
                client.get_bill_summaries(congress, bill_type, bill_number),
                client.get_bill_subjects(congress, bill_type, bill_number),
                return_exceptions=True,
            )

            # Check if bill fetch failed
            if isinstance(bill_data, Exception):
                logger.error(f"Failed to fetch bill: {bill_data}")
                return None

            # Handle optional failures for summaries/subjects
            if isinstance(summaries_data, Exception):
                logger.warning(f"Failed to fetch summaries: {summaries_data}")
                summaries_data = None

            if isinstance(subjects_data, Exception):
                logger.warning(f"Failed to fetch subjects: {subjects_data}")
                subjects_data = None

            # Transform with all available data
            bill = client.transform_bill(bill_data, summaries_data, subjects_data)
            if not bill:
                return None

            # Add metadata
            bill["updated_at"] = datetime.utcnow()
            bill["created_at"] = datetime.utcnow()

            return bill

        except Exception as e:
            logger.error(
                f"Error fetching bill {bill_type}{bill_number}-{congress}: {e}"
            )
            return None

    @staticmethod
    async def sync_recent_bills(congress: int = 119, limit: int = 50) -> int:
        """
        Sync recent bills from Congress.gov API.

        Fetches the most recent bills and stores them with full data
        (summaries and subjects) for search functionality.

        Args:
            congress: Congress number to sync (default: 119 for current)
            limit: Number of recent bills to fetch

        Returns:
            Number of bills synced
        """
        global _synced_congresses

        # Check if already synced
        if congress in _synced_congresses:
            logger.info(f"Congress {congress} already synced, skipping")
            return 0

        client = get_congress_client()
        collection = await get_collection("bills")

        try:
            logger.info(f"Syncing {limit} recent bills from Congress {congress}")

            # Fetch list of recent bills
            bills_response = await client.search_bills(
                congress=congress, limit=limit, offset=0
            )

            bills_list = bills_response.get("bills", [])
            if isinstance(bills_list, dict):
                bills_list = bills_list.get("item", [])

            synced_count = 0

            for bill_item in bills_list:
                bill = bill_item.get("bill", bill_item)
                bill_type = bill.get("type", "").lower()
                bill_number = bill.get("number")
                bill_congress = bill.get("congress")

                if not bill_type or not bill_number:
                    continue

                # Check if already exists
                bill_id = f"{bill_type}{bill_number}-{bill_congress}"
                existing = await collection.find_one({"bill_id": bill_id})

                if existing:
                    # Skip if recently updated (within 1 hour)
                    updated_at = existing.get("updated_at")
                    if updated_at and datetime.utcnow() - updated_at < timedelta(
                        hours=1
                    ):
                        continue

                # Fetch complete bill data
                complete_bill = await BillService.fetch_bill_complete(
                    bill_congress, bill_type, bill_number
                )

                if complete_bill:
                    # Store in database
                    await collection.update_one(
                        {"bill_id": bill_id},
                        {"$set": complete_bill},
                        upsert=True,
                    )
                    synced_count += 1
                    logger.debug(f"Synced bill {bill_id}")

            # Mark congress as synced
            _synced_congresses.add(congress)
            logger.info(f"Synced {synced_count} bills from Congress {congress}")

            return synced_count

        except Exception as e:
            logger.error(f"Error syncing bills from Congress {congress}: {e}")
            return 0

    @staticmethod
    async def search_bills(
        query: Optional[str] = None,
        party: Optional[str] = None,
        subject: Optional[str] = None,
        congress: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Search bills with incremental syncing.

        Strategy:
        1. Search local MongoDB first
        2. If results < page_size AND congress not synced yet:
           - Fetch recent bills from Congress.gov API
           - Store them with summaries/subjects
           - Re-run search
        3. Return paginated results

        Args:
            query: Keyword search (searches title and summaries)
            party: Filter by sponsor party (D, R, I)
            subject: Filter by legislative subject
            congress: Filter by congress number
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            Paginated search results with metadata
        """
        collection = await get_collection("bills")

        # Build query
        mongo_query = {}

        # Text search on title and summaries
        if query:
            mongo_query["$text"] = {"$search": query}

        # Filter by subject (partial, case-insensitive match)
        if subject:
            mongo_query["legislative_subjects"] = {"$regex": subject, "$options": "i"}

        # Filter by congress
        if congress:
            mongo_query["congress"] = congress

        # Filter by party (requires join with members)
        if party:
            members_collection = await get_collection("members")
            members_cursor = members_collection.find(
                {"party": party.upper()}, {"bioguide_id": 1}
            )
            party_member_ids = [m["bioguide_id"] async for m in members_cursor]
            mongo_query["sponsor_id"] = {"$in": party_member_ids}

        # Execute initial search
        total = await collection.count_documents(mongo_query)
        skip = (page - 1) * page_size
        total_pages = max(1, (total + page_size - 1) // page_size)

        # Check if we need to sync more data
        target_congress = congress or 119  # Default to current congress
        if total < page_size and target_congress not in _synced_congresses:
            logger.info(
                f"Insufficient results ({total}), syncing Congress {target_congress}"
            )
            await BillService.sync_recent_bills(target_congress)

            # Re-count after sync
            total = await collection.count_documents(mongo_query)
            total_pages = max(1, (total + page_size - 1) // page_size)

        # Fetch results with projection for text score if needed
        if query:
            # Include text score in projection for sorting
            projection = {"score": {"$meta": "textScore"}}
            cursor = (
                collection.find(mongo_query, projection)
                .sort([("score", {"$meta": "textScore"})])
                .skip(skip)
                .limit(page_size)
            )
        else:
            # Sort by introduced date
            cursor = (
                collection.find(mongo_query)
                .sort("introduced_date", -1)
                .skip(skip)
                .limit(page_size)
            )

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            doc.pop("score", None)  # Remove text search score from results
            results.append(doc)

        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
