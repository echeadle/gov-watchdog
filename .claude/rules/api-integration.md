---
paths: backend/**/clients/*.py, frontend/src/services/*.ts
---

# API Integration Rules

## Congress.gov API

### Authentication
- API key required in header: `X-Api-Key`
- Rate limit: 5000 requests/hour

### Key Endpoints
```python
# Members
GET /member                    # List all members
GET /member/{bioguideId}       # Get member details
GET /member/{bioguideId}/sponsored-legislation

# Bills
GET /bill                      # List bills
GET /bill/{congress}/{type}/{number}
GET /bill/{congress}/{type}/{number}/actions

# Votes
GET /house-vote/{congress}/{session}/{rollCallNumber}
GET /senate-vote/{congress}/{session}/{rollCallNumber}
```

### Response Handling
- Check for pagination in responses
- Handle rate limiting with exponential backoff
- Cache responses where appropriate

## FEC API

### Authentication
- API key required: `api_key` parameter

### Key Endpoints
```python
# Candidates
GET /candidates/              # Search candidates
GET /candidate/{candidate_id}/totals

# Contributions
GET /schedules/schedule_a/    # Individual contributions
GET /schedules/schedule_b/    # Disbursements

# Committees
GET /committees/              # List committees
```

## Best Practices

### Error Handling
```python
class APIError(Exception):
    def __init__(self, status_code, message, details=None):
        self.status_code = status_code
        self.message = message
        self.details = details

async def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                await asyncio.sleep(2 ** attempt)
            else:
                raise APIError(e.response.status_code, str(e))
    raise APIError(429, "Max retries exceeded")
```

### Caching
- Cache member data for 24 hours
- Cache bill data for 1 hour
- Invalidate cache on data updates
- Use Redis or MongoDB for cache storage

### Data Transformation
- Normalize API responses to internal models
- Handle missing or null fields gracefully
- Convert dates to consistent timezone (UTC)
