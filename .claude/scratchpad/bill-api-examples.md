# Congress.gov Bill API - Practical Examples

## Real Data Examples from HR1 (119th Congress)

### Example 1: Summaries Endpoint Response

**Request:**
```
GET https://api.congress.gov/v3/bill/119/hr/1/summaries?api_key=DEMO_KEY
```

**Key Response Fields:**

```json
{
  "summaries": [
    {
      "actionDate": "2025-01-07",
      "actionDesc": "Introduced in House",
      "versionCode": "00",
      "updateDate": "2025-01-10T15:30:00Z",
      "text": "<html><p>This bill reduces taxes, reduces or increases spending for various federal programs...</p></html>"
    },
    {
      "actionDate": "2025-02-15",
      "actionDesc": "Passed House",
      "versionCode": "53",
      "updateDate": "2025-02-16T10:00:00Z",
      "text": "<html><p>(Updated summary with more detail)...</p></html>"
    },
    {
      "actionDate": "2025-03-20",
      "actionDesc": "Passed Senate",
      "versionCode": "55",
      "updateDate": "2025-03-21T14:15:00Z",
      "text": "<html><p>(Further updated summary)...</p></html>"
    }
  ]
}
```

**Summary Progression:**
- Version 00 (Introduced): Brief overview at introduction
- Version 53 (Passed House): Expanded with committee details and amendments
- Version 55 (Passed Senate): Further expanded with Senate amendments and floor discussions

---

### Example 2: Subjects Endpoint Response

**Request:**
```
GET https://api.congress.gov/v3/bill/119/hr/1/subjects?api_key=DEMO_KEY
```

**Key Response Fields:**

```json
{
  "subjects": {
    "policyArea": {
      "name": "Economics and Public Finance",
      "updateDate": "2025-01-10T15:30:00Z"
    },
    "legislativeSubjects": [
      { "name": "Abortion", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Accounting and auditing", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Administrative law and regulatory procedures", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Advanced technology and technological innovations", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Agricultural conservation and pollution", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Agricultural insurance", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Agricultural prices, subsidies, credit", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Air quality", "updateDate": "2025-01-10T15:30:00Z" },
      { "name": "Alaska", "updateDate": "2025-01-10T15:30:00Z" },
      // ... (up to 238 total subjects)
    ]
  }
}
```

**Note on Subject Diversity:**
- Policy domains: Abortion, Accounting, Administrative law
- Technology: Advanced technology
- Agriculture: Multiple subjects (conservation, insurance, prices)
- Environment: Air quality
- Geography: State references (Alaska, Alabama, Afghanistan)

This broad subject list indicates this is a comprehensive/omnibus bill affecting many policy areas.

---

## Combined Data Structure for Storage

