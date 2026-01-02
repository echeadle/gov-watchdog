---
name: voting-analysis
description: Analyzes voting patterns and trends for Congress members. Use when comparing voting records, tracking party-line votes, or analyzing bipartisan voting.
allowed-tools: Read, Grep, Glob, Bash
---

# Voting Analysis Skill

## Purpose
This skill provides tools and patterns for analyzing Congressional voting data, including voting patterns, party alignment, bipartisanship metrics, and voting comparisons.

## Analysis Types

### 1. Party-Line Voting
Calculate how often a member votes with their party:
```python
async def calculate_party_loyalty(bioguide_id: str, congress: int) -> float:
    member = await db.members.find_one({"bioguide_id": bioguide_id})
    party = member["party"]

    votes = await db.votes.find({
        "congress": congress,
        f"votes.{bioguide_id}": {"$exists": True}
    }).to_list(None)

    party_votes = 0
    total_votes = 0

    for vote in votes:
        member_vote = vote["votes"].get(bioguide_id)
        if member_vote in ["Yea", "Nay"]:
            # Get party majority position
            party_majority = get_party_majority(vote, party)
            if member_vote == party_majority:
                party_votes += 1
            total_votes += 1

    return party_votes / total_votes if total_votes > 0 else 0
```

### 2. Bipartisanship Score
Measure cross-party voting:
```python
async def calculate_bipartisanship(bioguide_id: str, congress: int) -> float:
    member = await db.members.find_one({"bioguide_id": bioguide_id})
    party = member["party"]
    opposite_party = "D" if party == "R" else "R"

    votes = await db.votes.find({
        "congress": congress,
        f"votes.{bioguide_id}": {"$exists": True}
    }).to_list(None)

    bipartisan_votes = 0
    total_votes = 0

    for vote in votes:
        member_vote = vote["votes"].get(bioguide_id)
        if member_vote in ["Yea", "Nay"]:
            opposite_majority = get_party_majority(vote, opposite_party)
            if member_vote == opposite_majority:
                bipartisan_votes += 1
            total_votes += 1

    return bipartisan_votes / total_votes if total_votes > 0 else 0
```

### 3. Voting Similarity
Compare voting alignment between two members:
```python
async def calculate_voting_similarity(
    member1_id: str,
    member2_id: str,
    congress: int
) -> float:
    votes = await db.votes.find({
        "congress": congress,
        f"votes.{member1_id}": {"$exists": True},
        f"votes.{member2_id}": {"$exists": True},
    }).to_list(None)

    same_votes = 0
    total_votes = 0

    for vote in votes:
        v1 = vote["votes"].get(member1_id)
        v2 = vote["votes"].get(member2_id)
        if v1 in ["Yea", "Nay"] and v2 in ["Yea", "Nay"]:
            if v1 == v2:
                same_votes += 1
            total_votes += 1

    return same_votes / total_votes if total_votes > 0 else 0
```

### 4. Vote Participation Rate
```python
async def calculate_participation_rate(bioguide_id: str, congress: int) -> float:
    total_votes = await db.votes.count_documents({"congress": congress})
    member_votes = await db.votes.count_documents({
        "congress": congress,
        f"votes.{bioguide_id}": {"$in": ["Yea", "Nay", "Present"]}
    })
    return member_votes / total_votes if total_votes > 0 else 0
```

## Aggregation Pipelines

### Voting Statistics by Member
```python
voting_stats_pipeline = [
    {"$match": {"congress": 118}},
    {"$project": {
        "votes": {"$objectToArray": "$votes"}
    }},
    {"$unwind": "$votes"},
    {"$group": {
        "_id": "$votes.k",  # bioguide_id
        "total_votes": {"$sum": 1},
        "yea_votes": {
            "$sum": {"$cond": [{"$eq": ["$votes.v", "Yea"]}, 1, 0]}
        },
        "nay_votes": {
            "$sum": {"$cond": [{"$eq": ["$votes.v", "Nay"]}, 1, 0]}
        },
        "not_voting": {
            "$sum": {"$cond": [{"$eq": ["$votes.v", "Not Voting"]}, 1, 0]}
        },
    }},
    {"$sort": {"total_votes": -1}},
]
```

### Most Contentious Votes
```python
contentious_votes_pipeline = [
    {"$match": {"congress": 118}},
    {"$project": {
        "vote_id": 1,
        "question": 1,
        "date": 1,
        "margin": {
            "$abs": {
                "$subtract": ["$totals.yea", "$totals.nay"]
            }
        },
    }},
    {"$match": {"margin": {"$lt": 10}}},
    {"$sort": {"margin": 1}},
    {"$limit": 20},
]
```

## Visualization Data

### Voting Record Timeline
```python
async def get_voting_timeline(bioguide_id: str, congress: int):
    return await db.votes.aggregate([
        {"$match": {
            "congress": congress,
            f"votes.{bioguide_id}": {"$exists": True}
        }},
        {"$project": {
            "date": 1,
            "vote": f"$votes.{bioguide_id}",
            "question": 1,
            "bill_id": 1,
        }},
        {"$sort": {"date": 1}},
    ]).to_list(None)
```

## API Endpoints
- `GET /api/v1/members/{id}/voting-stats`
- `GET /api/v1/members/{id}/party-loyalty`
- `GET /api/v1/members/{id}/bipartisanship`
- `GET /api/v1/members/{id1}/compare/{id2}`
