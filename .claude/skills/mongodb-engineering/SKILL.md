---
name: mongodb-engineering
description: MongoDB schema design and query optimization. Use when designing collections, writing aggregations, or optimizing database performance.
allowed-tools: Read, Write, Edit, Bash
---

# MongoDB Engineering Skill

## Connection Setup

### Motor Async Client
```python
# backend/config/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from django.conf import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        cls.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        cls.db = cls.client[settings.MONGODB_DB]
        await cls.create_indexes()

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    async def create_indexes(cls):
        # Members indexes
        await cls.db.members.create_index("bioguide_id", unique=True)
        await cls.db.members.create_index("state")
        await cls.db.members.create_index("party")
        await cls.db.members.create_index("chamber")
        await cls.db.members.create_index([("name", "text"), ("state", "text")])

        # Bills indexes
        await cls.db.bills.create_index("bill_id", unique=True)
        await cls.db.bills.create_index("sponsor_id")
        await cls.db.bills.create_index("congress")
        await cls.db.bills.create_index("cosponsors")
        await cls.db.bills.create_index([("title", "text")])

        # Votes indexes
        await cls.db.votes.create_index("vote_id", unique=True)
        await cls.db.votes.create_index([("chamber", 1), ("congress", 1)])
        await cls.db.votes.create_index("date")

mongodb = MongoDB()
```

## Schema Designs

### Members Collection
```python
member_schema = {
    "_id": "ObjectId",
    "bioguide_id": "string (unique)",      # Primary identifier
    "name": "string",                       # Full display name
    "first_name": "string",
    "last_name": "string",
    "party": "string",                      # D, R, I
    "state": "string",                      # Two-letter code
    "district": "int | null",               # House only
    "chamber": "string",                    # house, senate
    "terms": [{
        "congress": "int",
        "chamber": "string",
        "state": "string",
        "district": "int | null",
        "start_date": "date",
        "end_date": "date | null",
    }],
    "image_url": "string | null",
    "contact": {
        "website": "string | null",
        "phone": "string | null",
        "office": "string | null",
    },
    "social": {
        "twitter": "string | null",
        "facebook": "string | null",
    },
    "fec_candidate_id": "string | null",    # For campaign finance linking
    "created_at": "date",
    "updated_at": "date",
}
```

### Bills Collection
```python
bill_schema = {
    "_id": "ObjectId",
    "bill_id": "string (unique)",           # e.g., "hr1234-118"
    "congress": "int",
    "type": "string",                       # hr, s, hjres, sjres, etc.
    "number": "int",
    "title": "string",
    "short_title": "string | null",
    "sponsor_id": "string",                 # bioguide_id
    "cosponsors": ["string"],               # Array of bioguide_ids
    "policy_area": "string | null",
    "subjects": ["string"],
    "status": "string",
    "introduced_date": "date",
    "latest_action": {
        "date": "date",
        "text": "string",
    },
    "actions": [{
        "date": "date",
        "text": "string",
        "type": "string",
    }],
    "text_versions": [{
        "type": "string",
        "date": "date",
        "url": "string",
    }],
    "referred_committees": ["string"],      # Committee system codes
    "created_at": "date",
    "updated_at": "date",
}
```

### Votes Collection
```python
vote_schema = {
    "_id": "ObjectId",
    "vote_id": "string (unique)",           # e.g., "h2024-123"
    "chamber": "string",                    # house, senate
    "congress": "int",
    "session": "int",
    "roll_call": "int",
    "date": "date",
    "question": "string",
    "description": "string | null",
    "result": "string",                     # Passed, Failed, etc.
    "bill_id": "string | null",             # Related bill if any
    "amendment_id": "string | null",
    "votes": {
        "bioguide_id": "string",            # Yea, Nay, Not Voting, Present
    },
    "totals": {
        "yea": "int",
        "nay": "int",
        "not_voting": "int",
        "present": "int",
    },
    "party_breakdown": {
        "D": {"yea": "int", "nay": "int"},
        "R": {"yea": "int", "nay": "int"},
        "I": {"yea": "int", "nay": "int"},
    },
    "created_at": "date",
    "updated_at": "date",
}
```

## Common Query Patterns

### Text Search
```python
async def search_members(query: str, limit: int = 20):
    cursor = mongodb.db.members.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    return await cursor.to_list(length=limit)
```

### Filtered Queries
```python
async def get_members_by_state_and_party(state: str, party: str):
    return await mongodb.db.members.find({
        "state": state.upper(),
        "party": party.upper(),
    }).to_list(None)
```

### Projections (Select Fields)
```python
async def get_member_summary(bioguide_id: str):
    return await mongodb.db.members.find_one(
        {"bioguide_id": bioguide_id},
        {"name": 1, "party": 1, "state": 1, "chamber": 1, "_id": 0}
    )
```

## Aggregation Pipelines

### Bills Per Member
```python
bills_per_member_pipeline = [
    {"$group": {
        "_id": "$sponsor_id",
        "bill_count": {"$sum": 1},
        "bills": {"$push": "$bill_id"},
    }},
    {"$sort": {"bill_count": -1}},
    {"$limit": 20},
    {"$lookup": {
        "from": "members",
        "localField": "_id",
        "foreignField": "bioguide_id",
        "as": "member",
    }},
    {"$unwind": "$member"},
    {"$project": {
        "bioguide_id": "$_id",
        "name": "$member.name",
        "party": "$member.party",
        "bill_count": 1,
    }},
]
```

### Voting Stats
```python
async def get_voting_statistics(bioguide_id: str, congress: int):
    pipeline = [
        {"$match": {
            "congress": congress,
            f"votes.{bioguide_id}": {"$exists": True},
        }},
        {"$group": {
            "_id": f"$votes.{bioguide_id}",
            "count": {"$sum": 1},
        }},
    ]

    results = await mongodb.db.votes.aggregate(pipeline).to_list(None)

    stats = {"Yea": 0, "Nay": 0, "Not Voting": 0, "Present": 0}
    for r in results:
        stats[r["_id"]] = r["count"]

    return stats
```

## Performance Optimization

### Use Explain
```python
async def analyze_query(query: dict):
    explanation = await mongodb.db.members.find(query).explain()
    return {
        "execution_time_ms": explanation["executionStats"]["executionTimeMillis"],
        "docs_examined": explanation["executionStats"]["totalDocsExamined"],
        "docs_returned": explanation["executionStats"]["nReturned"],
        "index_used": explanation["queryPlanner"]["winningPlan"].get("inputStage", {}).get("indexName"),
    }
```

### Bulk Operations
```python
from pymongo import UpdateOne

async def bulk_update_members(updates: list):
    operations = [
        UpdateOne(
            {"bioguide_id": u["bioguide_id"]},
            {"$set": u["data"]},
            upsert=True
        )
        for u in updates
    ]

    result = await mongodb.db.members.bulk_write(operations)
    return {
        "inserted": result.upserted_count,
        "modified": result.modified_count,
    }
```

## Docker Compose MongoDB
```yaml
services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}

volumes:
  mongodb_data:
```
