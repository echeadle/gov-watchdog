# Congress.gov Bill API - Complete Reference

Comprehensive reference for bill summaries and subjects endpoints. Last updated: 2026-01-04

---

## Quick Reference

### Summaries Endpoint
**URL:** `GET /bill/{congress}/{type}/{number}/summaries`
**Example:** `GET /bill/119/hr/1/summaries?api_key=KEY`

**Key Facts:**
- **Content Size:** 15,000-65,000 characters per summary (HTML formatted)
- **Author:** Congressional Research Service (CRS)
- **Versions:** Up to 5 versions tracking bill progression
- **Version Codes:** 00 (Introduced), 07 (Committee), 53 (Passed House), 55 (Passed Senate), 49 (Public Law)
- **Cache TTL:** 1 hour (frequently updated during active session)

### Subjects Endpoint
**URL:** `GET /bill/{congress}/{type}/{number}/subjects`
**Example:** `GET /bill/119/hr/1/subjects?api_key=KEY`

**Key Facts:**
- **Structure:** Flat array (no hierarchy/nesting)
- **Subject Count:** 10-238 subjects per bill (varies by scope)
- **Policy Area:** Single top-level category
- **Pagination:** 20 subjects per page
- **Cache TTL:** 24 hours (rarely change)

---

## API Response Structures

### Summaries Response
```json
{
  "request": { /* metadata */ },
  "summaries": [
    {
      "actionDate": "2025-01-07",
      "actionDesc": "Introduced in House",
      "text": "<html>...(15k-65k characters)...</html>",
      "updateDate": "2025-01-10T15:30:00Z",
      "versionCode": "00"
    },
    {
      "actionDate": "2025-02-15",
      "actionDesc": "Passed House",
      "text": "<html>...(updated summary)...</html>",
      "updateDate": "2025-02-16T10:00:00Z",
      "versionCode": "53"
    }
  ]
}
```

**Field Descriptions:**
| Field | Type | Description |
|-------|------|-------------|
| actionDate | ISO 8601 date | When the legislative action occurred |
| actionDesc | string | Human-readable description ("Introduced in House", etc.) |
| text | HTML string | Full summary content (15k-65k chars) |
| updateDate | ISO 8601 timestamp | Last modification time |
| versionCode | string | Version identifier (00-99) |

### Subjects Response
```json
{
  "request": { /* metadata */ },
  "subjects": {
    "legislativeSubjects": [
      {
        "name": "Abortion",
        "updateDate": "2025-01-10T15:30:00Z"
      },
      {
        "name": "Agricultural conservation and pollution",
        "updateDate": "2025-01-10T15:30:00Z"
      }
      // ... up to 238 subjects
    ],
    "policyArea": {
      "name": "Economics and Public Finance",
      "updateDate": "2025-01-10T15:30:00Z"
    }
  }
}
```

---

## Version Codes Reference

| Code | Stage | Summary Completeness |
|------|-------|---------------------|
| 00 | Introduced | Basic overview |
| 07 | Reported to House Committee | Committee analysis added |
| 53 | Passed House | Amendments documented |
| 54 | Engrossed in House | Final House version |
| 55 | Passed Senate | Senate amendments documented |
| 56 | Engrossed in Senate | Final Senate version |
| 49 | Becomes Public Law | Final law version |

---

## MongoDB Schema

### Bills Collection - Extended
```javascript
{
  "_id": ObjectId,
  "bill_id": "hr1-119",              // Unique identifier
  "congress": 119,
  "type": "hr",                      // "hr", "s", "hjres", "sjres", etc.
  "number": 1,
  "title": "Official title...",

  // Classification (from /subjects endpoint)
  "policy_area": "Economics and Public Finance",
  "legislative_subjects": [
    "Abortion",
    "Agricultural conservation and pollution",
    // ... up to 238 subjects
  ],

  // Content history (from /summaries endpoint)
  "summaries": [
    {
      "version_code": "00",
      "action_date": ISODate("2025-01-07"),
      "action_desc": "Introduced in House",
      "text_html": "<p>...</p>",
      "text_plain": "...",           // Stripped HTML for search
      "updated_at": ISODate("2025-01-10T15:30:00Z"),
      "char_count": 15432
    }
  ],

  // Metadata
  "sponsor_id": "B000001",           // bioguide_id
  "introduced_date": ISODate("2025-01-07"),
  "latest_version": "00",
  "created_at": ISODate("2025-01-07"),
  "updated_at": ISODate("2025-01-10")
}
```

