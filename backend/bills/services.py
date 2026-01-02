"""
Bill service layer - business logic for bill operations.
"""

import logging
from datetime import datetime
from typing import Optional

from config.database import get_collection
from members.clients.congress import get_congress_client

logger = logging.getLogger(__name__)


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
    async def search_bills(
        congress: Optional[int] = None,
        bill_type: Optional[str] = None,
        sponsor_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Search bills in local database.

        For on-demand fetching, use member bills endpoints.
        """
        collection = await get_collection("bills")

        query = {}
        if congress:
            query["congress"] = congress
        if bill_type:
            query["type"] = bill_type.lower()
        if sponsor_id:
            query["sponsor_id"] = sponsor_id

        total = await collection.count_documents(query)
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        cursor = (
            collection.find(query)
            .sort("introduced_date", -1)
            .skip(skip)
            .limit(page_size)
        )

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)

        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