### How to Combine Both Endpoints in MongoDB

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  
  // Basic identifiers
  "bill_id": "hr1-119",
  "congress": 119,
  "type": "hr",
  "number": 1,
  "title": "[Full official title from /bill endpoint]",
  
  // Classification (from /subjects)
  "policy_area": "Economics and Public Finance",
  "legislative_subjects": [
    "Abortion",
    "Accounting and auditing",
    "Administrative law and regulatory procedures",
    "Advanced technology and technological innovations",
    "Agricultural conservation and pollution",
    "Agricultural insurance",
    "Agricultural prices, subsidies, credit",
    "Air quality",
    "Alaska",
    // ... more subjects
  ],
  
  // Content history (from /summaries)
  "summaries": [
    {
      "version_code": "00",
      "action_date": ISODate("2025-01-07"),
      "action_desc": "Introduced in House",
      "text_html": "<p>This bill reduces taxes, reduces or increases spending for various federal programs, increases the statutory debt limit. Title I contains agricultural conservation provisions affecting Department of Agriculture programs. Title II addresses defense appropriations and military modernization...</p>",
      "text_plain": "This bill reduces taxes, reduces or increases spending for various federal programs, increases the statutory debt limit. Title I contains agricultural conservation provisions...",
      "updated_at": ISODate("2025-01-10T15:30:00Z"),
      "char_count": 15432
    },
    {
      "version_code": "53",
      "action_date": ISODate("2025-02-15"),
      "action_desc": "Passed House",
      "text_html": "<p>Expanded summary after House amendments...</p>",
      "text_plain": "Expanded summary after House amendments...",
      "updated_at": ISODate("2025-02-16T10:00:00Z"),
      "char_count": 28956
    },
    {
      "version_code": "55",
      "action_date": ISODate("2025-03-20"),
      "action_desc": "Passed Senate",
      "text_html": "<p>Further expanded summary after Senate passage...</p>",
      "text_plain": "Further expanded summary after Senate passage...",
      "updated_at": ISODate("2025-03-21T14:15:00Z"),
      "char_count": 45123
    }
  ],
  
  // Metadata
  "latest_version": "55",
  "created_at": ISODate("2025-01-07"),
  "updated_at": ISODate("2025-03-21T14:15:00Z"),
  "ttl_expires_at": ISODate("2025-01-11T00:00:00Z")  // 1 hour from last fetch
}
```

---

## Real-World Search Queries

### Query 1: Find all bills with specific subject
```javascript
db.bills.find({
  "legislative_subjects": "Agricultural conservation and pollution"
})
```

### Query 2: Full-text search in summaries
```javascript
db.bills.find({
  $text: { $search: "Department of Agriculture funding allocation" }
})
```

### Query 3: Policy area + subject combination
```javascript
db.bills.find({
  "policy_area": "Defense",
  "legislative_subjects": "Military readiness"
})
```

### Query 4: Get all versions of a bill
```javascript
db.bills.findOne(
  { "bill_id": "hr1-119" },
  { "summaries": 1 }
)
// Returns array of all summary versions
```

### Query 5: Find latest summary version
```javascript
db.bills.aggregate([
  { $match: { "bill_id": "hr1-119" } },
  { $unwind: "$summaries" },
  { $sort: { "summaries.updated_at": -1 } },
  { $limit: 1 },
  { $replaceRoot: { newRoot: "$summaries" } }
])
```

---

## Performance Notes

### Text Content Volume
- HR1 (budget bill): 15k-65k characters per version
- Most bills: 5k-30k characters
- Average bill has 3-5 version snapshots = 25k-150k characters total
- Storage efficient in MongoDB (compression applied)

### Subject Lists
- Complex bills: 200+ subjects
- Simple bills: 10-50 subjects
- Average: 60-80 subjects per bill
- Flat structure (no hierarchy) makes indexing simple

### Query Performance
- Subject array query (indexed): < 10ms
- Full-text search: 50-200ms depending on result set size
- Combined query (policy_area + subject): < 50ms

---

## API Call Optimization

### Efficient Workflow (per bill)
```
1. GET /bill/119/hr/1                    [2 KB response]
2. GET /bill/119/hr/1/summaries          [50 KB response, up to 5 versions]
3. GET /bill/119/hr/1/subjects           [15 KB response, up to 238 subjects]
───────────────────────────────────────────────────────
Total: ~3 API calls, ~65 KB data per bill

With 5,000 req/hour limit:
Can fetch ~1,666 bills per hour (3 calls each)
= ~500 bills per hour if respecting rate limits
= All 10,000 bills in Congress in ~20 hours
```

### Caching Benefits
- Re-fetching without cache: 65 KB per bill
- With 1-hour cache: 65 KB for first access, 0 KB for cached access
- Typical user session: 5-10 bills viewed = 325-650 KB with cache
  vs. 325-650 KB without cache (same but prevents re-fetching)

---

## Version Code Reference

| Code | Legislative Stage | Summary Completeness |
|------|------------------|----------------------|
| 00 | Introduced | Basic overview |
| 07 | Reported to House Committee | Committee analysis added |
| 53 | Passed House | Amendments documented |
| 54 | Engrossed in House | Final House version |
| 55 | Passed Senate | Senate amendments documented |
| 56 | Engrossed in Senate | Final Senate version |
| 49 | Becomes Public Law | Final law version |

---

## Reference Implementation Pattern

```python
class BillDataService:
    """Service to fetch and combine bill data from Congress API"""
    
    async def fetch_complete_bill_data(self, congress: int, bill_type: str, number: int):
        """Fetch all bill data from three endpoints"""
        
        bill_id = f"{bill_type}{number}-{congress}"
        
        # Fetch from three endpoints
        bill_info = await self.congress_client.get_bill(congress, bill_type, number)
        summaries = await self.congress_client.get_summaries(congress, bill_type, number)
        subjects = await self.congress_client.get_subjects(congress, bill_type, number)
        
        # Combine into single document
        document = {
            "bill_id": bill_id,
            "congress": congress,
            "type": bill_type,
            "number": number,
            "title": bill_info["title"],
            "policy_area": subjects["policyArea"]["name"],
            "legislative_subjects": [
                s["name"] for s in subjects["legislativeSubjects"]
            ],
            "summaries": [
                {
                    "version_code": s["versionCode"],
                    "action_date": s["actionDate"],
                    "action_desc": s["actionDesc"],
                    "text_html": s["text"],
                    "text_plain": self.strip_html(s["text"]),
                    "updated_at": s["updateDate"],
                }
                for s in summaries
            ],
            "latest_version": max(s["versionCode"] for s in summaries),
            "created_at": bill_info["introducedDate"],
            "updated_at": datetime.utcnow(),
        }
        
        # Store in MongoDB with 1-hour TTL
        await self.db.bills.insert_one(document)
        
        return document
```

