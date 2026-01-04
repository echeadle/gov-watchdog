# Bill API Investigation - Complete Index

## Investigation Scope

Analyzed Congress.gov API for bill summaries and subjects to support a bill search feature with topic filtering capability.

**Endpoints Analyzed:**
1. `GET /bill/119/hr/1/summaries` - Bill summary content and versions
2. `GET /bill/119/hr/1/subjects` - Bill topics and policy area classification

**Test Bill:** HR1 - 119th Congress (omnibus/complex bill)

---

## Key Findings Summary

### Summaries Endpoint
- **Content Size:** 15,000 to 65,000+ characters per summary
- **Format:** HTML with semantic structure
- **Versions:** Up to 5 distinct versions tracking bill progression
- **Version Codes:** 00 (Introduced), 07 (Committee), 53 (Passed House), 55 (Passed Senate), 49 (Law)
- **Author:** Congressional Research Service (no explicit author field)
- **Update Frequency:** Changes as bill progresses through legislature
- **Use Case:** Full-text search and bill content understanding

### Subjects Endpoint
- **Structure:** Flat (non-hierarchical), no nesting
- **Subject Count:** 238 for HR1 (varies: 10-238 depending on bill scope)
- **Policy Area:** Single top-level categorization
- **Pagination:** 20 per page
- **Format:** Array of subject objects with name and updateDate
- **Subject Examples:** Abortion, Accounting, Agriculture, Technology, Air quality, Geographic references
- **Use Case:** Topic-based bill filtering and classification

---

## Documentation Files Created

### 1. BILL-API-REFERENCE.md ⭐ PRIMARY REFERENCE (Updated 2026-01-04)
**Purpose:** Consolidated comprehensive reference combining all technical documentation
**Contents:**
- Quick reference cards for both endpoints
- Full API response structures and field descriptions
- Version code reference table
- MongoDB schema with indexes
- Query examples (simple to advanced)
- API fetching workflow with Python code
- Search implementation patterns
- Performance optimization guide
- Implementation checklist
- Common gotchas and solutions
- Real-world example (HR1)

**Best For:** All implementation needs - quick lookup, detailed specs, examples, troubleshooting

### 2. bill-search-summary.md
**Purpose:** Strategic implementation guide
**Contents:**
- User search scenarios
- Implementation strategy
- Data storage and indexing patterns
- API fetching workflow
- Caching TTL strategy
- Frontend search implementation examples
- Search UI pattern suggestions

**Best For:** Overall design and architecture discussions

### 5. API-ANALYSIS-SUMMARY.txt
**Purpose:** Executive summary in plain text format
**Contents:**
- High-level findings for both endpoints
- Design implications for bill search
- MongoDB schema overview
- Efficiency analysis
- Key takeaways
- Search scenarios supported

**Best For:** Quick briefing and project stakeholders

### 6. research-notes.md
**Purpose:** Formal research notes archive
**Contents:**
- Investigation date and sources
- Key findings bullet points
- Design implications
- Confidence level assessment
- Comparison to project requirements

**Best For:** Reference and future research auditing

---

## Implementation Roadmap

### Phase 1: Data Structure & Storage
1. Design MongoDB schema for bills with summaries and subjects
2. Create indexes for search operations
3. Implement HTML parsing for summary text

### Phase 2: Backend API Integration
1. Create Congress.gov API client for bill endpoints
2. Implement caching layer (1-hour TTL for summaries)
3. Build bill fetch service combining all 3 endpoints
4. Add full-text search capability to bill queries

### Phase 3: Backend Search Endpoints
1. Create `/api/v1/bills/search?q=...` endpoint
2. Create `/api/v1/bills/subjects/{subject}` filter
3. Create `/api/v1/bills/policy-area/{area}` filter
4. Implement combined search: policy area + subjects + keywords

### Phase 4: Frontend Implementation
1. Create bill search component
2. Implement subject filter dropdown
3. Implement full-text search box
4. Add policy area browsing
5. Display bill versions and evolution timeline

### Phase 5: User Testing & Optimization
1. Test search relevance and performance
2. Optimize indexes based on query patterns
3. Implement caching in frontend (React Query)
4. Gather user feedback on search effectiveness

---

## Critical Implementation Details

### HTML Parsing
Summaries are HTML-formatted. Must:
- Strip tags for plain text storage
- Preserve tags for HTML display option
- Handle nested semantic structure

