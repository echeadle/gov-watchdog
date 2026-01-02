---
name: campaign-finance
description: Retrieves campaign finance data from FEC API. Use when looking up donations, expenditures, contributor information, or campaign funding.
allowed-tools: Read, Bash, WebFetch
---

# Campaign Finance Skill

## Purpose
This skill handles interactions with the Federal Election Commission (FEC) API to retrieve campaign finance data including contributions, expenditures, and candidate fundraising totals.

## FEC API Reference

### Base URL
`https://api.open.fec.gov/v1`

### Authentication
- Query parameter: `api_key=YOUR_API_KEY`
- Rate limit: 1000 requests/hour

### Key Endpoints

#### Candidates
```
GET /candidates/                      # Search candidates
GET /candidates/search/               # Full-text candidate search
GET /candidate/{candidate_id}/        # Get candidate details
GET /candidate/{candidate_id}/totals/ # Fundraising totals
GET /candidate/{candidate_id}/history/# Election history
```

#### Committees
```
GET /committees/                      # Search committees
GET /committee/{committee_id}/        # Committee details
GET /committee/{committee_id}/totals/ # Committee financials
```

#### Contributions (Schedule A)
```
GET /schedules/schedule_a/            # Individual contributions
GET /schedules/schedule_a/by_employer/# Contributions by employer
GET /schedules/schedule_a/by_occupation/
```

#### Disbursements (Schedule B)
```
GET /schedules/schedule_b/            # Disbursements/expenditures
GET /schedules/schedule_b/by_recipient/
GET /schedules/schedule_b/by_purpose/
```

#### Financial Summaries
```
GET /totals/by_entity/                # Totals by entity type
GET /elections/                       # Election cycle data
```

### Common Parameters
- `cycle`: Election cycle year (2024, 2022, etc.)
- `per_page`: Results per page (max 100)
- `page`: Page number
- `sort`: Sort field
- `sort_hide_null`: Exclude null values in sorting

## Usage Patterns

### Find Candidate by Name
```python
response = await fetch(
    f"{BASE_URL}/candidates/search/?q={name}&api_key={api_key}"
)
```

### Get Fundraising Totals
```python
response = await fetch(
    f"{BASE_URL}/candidate/{candidate_id}/totals/?cycle=2024&api_key={api_key}"
)
```

### Get Top Contributors
```python
response = await fetch(
    f"{BASE_URL}/schedules/schedule_a/?committee_id={committee_id}" +
    f"&sort=-contribution_receipt_amount&per_page=20&api_key={api_key}"
)
```

## Data Models

### Candidate Financial Summary
```python
{
    "candidate_id": str,
    "name": str,
    "party": str,
    "office": str,  # H, S, P
    "state": str,
    "district": str | None,
    "cycle": int,
    "receipts": float,
    "disbursements": float,
    "cash_on_hand": float,
    "debts_owed": float,
    "individual_contributions": float,
    "pac_contributions": float,
}
```

### Contribution Record
```python
{
    "contributor_name": str,
    "contributor_employer": str,
    "contributor_occupation": str,
    "contributor_city": str,
    "contributor_state": str,
    "contribution_receipt_amount": float,
    "contribution_receipt_date": date,
    "committee_id": str,
    "committee_name": str,
}
```

## FEC ID Mapping
FEC uses different IDs than Congress.gov. Cross-reference needed:
- Congress.gov: bioguide_id (e.g., "P000197")
- FEC: candidate_id (e.g., "H8CA12060")

## Error Handling
- 403: Invalid API key
- 429: Rate limited
- 422: Invalid parameters

## Caching Strategy
- Cache candidate totals for 24 hours
- Cache contribution data for 12 hours
- Update after FEC filing deadlines
