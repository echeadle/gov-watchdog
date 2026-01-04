# Bill Search API - Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   cd backend
   pip install beautifulsoup4
   ```

   Or rebuild Docker:
   ```bash
   docker compose build backend
   ```

2. **Start the backend:**
   ```bash
   docker compose up backend
   ```

3. **Verify indexes:**
   Indexes are created automatically on startup via `ensure_indexes()`

## API Endpoint

**URL:** `GET /api/v1/bills/search/`

## Quick Examples

### 1. Get Recent Bills
```bash
curl "http://localhost:8000/api/v1/bills/search/?congress=119"
```

### 2. Search by Keyword
```bash
curl "http://localhost:8000/api/v1/bills/search/?q=climate"
```

### 3. Filter by Party
```bash
# Democrat sponsors only
curl "http://localhost:8000/api/v1/bills/search/?party=D&congress=119"

# Republican sponsors only
curl "http://localhost:8000/api/v1/bills/search/?party=R&congress=119"

# Independent sponsors only
curl "http://localhost:8000/api/v1/bills/search/?party=I&congress=119"
```

### 4. Filter by Subject
```bash
curl "http://localhost:8000/api/v1/bills/search/?subject=Environmental%20protection"
```

### 5. Combined Search
```bash
curl "http://localhost:8000/api/v1/bills/search/?q=tax&party=D&congress=119&page=1&page_size=10"
```

### 6. Pagination
```bash
# Page 1
curl "http://localhost:8000/api/v1/bills/search/?congress=119&page=1&page_size=20"