### Indexes
```javascript
// Full-text search on summaries and title
db.bills.createIndex({
  "title": "text",
  "summaries.text_plain": "text"
})

// Subject filtering
db.bills.createIndex({ "legislative_subjects": 1 })

// Policy area browsing
db.bills.createIndex({ "policy_area": 1 })

// Congress lookup
db.bills.createIndex({ "congress": 1, "type": 1, "number": 1 })

// Sponsor lookup
db.bills.createIndex({ "sponsor_id": 1 })
```

---

## Query Examples

### Search by subject (partial match)
```javascript
db.bills.find({
  legislative_subjects: { $regex: "Immigrat", $options: "i" }
})
// Matches: "Immigration", "Immigration law", "Border security and unlawful immigration"
```

### Full-text search in summaries
```javascript
db.bills.find({
  $text: { $search: "climate change adaptation" }
})
```

### Filter by policy area
```javascript
db.bills.find({
  policy_area: "Defense",
  congress: 118
})
```

### Combined search (policy area + subject + keyword)
```javascript
db.bills.find({
  policy_area: "Defense",
  legislative_subjects: { $regex: "Military", $options: "i" },
  $text: { $search: "readiness" }
})
```

### Get all versions of a bill
```javascript
db.bills.findOne(
  { bill_id: "hr1-119" },
  { summaries: 1 }
)
```

### Get latest summary version
```javascript
db.bills.aggregate([
  { $match: { bill_id: "hr1-119" } },
  { $unwind: "$summaries" },
  { $sort: { "summaries.updated_at": -1 } },
  { $limit: 1 },
  { $replaceRoot: { newRoot: "$summaries" } }
])
```

---

## API Fetching Workflow

### Single Bill - Complete Data (3 API Calls)
```python
async def fetch_complete_bill(congress: int, bill_type: str, number: int):
    """Fetch bill with summaries and subjects from Congress.gov API"""

    # Call 1: Basic bill info
    bill = await api.get_bill(congress, bill_type, number)

    # Call 2: All summaries (versions)
    summaries_response = await api.get_summaries(congress, bill_type, number)

    # Call 3: Subjects and policy area
    subjects_response = await api.get_subjects(congress, bill_type, number)

    # Combine into single document
    return {
        "bill_id": f"{bill_type}{number}-{congress}",
        "congress": congress,
        "type": bill_type,
        "number": number,
        "title": bill["title"],
        "sponsor_id": bill.get("sponsor", {}).get("bioguideId"),
        "introduced_date": bill.get("introducedDate"),

        # Extract policy area
        "policy_area": subjects_response.get("subjects", {})
            .get("policyArea", {}).get("name"),

        # Extract legislative subjects
        "legislative_subjects": [
            s["name"]
            for s in subjects_response.get("subjects", {})
                .get("legislativeSubjects", [])
        ],

        # Process summaries
        "summaries": [
            {
                "version_code": s["versionCode"],
                "action_date": s["actionDate"],
                "action_desc": s["actionDesc"],
                "text_html": s["text"],
                "text_plain": strip_html(s["text"]),
                "updated_at": s["updateDate"],
                "char_count": len(s["text"])
            }
            for s in summaries_response.get("summaries", [])
        ],

        "latest_version": max(
            s["versionCode"] for s in summaries_response.get("summaries", [])
        ) if summaries_response.get("summaries") else None,

        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
```

### HTML Stripping Utility
```python
def strip_html(html_text: str) -> str:
    """Strip HTML tags from summary text using BeautifulSoup"""
    if not html_text:
        return ""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text()
    except Exception as e:
        logger.warning(f"Error stripping HTML: {e}")
        return html_text
```

---

## Search Implementation Patterns

