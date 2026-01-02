"""
MongoDB database connection using Motor (async driver).
"""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from django.conf import settings

logger = logging.getLogger(__name__)

# Global database connection
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.
    Creates connection on first call, reuses on subsequent calls.
    """
    global _client, _database

    if _database is None:
        logger.info("Connecting to MongoDB...")
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
        _database = _client[settings.MONGODB_DB]

        # Verify connection
        try:
            await _client.admin.command("ping")
            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    return _database


async def close_database():
    """Close the MongoDB connection."""
    global _client, _database

    if _client is not None:
        logger.info("Closing MongoDB connection...")
        _client.close()
        _client = None
        _database = None


# Collection names
COLLECTIONS = {
    "members": "members",
    "bills": "bills",
    "votes": "votes",
}


async def get_collection(name: str):
    """Get a specific collection by name."""
    db = await get_database()
    if name not in COLLECTIONS:
        raise ValueError(f"Unknown collection: {name}")
    return db[COLLECTIONS[name]]


async def ensure_indexes():
    """Create indexes for all collections. Skips if indexes already exist."""
    from pymongo.errors import OperationFailure

    db = await get_database()

    async def safe_create_index(collection, keys, **kwargs):
        """Create index, ignoring if it already exists."""
        try:
            await collection.create_index(keys, **kwargs)
        except OperationFailure as e:
            if e.code == 85:  # IndexOptionsConflict - index already exists
                logger.debug(f"Index already exists: {keys}")
            else:
                raise

    # Members indexes
    members = db[COLLECTIONS["members"]]
    await safe_create_index(members, "bioguide_id", unique=True)
    await safe_create_index(members, "state")
    await safe_create_index(members, "party")
    await safe_create_index(members, "chamber")

    # Name search indexes - optimized for flexible searching
    # 1. Compound index for sorted queries (last name, first name)
    await safe_create_index(members, [("last_name", 1), ("first_name", 1)])

    # 2. Case-insensitive indexes for exact and prefix matching
    await safe_create_index(
        members,
        "first_name",
        name="first_name_case_insensitive",
        collation={"locale": "en", "strength": 2}
    )
    await safe_create_index(
        members,
        "last_name",
        name="last_name_case_insensitive",
        collation={"locale": "en", "strength": 2}
    )

    # 3. Text index for full-text search (any order, partial matching)
    await safe_create_index(
        members,
        [("name", "text"), ("first_name", "text"), ("last_name", "text")],
        name="member_text_search",
        default_language="english",
    )

    # Bills indexes
    bills = db[COLLECTIONS["bills"]]
    await safe_create_index(bills, "bill_id", unique=True)
    await safe_create_index(bills, "sponsor_id")
    await safe_create_index(bills, "congress")
    await safe_create_index(bills, "introduced_date")
    await safe_create_index(bills, [("title", "text")], name="bill_text_search")

    # Votes indexes
    votes = db[COLLECTIONS["votes"]]
    await safe_create_index(votes, "vote_id", unique=True)
    await safe_create_index(votes, "bill_id")
    await safe_create_index(votes, "chamber")
    await safe_create_index(votes, "date")

    logger.info("Database indexes verified")
