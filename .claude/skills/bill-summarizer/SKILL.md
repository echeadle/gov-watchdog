---
name: bill-summarizer
description: Summarizes complex legislation in plain language. Use when explaining bills, extracting key provisions, or identifying sponsors and cosponsors.
allowed-tools: Read, WebFetch, Bash
---

# Bill Summarizer Skill

## Purpose
This skill provides tools for summarizing and explaining Congressional legislation, making complex bills accessible to users.

## Bill Data Structure

### From Congress.gov API
```json
{
  "bill": {
    "congress": 118,
    "type": "HR",
    "number": 1234,
    "title": "Full title of the bill...",
    "introducedDate": "2023-01-15",
    "updateDate": "2023-06-01",
    "sponsors": [{
      "bioguideId": "A000001",
      "fullName": "Rep. Name [D-CA-12]"
    }],
    "cosponsors": [...],
    "latestAction": {
      "actionDate": "2023-05-15",
      "text": "Referred to committee..."
    },
    "policyArea": {"name": "Health"},
    "subjects": [...]
  }
}
```

## Summary Generation

### Using Claude for Summarization
```python
async def summarize_bill(bill_data: dict) -> dict:
    # Fetch full bill text if available
    bill_text = await fetch_bill_text(bill_data["textVersions"])

    prompt = f"""Summarize this Congressional bill for a general audience:

Title: {bill_data['title']}
Introduced: {bill_data['introducedDate']}
Sponsor: {bill_data['sponsors'][0]['fullName']}
Policy Area: {bill_data.get('policyArea', {}).get('name', 'N/A')}

Bill Text:
{bill_text[:10000]}  # Limit for context window

Please provide:
1. A one-paragraph plain language summary
2. Key provisions (bullet points)
3. Who it affects
4. Current status
"""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_summary_response(response.content[0].text)
```

## Bill Status Tracking

### Legislative Process Stages
```python
BILL_STAGES = [
    "Introduced",
    "Referred to Committee",
    "Committee Consideration",
    "Reported by Committee",
    "Floor Consideration",
    "Passed House" | "Passed Senate",
    "Passed Both Chambers",
    "Resolving Differences",
    "Sent to President",
    "Signed into Law" | "Vetoed" | "Pocket Vetoed",
]

def determine_bill_stage(actions: list) -> str:
    # Analyze actions to determine current stage
    for action in reversed(actions):
        if "became public law" in action["text"].lower():
            return "Signed into Law"
        if "passed" in action["text"].lower():
            if "house" in action["text"].lower():
                return "Passed House"
            if "senate" in action["text"].lower():
                return "Passed Senate"
        # ... more stage detection
    return "Introduced"
```

## Data Extraction Patterns

### Extract Sponsors and Cosponsors
```python
async def get_bill_sponsors(bill_id: str) -> dict:
    bill = await db.bills.find_one({"bill_id": bill_id})

    sponsor = await db.members.find_one(
        {"bioguide_id": bill["sponsor_id"]}
    )

    cosponsors = await db.members.find(
        {"bioguide_id": {"$in": bill["cosponsors"]}}
    ).to_list(None)

    return {
        "sponsor": format_member(sponsor),
        "cosponsors": [format_member(c) for c in cosponsors],
        "cosponsor_count": len(cosponsors),
        "bipartisan": has_bipartisan_support(sponsor, cosponsors),
    }
```

### Extract Related Bills
```python
async def get_related_bills(bill_id: str) -> list:
    bill = await db.bills.find_one({"bill_id": bill_id})
    subjects = bill.get("subjects", [])

    related = await db.bills.find({
        "subjects": {"$in": subjects},
        "bill_id": {"$ne": bill_id},
    }).limit(10).to_list(None)

    return related
```

## API Endpoints

### GET /api/v1/bills/{id}/summary
```python
@api_view(['GET'])
async def bill_summary(request, bill_id):
    bill = await get_bill(bill_id)

    # Check cache first
    cached = await cache.get(f"bill_summary:{bill_id}")
    if cached:
        return Response(cached)

    summary = await summarize_bill(bill)
    await cache.set(f"bill_summary:{bill_id}", summary, ttl=3600)

    return Response(summary)
```

### Response Format
```json
{
  "bill_id": "hr1234-118",
  "title": "Full title...",
  "short_title": "Short Title Act",
  "summary": "Plain language summary...",
  "key_provisions": [
    "Provision 1...",
    "Provision 2..."
  ],
  "affected_parties": ["Healthcare providers", "Patients"],
  "status": "Passed House",
  "progress_percentage": 60,
  "sponsor": {...},
  "cosponsor_count": 45,
  "last_action": "Referred to Senate committee..."
}
```

## Caching Strategy
- Cache summaries for 24 hours
- Invalidate when bill status changes
- Pre-generate summaries for trending bills
