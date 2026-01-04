# Bill Search API - Implementation Guide

## Overview

The bill search API provides comprehensive search functionality for congressional bills with incremental syncing from Congress.gov. Bills are stored with full summaries and legislative subjects for rich search capabilities.

## Architecture

### Data Flow

```
User Request
    ↓
BillSearchView (views.py)
    ↓
BillService.search_bills() (services.py)
    ↓
├─→ Check MongoDB for existing data
├─→ If insufficient results: sync_recent_bills()
│   ├─→ CongressClient.search_bills() - Get bill list
│   ├─→ For each bill:
│   │   ├─→ CongressClient.get_bill() - Basic info
│   │   ├─→ CongressClient.get_bill_summaries() - CRS summaries
│   │   └─→ CongressClient.get_bill_subjects() - Topics
│   └─→ Store in MongoDB with transformed data
└─→ Return paginated results
```

### Components

1. **CongressClient** (`backend/members/clients/congress.py`)
   - `get_bill_summaries()` - Fetch bill summaries
   - `get_bill_subjects()` - Fetch legislative subjects
   - `strip_html()` - Convert HTML summaries to plain text
   - `transform_bill()` - Transform API data to MongoDB schema

2. **BillService** (`backend/bills/services.py`)
   - `fetch_bill_complete()` - Fetch bill with all 3 API calls
   - `sync_recent_bills()` - Incremental sync strategy
   - `search_bills()` - Main search method with filters

3. **BillSearchView** (`backend/bills/views.py`)
   - REST endpoint at `/api/v1/bills/search/`
   - Query parameter validation
   - Error handling

## API Endpoint

### `GET /api/v1/bills/search/`

Search bills with multiple filter options.

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Keyword search (title + summaries) | `climate change` |
| `party` | string | Filter by sponsor party (D, R, I) | `D` |
| `subject` | string | Filter by legislative subject | `Environmental protection` |
| `congress` | integer | Filter by congress number | `119` |
| `page` | integer | Page number (default: 1) | `2` |
| `page_size` | integer | Results per page (1-100, default: 20) | `50` |

**Response Format:**

```json
{
  "results": [
    {
      "bill_id": "hr1-119",
      "congress": 119,
      "type": "hr",
      "number": 1,
      "title": "Tax Relief for American Families and Workers Act of 2024",
      "sponsor_id": "S000250",
      "introduced_date": "2025-01-07",
      "policy_area": "Economics and Public Finance",
      "legislative_subjects": [
        "Climate change",
        "Environmental protection",
        "Carbon emissions"
      ],
      "summaries": [
        {
          "version_code": "00",
          "action_desc": "Introduced in House",
          "action_date": "2025-01-07",
          "text_html": "<p>This bill...</p>",
          "text_plain": "This bill modifies the tax code...",
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

## Examples

### Basic keyword search
```bash
curl "http://localhost:8000/api/v1/bills/search/?q=climate"
```

### Filter by party
```bash
curl "http://localhost:8000/api/v1/bills/search/?party=D&congress=119"
```

### Filter by subject
```bash
curl "http://localhost:8000/api/v1/bills/search/?subject=Environmental%20protection"
```

### Combined search
```bash
curl "http://localhost:8000/api/v1/bills/search/?q=tax&party=R&congress=119&page=1&page_size=10"
```

## Incremental Sync Strategy

### Why Incremental?

- Congress has ~10,000 bills per session
- Each bill requires 3 API calls (bill + summaries + subjects)
- Full sync = 30,000 API calls = 6-7 hours with 5000/hour rate limit

### How It Works

1. **First Search**: Fetches 50 most recent bills from Congress 119
2. **Stores Locally**: Full bill data with summaries and subjects
3. **Subsequent Searches**: Use cached data, only sync if needed
4. **Sync Trigger**: When search returns < page_size results AND congress not synced

### Sync Tracking

```python
# In-memory tracking (resets on server restart)
_synced_congresses = set()

# After syncing Congress 119:
_synced_congresses.add(119)
```

### Cache Strategy

Bills are cached with:
- `created_at`: When first stored
- `updated_at`: Last refresh time
- Re-sync skipped if `updated_at` < 1 hour ago

## Database Schema

### MongoDB Document

```javascript
{
  // Core identifiers
  "bill_id": "hr1-119",
  "congress": 119,
  "type": "hr",
  "number": 1,
  "title": "Tax Relief for American Families and Workers Act of 2024",
  "short_title": "Tax Relief Act",
  "sponsor_id": "S000250",
  "introduced_date": ISODate("2025-01-07"),
  "latest_action": "Referred to committee",
  "latest_action_date": ISODate("2025-01-07"),

  // NEW: Subjects (from /subjects endpoint)
  "policy_area": "Economics and Public Finance",
  "legislative_subjects": [
    "Taxation",
    "Income tax credits",
    "Families"
  ],

  // NEW: Summaries (from /summaries endpoint)
  "summaries": [
    {
      "version_code": "00",
      "action_desc": "Introduced in House",
      "action_date": ISODate("2025-01-07"),
      "text_html": "<p>HTML content...</p>",
      "text_plain": "Plain text for searching...",
      "updated_at": ISODate("2025-01-08T10:30:00")
    }
  ],

  // Metadata
  "created_at": ISODate("2025-01-08T12:00:00"),
  "updated_at": ISODate("2025-01-08T12:00:00")
}
```

### MongoDB Indexes

```javascript
// Unique identifier
db.bills.createIndex({ bill_id: 1 }, { unique: true })