# Page 2
curl "http://localhost:8000/api/v1/bills/search/?congress=119&page=2&page_size=20"
```

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | No | - | Keyword search (searches title + summaries) |
| `party` | string | No | - | Filter by sponsor party: D, R, or I |
| `subject` | string | No | - | Filter by legislative subject name |
| `congress` | integer | No | 119 | Filter by congress number |
| `page` | integer | No | 1 | Page number (1-indexed) |
| `page_size` | integer | No | 20 | Results per page (max 100) |

## Response Format

```json
{
  "results": [
    {
      "bill_id": "hr1-119",
      "congress": 119,
      "type": "hr",
      "number": 1,
      "title": "Full bill title",
      "sponsor_id": "S000250",
      "introduced_date": "2025-01-07",
      "latest_action": "Referred to committee",
      "latest_action_date": "2025-01-07",
      "policy_area": "Economics and Public Finance",
      "legislative_subjects": ["Tax", "Income tax credits"],
      "summaries": [
        {
          "version_code": "00",
          "action_desc": "Introduced in House",
          "action_date": "2025-01-07",
          "text_html": "<p>HTML summary...</p>",
          "text_plain": "Plain text summary...",
          "updated_at": "2025-01-08T10:30:00"
        }
      ],
      "created_at": "2025-01-08T12:00:00",
      "updated_at": "2025-01-08T12:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

## Bill Types

| Code | Description |
|------|-------------|
| `hr` | House Bill |
| `s` | Senate Bill |
| `hjres` | House Joint Resolution |
| `sjres` | Senate Joint Resolution |
| `hconres` | House Concurrent Resolution |
| `sconres` | Senate Concurrent Resolution |
| `hres` | House Simple Resolution |
| `sres` | Senate Simple Resolution |

## Summary Version Codes

| Code | Stage |
|------|-------|
| `00` | Introduced |
| `07` | Reported to Committee |
| `53` | Passed House |
| `55` | Passed Senate |
| `49` | Public Law |

## How Incremental Sync Works

1. **First search**: System fetches 50 most recent bills from Congress 119
2. **Stores data**: Each bill stored with summaries and subjects (3 API calls per bill)
3. **Subsequent searches**: Use cached data from MongoDB
4. **Auto-sync**: If search returns < page_size results, fetches more bills

## Testing

### Run Test Script
```bash
cd backend
python test_bill_search.py
```

This will:
- Create database indexes
- Sync recent bills
- Test various search combinations
- Display sample results

### Check MongoDB
```bash
# Connect to MongoDB
docker exec -it gov-watchdog-mongodb-1 mongosh

# Use database
use gov_watchdog

# Count bills
db.bills.countDocuments()

# View a sample bill
db.bills.findOne()

# Check for bills with summaries
db.bills.findOne({ "summaries.0": { $exists: true } })

# Search by subject
db.bills.find({ legislative_subjects: "Environmental protection" }).limit(5)
```

## Common Use Cases

### 1. Find All Tax Bills by Democrats
```bash
curl "http://localhost:8000/api/v1/bills/search/?q=tax&party=D&congress=119"
```

### 2. Browse Bills by Policy Area
First, get bills and examine their `policy_area` field, then search:
```bash
curl "http://localhost:8000/api/v1/bills/search/?congress=119" | jq '.results[].policy_area' | sort -u
```

### 3. Find Bills on Specific Topic
```bash
curl "http://localhost:8000/api/v1/bills/search/?subject=Climate%20change&congress=119"
```

### 4. Get Bill Summary Text
```bash
curl "http://localhost:8000/api/v1/bills/search/?q=infrastructure" | jq '.results[0].summaries[0].text_plain'
```

## Error Handling

### No Results
If no results found, check:
- Congress number is correct (119 for current)
- Subject name is exact match
- Party is uppercase (D, R, I)

### Slow First Search
First search syncs 50 bills (150 API calls):
- Expect 1-3 minute delay
- Subsequent searches are instant
- Uses cached data

### API Rate Limit
Congress.gov limits to 5000 requests/hour:
- Service handles this with exponential backoff
- Check logs for rate limit errors
- Wait and retry

## Frontend Integration

### React Query Example
```typescript
import { useQuery } from '@tanstack/react-query';

const useBillSearch = (params: BillSearchParams) => {
  return useQuery({
    queryKey: ['bills', 'search', params],
    queryFn: async () => {
      const query = new URLSearchParams(params);
      const response = await fetch(
        `/api/v1/bills/search/?${query}`
      );
      return response.json();
    },
  });
};

// Usage
const { data, isLoading } = useBillSearch({
  q: 'climate',
  party: 'D',
  congress: 119,
  page: 1,
  page_size: 20,
});
```

### Display Summary
```typescript
const BillSummary = ({ bill }) => {
  const latestSummary = bill.summaries?.[0];

  return (
    <div>
      <h3>{bill.title}</h3>
      {latestSummary && (
        <div>
          <p className="text-sm text-gray-500">
            {latestSummary.action_desc} - {latestSummary.action_date}
          </p>
          <p>{latestSummary.text_plain.substring(0, 200)}...</p>
        </div>
      )}
    </div>
  );
};
```

## Troubleshooting

### Import Error: bs4
```bash
# Install beautifulsoup4
pip install beautifulsoup4

# Or rebuild Docker
docker compose build backend
```

### No Bills Synced
Check logs:
```bash
docker compose logs backend | grep -i sync
```

### MongoDB Connection Error
Verify MongoDB is running:
```bash
docker compose ps
docker compose up mongodb
```

## Performance Tips

1. **Use pagination** - Don't request all results at once
2. **Cache on frontend** - Use React Query or similar
3. **Specific searches** - Use subject filters instead of broad keyword searches
4. **Congress filter** - Always specify congress number

## Next Steps

1. Build frontend search UI
2. Add bill cards with summary snippets
3. Integrate with AI agent for natural language queries
4. Add subject auto-complete
5. Show policy area facets

## Support

- Full docs: `/docs/BILL-SEARCH-IMPLEMENTATION.md`
- API reference: `/.claude/scratchpad/BILL-SEARCH-QUICK-REF.md`
- Test script: `/backend/test_bill_search.py`
