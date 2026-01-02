---
paths: backend/**/models/*.py, backend/**/repositories/*.py
---

# MongoDB Development Rules

## Connection Management
```python
from motor.motor_asyncio import AsyncIOMotorClient

# Use connection pooling
client = AsyncIOMotorClient(
    MONGODB_URI,
    maxPoolSize=50,
    minPoolSize=10,
)
db = client.gov_watchdog
```

## Schema Design

### Members Collection
```python
{
    "_id": ObjectId,
    "bioguide_id": str,          # Primary identifier
    "name": str,
    "first_name": str,
    "last_name": str,
    "party": str,                # "D", "R", "I"
    "state": str,                # State code
    "district": int | None,      # House only
    "chamber": str,              # "house" or "senate"
    "terms": [...],
    "contact": {...},
    "created_at": datetime,
    "updated_at": datetime,
}
```

### Bills Collection
```python
{
    "_id": ObjectId,
    "bill_id": str,              # e.g., "hr1234-118"
    "congress": int,
    "type": str,                 # "hr", "s", "hjres", etc.
    "number": int,
    "title": str,
    "sponsor_id": str,           # bioguide_id
    "cosponsors": [str],
    "status": str,
    "introduced_date": datetime,
    "actions": [...],
    "created_at": datetime,
    "updated_at": datetime,
}
```

### Votes Collection
```python
{
    "_id": ObjectId,
    "vote_id": str,
    "chamber": str,
    "congress": int,
    "session": int,
    "roll_call": int,
    "date": datetime,
    "question": str,
    "result": str,
    "bill_id": str | None,
    "votes": {
        "bioguide_id": "Yea" | "Nay" | "Not Voting" | "Present"
    },
    "totals": {
        "yea": int,
        "nay": int,
        "not_voting": int,
        "present": int,
    },
}
```

## Indexing Strategy
```python
# Create indexes on startup
await db.members.create_index("bioguide_id", unique=True)
await db.members.create_index("state")
await db.members.create_index([("name", "text")])

await db.bills.create_index("bill_id", unique=True)
await db.bills.create_index("sponsor_id")
await db.bills.create_index("congress")

await db.votes.create_index("vote_id", unique=True)
await db.votes.create_index([("chamber", 1), ("congress", 1)])
```

## Query Patterns
```python
# Search members by state
async def get_members_by_state(state: str):
    return await db.members.find({"state": state}).to_list(None)

# Full-text search
async def search_members(query: str):
    return await db.members.find(
        {"$text": {"$search": query}}
    ).to_list(100)

# Aggregation example
async def get_voting_stats(bioguide_id: str):
    pipeline = [
        {"$match": {f"votes.{bioguide_id}": {"$exists": True}}},
        {"$group": {
            "_id": f"$votes.{bioguide_id}",
            "count": {"$sum": 1}
        }}
    ]
    return await db.votes.aggregate(pipeline).to_list(None)
```

## Best Practices
- Use async operations with Motor
- Limit result sets with `.to_list(limit)`
- Use projections to reduce data transfer
- Handle ObjectId serialization for JSON responses