// Filtering indexes
db.bills.createIndex({ sponsor_id: 1 })
db.bills.createIndex({ congress: 1 })
db.bills.createIndex({ introduced_date: 1 })
db.bills.createIndex({ legislative_subjects: 1 })  // Array index
db.bills.createIndex({ policy_area: 1 })

// Full-text search index
db.bills.createIndex(
  {
    "title": "text",
    "summaries.text_plain": "text"
  },
  {
    name: "bill_full_text_search",
    default_language: "english"
  }
)
```

## Implementation Details

### HTML Stripping

Summaries from Congress.gov are HTML-formatted. We strip HTML to create searchable plain text:

```python
from bs4 import BeautifulSoup

def strip_html(html_text: str) -> str:
    """Strip HTML tags and return plain text."""
    if not html_text:
        return ""

    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    # Normalize whitespace
    return " ".join(text.split())
```

### Concurrent API Calls

To minimize latency, we fetch all 3 endpoints concurrently:

```python
import asyncio

bill_data, summaries_data, subjects_data = await asyncio.gather(
    client.get_bill(congress, bill_type, bill_number),
    client.get_bill_summaries(congress, bill_type, bill_number),
    client.get_bill_subjects(congress, bill_type, bill_number),
    return_exceptions=True,
)
```

### Text Search Scoring

When using keyword search (`q` parameter), MongoDB returns results sorted by relevance:

```python
if query:
    projection = {"score": {"$meta": "textScore"}}
    cursor = (
        collection.find(mongo_query, projection)
        .sort([("score", {"$meta": "textScore"})])
        .skip(skip)
        .limit(page_size)
    )
```

## Testing

### Manual Testing

1. **Start backend:**
   ```bash
   docker compose up backend
   ```

2. **Test search:**
   ```bash
   curl "http://localhost:8000/api/v1/bills/search/?q=climate&congress=119"
   ```

3. **Verify MongoDB:**
   ```bash
   docker exec -it gov-watchdog-mongodb-1 mongosh
   use gov_watchdog
   db.bills.find().limit(1).pretty()
   ```

### Automated Testing

Run the test script:

```bash
cd backend
python test_bill_search.py
```

This will:
- Create indexes
- Sync recent bills
- Test various search combinations
- Display sample results

## Performance Considerations

### API Rate Limits

- Congress.gov: 5000 requests/hour
- 3 calls per bill = ~1666 bills/hour max
- Sync strategy: 50 bills on first search = 150 API calls

### Database Performance

- Text search uses indexes for fast queries
- Array index on `legislative_subjects` enables fast subject filtering
- Compound queries (party + subject + keyword) are optimized

### Caching

- Bills cached for 1 hour (`updated_at` check)
- Synced congresses tracked in memory
- Consider Redis for distributed deployments

## Future Enhancements

1. **Persistent Sync Tracking**
   - Store `_synced_congresses` in Redis/MongoDB
   - Survive server restarts

2. **Background Sync Job**
   - Celery task to sync all bills overnight
   - Refresh summaries for active bills

3. **Advanced Filters**
   - Date range filtering
   - Bill status filtering (introduced, passed, enacted)
   - Committee filtering

4. **Search Analytics**
   - Track popular searches
   - Suggest related subjects

5. **Faceted Search**
   - Return subject counts
   - Show policy area distribution

## Troubleshooting

### No results returned

- Check if Congress.gov API is accessible
- Verify `CONGRESS_API_KEY` in environment
- Check logs for API errors

### Slow search performance

- Verify indexes are created: `await ensure_indexes()`
- Check MongoDB query explain: `cursor.explain()`
- Consider increasing sync limit for faster initial load

### Missing summaries/subjects

- Some bills may not have summaries yet (newly introduced)
- Subjects endpoint may fail - service handles gracefully
- Check API logs for specific errors

## Related Files

- `/home/echeadle/Projects/Jan_01/gov-watchdog/backend/members/clients/congress.py` - API client
- `/home/echeadle/Projects/Jan_01/gov-watchdog/backend/bills/services.py` - Business logic
- `/home/echeadle/Projects/Jan_01/gov-watchdog/backend/bills/views.py` - REST endpoints
- `/home/echeadle/Projects/Jan_01/gov-watchdog/backend/bills/urls.py` - URL routing
- `/home/echeadle/Projects/Jan_01/gov-watchdog/backend/config/database.py` - Database setup
- `/home/echeadle/Projects/Jan_01/gov-watchdog/.claude/scratchpad/BILL-SEARCH-QUICK-REF.md` - API reference