### Pattern 1: Subject Filter Dropdown
User selects from predefined subjects (Government, Health, Climate, etc.)
- Use partial regex matching: `{"$regex": subject, "$options": "i"}`
- Matches both exact terms and variations

### Pattern 2: Full-Text Search Box
User types freeform query
- Searches `title` and `summaries.text_plain` fields
- MongoDB text index required
- Returns relevance-scored results

### Pattern 3: Policy Area Browse
User clicks top-level category (Defense, Economics, Environment)
- Filter by `policy_area` field
- Then optionally add subject filter

### Pattern 4: Advanced Search
Combine multiple filters
- Policy area: dropdown
- Subjects: multi-select or text input
- Keywords: text search box
- Congress: dropdown (118, 119, 117, etc.)
- Party: filter by sponsor's party

---

## Performance & Optimization

### API Efficiency
| Operation | Data Size | API Calls |
|-----------|-----------|-----------|
| Basic bill info | 2 KB | 1 |
| Summaries | 50 KB | 1 |
| Subjects | 15 KB | 1 |
| **Total per bill** | ~65 KB | 3 |
| Full congress (10,000 bills) | 650 MB | 30,000 |

### Rate Limiting
- **Limit:** 5,000 requests/hour
- **Bills per hour:** ~1,666 (3 calls each)
- **Time for full congress:** 6-7 hours

### Caching Strategy
- **Summaries:** 1 hour TTL (updated during active session)
- **Subjects:** 24 hours TTL (rarely change)
- **Policy areas:** 7 days TTL (static list)

### Query Performance (indexed)
- Subject array query: < 10ms
- Full-text search: 50-200ms (depends on result set)
- Combined query (policy + subject): < 50ms

---

## Implementation Checklist

- [x] Parse HTML from summaries (BeautifulSoup4)
- [x] Store both HTML and plain text versions
- [x] Create full-text index on summary text
- [x] Create array index on legislative_subjects
- [x] Create index on policy_area
- [x] Implement partial regex matching for subject filters
- [x] Handle pagination in /subjects endpoint
- [x] Map version codes to human-readable text
- [x] Add search filters to UI (party, subject, congress, keyword)
- [x] Implement export functionality with unique timestamps

---

## Common Gotchas

1. **HTML in summaries** - Must strip/parse for plain text search
2. **Many subjects** - Up to 238 per bill, use pagination if displaying all
3. **Version codes** - Map numeric codes ("00") to human-readable ("Introduced")
4. **Subject names** - Some are long, allow partial/fuzzy matching
5. **Policy area** - Single value per bill, good for primary grouping
6. **API endpoint format** - Use `/bill/{congress}` NOT `?congress={congress}` (query param ignored!)
7. **Type checking** - API sometimes returns lists instead of dicts, validate before `.get()`
8. **Congress data availability** - Congress 118 has full data, Congress 119 (current) has limited CRS analysis

---

## Real-World Example: HR1 (119th Congress)

### Basic Info
- **Bill ID:** hr1-119
- **Title:** Budget reconciliation bill (omnibus/complex)
- **Policy Area:** Economics and Public Finance
- **Subjects:** 238 legislative subjects
- **Summaries:** Multiple versions (15k-65k chars each)

### Subject Diversity
- Policy domains: Abortion, Accounting, Administrative law
- Technology: Advanced technology and technological innovations
- Agriculture: Conservation, insurance, prices, subsidies
- Environment: Air quality, climate change
- Geography: State references (Alaska, Alabama, etc.)

### Summary Progression
1. **Version 00 (Introduced):** Basic overview at introduction (~15k chars)
2. **Version 53 (Passed House):** Expanded with committee details and House amendments (~30k chars)
3. **Version 55 (Passed Senate):** Further expanded with Senate amendments (~45k chars)
4. **Version 49 (Public Law):** Final law version with all modifications (~65k chars)

---

## Related Files

- **Strategic guide:** `bill-search-summary.md`
- **Implementation notes:** `bill-search-implementation-summary.md`
- **Documentation index:** `BILL-API-INVESTIGATION.md`
- **Research notes:** `research-notes.md`
