---
name: congress-data-lookup
description: Fetches US Congress member data, bills, and voting records from Congress.gov API. Use when searching for representatives, senators, their legislation, or voting history.
allowed-tools: Read, Bash, WebFetch
---

# Congress Data Lookup Skill

## Purpose
This skill handles all interactions with the Congress.gov API to retrieve data about members, bills, and votes.

## Congress.gov API Reference

### Base URL
`https://api.congress.gov/v3`

### Authentication
- Header: `X-Api-Key: YOUR_API_KEY`
- Rate limit: 5000 requests/hour

### Key Endpoints

#### Members
```
GET /member                           # List all members
GET /member/{bioguideId}              # Get member by bioguide ID
GET /member/{bioguideId}/sponsored-legislation
GET /member/{bioguideId}/cosponsored-legislation
```

#### Bills
```
GET /bill                             # List all bills
GET /bill/{congress}/{billType}/{billNumber}
GET /bill/{congress}/{billType}/{billNumber}/actions
GET /bill/{congress}/{billType}/{billNumber}/cosponsors
GET /bill/{congress}/{billType}/{billNumber}/subjects
```

#### Votes (House)
```
GET /house-vote                       # List House votes
GET /house-vote/{congress}/{session}/{rollCallNumber}
```

#### Votes (Senate)
```
GET /senate-vote                      # List Senate votes
GET /senate-vote/{congress}/{session}/{rollCallNumber}
```

### Response Format
All responses follow this structure:
```json
{
  "request": {...},
  "results": [...] or {...},
  "pagination": {
    "count": 100,
    "next": "url_to_next_page"
  }
}
```

## Usage Patterns

### Search Members by State
```python
# Example: Get all California representatives
response = await fetch(
    f"{BASE_URL}/member?state=CA&chamber=house",
    headers={"X-Api-Key": api_key}
)
```

### Get Member's Bills
```python
# Get bills sponsored by a specific member
response = await fetch(
    f"{BASE_URL}/member/{bioguide_id}/sponsored-legislation",
    headers={"X-Api-Key": api_key}
)
```

### Get Voting Record
```python
# Get votes for a specific Congress session
response = await fetch(
    f"{BASE_URL}/house-vote?congress=118&session=1",
    headers={"X-Api-Key": api_key}
)
```

## Data Transformation

### Member Normalization
```python
def normalize_member(api_response):
    return {
        "bioguide_id": api_response["bioguideId"],
        "name": api_response["name"],
        "party": api_response["partyName"][0],  # D, R, or I
        "state": api_response["state"],
        "chamber": api_response["terms"][-1]["chamber"].lower(),
        "district": api_response.get("district"),
    }
```

## Error Handling
- 429: Rate limited - wait and retry
- 404: Resource not found - check ID format
- 500: Server error - retry with backoff

## Caching Strategy
- Cache member profiles for 24 hours
- Cache bills for 1 hour
- Cache votes for 30 minutes
