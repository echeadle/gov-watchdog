---
name: committee-tracking
description: Tracks Congressional committee memberships and activities. Use when looking up committee assignments, hearings, or legislation progress through committees.
allowed-tools: Read, WebFetch, Bash
---

# Committee Tracking Skill

## Purpose
This skill tracks Congressional committees, their memberships, hearings, and the legislation they consider.

## Committee Data Structure

### From Congress.gov API
```json
{
  "committee": {
    "systemCode": "hsag00",
    "name": "Agriculture Committee",
    "chamber": "House",
    "type": "Standing",
    "parent": null,
    "subcommittees": [...],
    "bills": [...],
    "reports": [...],
    "nominations": [...],
    "communications": [...]
  }
}
```

### MongoDB Schema
```python
{
    "_id": ObjectId,
    "system_code": str,           # e.g., "hsag00"
    "name": str,
    "chamber": str,               # "House" or "Senate"
    "type": str,                  # "Standing", "Select", "Joint"
    "url": str,
    "parent_code": str | None,    # For subcommittees
    "members": [{
        "bioguide_id": str,
        "role": str,              # "Chair", "Ranking Member", "Member"
        "party": str,
    }],
    "jurisdiction": [str],
    "updated_at": datetime,
}
```

## Key API Endpoints

### Congress.gov Committee API
```
GET /committee                        # List all committees
GET /committee/{chamber}              # House or Senate committees
GET /committee/{systemCode}           # Specific committee
GET /committee/{systemCode}/bills     # Bills referred to committee
GET /committee/{systemCode}/reports   # Committee reports
```

## Committee Member Tracking

### Get Member's Committees
```python
async def get_member_committees(bioguide_id: str) -> list:
    committees = await db.committees.find({
        "members.bioguide_id": bioguide_id
    }).to_list(None)

    return [{
        "system_code": c["system_code"],
        "name": c["name"],
        "chamber": c["chamber"],
        "role": next(
            (m["role"] for m in c["members"]
             if m["bioguide_id"] == bioguide_id),
            "Member"
        ),
    } for c in committees]
```

### Get Committee Membership
```python
async def get_committee_members(system_code: str) -> dict:
    committee = await db.committees.find_one({"system_code": system_code})

    if not committee:
        return None

    # Enrich with member details
    member_ids = [m["bioguide_id"] for m in committee["members"]]
    members = await db.members.find(
        {"bioguide_id": {"$in": member_ids}}
    ).to_list(None)

    member_map = {m["bioguide_id"]: m for m in members}

    enriched_members = []
    for cm in committee["members"]:
        member = member_map.get(cm["bioguide_id"], {})
        enriched_members.append({
            **cm,
            "name": member.get("name"),
            "state": member.get("state"),
            "party": member.get("party"),
        })

    # Sort: Chair first, then Ranking Member, then by name
    role_order = {"Chair": 0, "Ranking Member": 1, "Vice Chair": 2}
    enriched_members.sort(
        key=lambda m: (role_order.get(m["role"], 99), m.get("name", ""))
    )

    return {
        **committee,
        "members": enriched_members,
    }
```

## Committee Bills Tracking

### Get Bills in Committee
```python
async def get_committee_bills(system_code: str, status: str = None) -> list:
    query = {"referred_committees": system_code}
    if status:
        query["committee_status"] = status

    bills = await db.bills.find(query).sort("updated_at", -1).limit(50).to_list(None)

    return [{
        "bill_id": b["bill_id"],
        "title": b["title"],
        "sponsor_id": b["sponsor_id"],
        "introduced_date": b["introduced_date"],
        "last_action": b.get("last_action"),
        "status": b.get("committee_status", "Referred"),
    } for b in bills]
```

### Bill Progress Through Committee
```python
COMMITTEE_STAGES = [
    "Referred",
    "Hearings Held",
    "Markup",
    "Ordered Reported",
    "Reported",
]

async def get_bill_committee_progress(bill_id: str) -> dict:
    bill = await db.bills.find_one({"bill_id": bill_id})

    committee_actions = [
        a for a in bill.get("actions", [])
        if is_committee_action(a)
    ]

    return {
        "bill_id": bill_id,
        "committees": bill.get("referred_committees", []),
        "current_stage": determine_committee_stage(committee_actions),
        "actions": committee_actions,
    }
```

## API Endpoints

### GET /api/v1/committees
```python
@api_view(['GET'])
async def list_committees(request):
    chamber = request.query_params.get('chamber')

    query = {}
    if chamber:
        query["chamber"] = chamber.title()

    committees = await db.committees.find(query).to_list(None)
    return Response([format_committee(c) for c in committees])
```

### GET /api/v1/committees/{code}
```python
@api_view(['GET'])
async def get_committee(request, system_code):
    committee = await get_committee_members(system_code)
    if not committee:
        return Response({"error": "Committee not found"}, status=404)
    return Response(committee)
```

### GET /api/v1/members/{id}/committees
```python
@api_view(['GET'])
async def member_committees(request, bioguide_id):
    committees = await get_member_committees(bioguide_id)
    return Response(committees)
```

## Response Format
```json
{
  "system_code": "hsag00",
  "name": "Agriculture Committee",
  "chamber": "House",
  "type": "Standing",
  "url": "https://agriculture.house.gov",
  "members": [
    {
      "bioguide_id": "T000467",
      "name": "Glenn Thompson",
      "role": "Chair",
      "party": "R",
      "state": "PA"
    },
    ...
  ],
  "subcommittees": [...],
  "pending_bills": 45,
  "reported_bills": 12
}
```

## Sync Strategy
- Sync committee data weekly
- Sync membership when Congress changes
- Track changes to leadership positions