### Version Code Mapping
Map numeric codes to user-friendly text:
```
00 -> "Introduced"
07 -> "Reported to Committee"
49 -> "Public Law"
53 -> "Passed House"
55 -> "Passed Senate"
```

### Subject Filtering
Legislative subjects are flat array, enable:
- Single subject filter
- Multiple subject filtering (OR logic)
- Wildcard/partial matching for long subject names

### Caching Strategy
Different TTLs because:
- Summaries: 1 hour (updated during active session)
- Subjects: 24 hours (rarely change)
- Policy areas: 7 days (static list)

### API Rate Limiting
With 5,000 req/hour limit:
- ~1,666 bills per hour (3 calls each)
- ~6-7 hours to fetch all 10,000 bills
- Recommend batch operations during off-peak

---

## Sample Code Snippets

### Python: Combined Bill Fetch
```python
async def fetch_complete_bill(congress: int, bill_type: str, number: int):
    bill = await api.get_bill(congress, bill_type, number)
    summaries = await api.get_summaries(congress, bill_type, number)
    subjects = await api.get_subjects(congress, bill_type, number)
    
    return {
        "bill_id": f"{bill_type}{number}-{congress}",
        "title": bill["title"],
        "policy_area": subjects["policyArea"]["name"],
        "legislative_subjects": [s["name"] for s in subjects["legislativeSubjects"]],
        "summaries": [
            {
                "version_code": s["versionCode"],
                "action_desc": s["actionDesc"],
                "text_html": s["text"],
                "text_plain": strip_html(s["text"]),
                "updated_at": s["updateDate"],
            }
            for s in summaries
        ]
    }
```

### MongoDB: Full-Text Search Index
```javascript
db.bills.createIndex({
    "summary_text_plain": "text",
    "title": "text",
    "policy_area": 1
})
```

### MongoDB: Subject Filter Query
```javascript
db.bills.find({
    legislative_subjects: "Agricultural conservation and pollution"
}).limit(20)
```

---

## Risk Assessment

### Low Risk
- API structure is stable and well-documented
- Version codes follow predictable pattern
- Subject taxonomy is consistent

### Medium Risk
- Large number of subjects per bill (238) might need pagination
- HTML parsing might miss edge cases
- Full-text search performance depends on index tuning

### Mitigation
- Implement robust HTML parser (use library like html2text)
- Test full-text search with real bill data
- Create performance benchmark baseline
- Monitor API rate limits and implement backoff

---

## Questions Answered

Q: What fields are available in summaries?
A: actionDate, actionDesc, text (HTML), updateDate, versionCode

Q: How long are summaries?
A: 15,000 to 65,000+ characters depending on bill complexity

Q: Who writes them?
A: Congressional Research Service (CRS), no individual author

Q: What version types exist?
A: 5 common types tracking progression (Introduced to Public Law)

Q: What's the subjects data structure?
A: Flat array of objects with name and updateDate

Q: How many subjects?
A: 238 for HR1, varies 10-238 depending on bill

Q: Are subjects hierarchical?
A: No, flat structure with no nesting

Q: Can we support topic search?
A: Yes, both via subjects array and full-text summaries

Q: How should we search?
A: Array filter for subjects, full-text for keywords, policy area for browsing

---

## References

**API Documentation:** https://api.congress.gov/

**Congress.gov:** https://congress.gov/

**Test Data:** HR1 - 119th Congress
- Complex omnibus bill
- 238 legislative subjects
- Spans multiple policy areas
- Good representative sample

---

## Next Steps

1. Review `BILL-SEARCH-QUICK-REF.md` for implementation details
2. Check `bill-api-examples.md` for MongoDB patterns
3. Reference `congress-api-bill-structure.md` for detailed specs
4. Consult `research-notes.md` for original findings

---

## Document Locations

All files saved to:
`/home/echeadle/Projects/Jan_01/gov-watchdog/.claude/scratchpad/`

**Active Files:**
- `BILL-API-REFERENCE.md` ⭐ - Consolidated technical reference (use this)
- `bill-search-summary.md` - Strategic guide
- `BILL-API-INVESTIGATION.md` - This index

**Archived Files (consolidated into BILL-API-REFERENCE.md):**
- `BILL-SEARCH-QUICK-REF.md` - Quick lookup (archived)
- `congress-api-bill-structure.md` - Full specs (archived)
- `bill-api-examples.md` - Real examples (archived)

**Supporting Files:**
- `API-ANALYSIS-SUMMARY.txt` - Executive summary
- `research-notes.md` - Research archive
- `bill-search-implementation-summary.md` - Implementation notes

