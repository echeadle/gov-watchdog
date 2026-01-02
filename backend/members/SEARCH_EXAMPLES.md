# Member Search Enhancement - Usage Examples

## Overview

The enhanced member search functionality provides flexible, intelligent name searching with support for:
- Single name searches (first or last name)
- Full name searches in any order
- Partial name matching
- Case-insensitive matching
- Combination with other filters (state, party, chamber)

## Search Examples

### 1. Single Name Search

**Search by First Name:**
```python
from members.models import MemberSearchParams
from members.services import MemberService

# Find all members named "Mike"
params = MemberSearchParams(q="Mike")
results = await MemberService.search_members(params)

# Returns: Mike Lee, Mike Johnson, Mike Braun, etc.
```

**Search by Last Name:**
```python
# Find all members with last name "Smith"
params = MemberSearchParams(q="Smith")
results = await MemberService.search_members(params)

# Returns: Adam Smith, Tina Smith, Jason Smith, etc.
```

### 2. Full Name Search (Any Order)

```python
# Both of these work identically:
params1 = MemberSearchParams(q="Nancy Pelosi")
params2 = MemberSearchParams(q="Pelosi Nancy")

results1 = await MemberService.search_members(params1)
results2 = await MemberService.search_members(params2)

# Both return: Nancy Pelosi
```

### 3. Partial Name Matching

```python
# Find names starting with "Mic"
params = MemberSearchParams(q="Mic")
results = await MemberService.search_members(params)

# Returns: Michael Bennett, Michelle Steel, Mick Mulvaney, etc.
# Note: Uses word boundaries, so "Dominic" would NOT match
```

### 4. Case-Insensitive Search

```python
# All of these return the same results:
params1 = MemberSearchParams(q="mike")
params2 = MemberSearchParams(q="MIKE")
params3 = MemberSearchParams(q="Mike")

# All return: Mike Lee, Mike Johnson, etc.
```

### 5. Multiple Name Parts

```python
# Handle names with multiple parts
params = MemberSearchParams(q="Martin Luther King")
results = await MemberService.search_members(params)

# Searches:
# 1. Full name: "Martin Luther King"
# 2. First="Martin", Last="King"
# 3. First="King", Last="Martin" (reversed)
```

### 6. Combined with Filters

**State Filter:**
```python
# Find all Smiths in California
params = MemberSearchParams(q="Smith", state="CA")
results = await MemberService.search_members(params)
```

**Party Filter:**
```python
# Find all Republican Mikes
params = MemberSearchParams(q="Mike", party="R")
results = await MemberService.search_members(params)
```

**Chamber Filter:**
```python
# Find all Senators named Lee
params = MemberSearchParams(q="Lee", chamber="senate")
results = await MemberService.search_members(params)
```

**Multiple Filters:**
```python
# Find Democratic Senators in New York
params = MemberSearchParams(
    q="Schumer",
    state="NY",
    party="D",
    chamber="senate"
)
results = await MemberService.search_members(params)
```

### 7. Pagination

```python
# Get second page of results
params = MemberSearchParams(
    q="Smith",
    page=2,
    page_size=10
)
results = await MemberService.search_members(params)

print(f"Total results: {results.total}")
print(f"Current page: {results.page}")
print(f"Total pages: {results.total_pages}")
```

## API Endpoint Usage

### GET /api/members/

**Example 1: Search by first name**
```bash
curl "http://localhost:8000/api/members/?q=Mike"
```

**Example 2: Search by full name**
```bash
curl "http://localhost:8000/api/members/?q=Nancy+Pelosi"
```

**Example 3: Search with filters**
```bash
curl "http://localhost:8000/api/members/?q=Smith&state=CA&party=D"
```

**Example 4: Partial search**
```bash
curl "http://localhost:8000/api/members/?q=Mic"
```

## How It Works

### Query Parsing

The search query is parsed to detect the number of words:

1. **Single Word** (e.g., "Mike"):
   - Searches: `first_name`, `last_name`, `name` fields
   - Uses word boundary (`\b`) for partial matching

2. **Two Words** (e.g., "Mike Lee"):
   - Tries `first_name="Mike" AND last_name="Lee"`
   - Tries `first_name="Lee" AND last_name="Mike"` (reversed)
   - Tries full `name` field with both orders

3. **Three+ Words** (e.g., "Martin Luther King"):
   - Searches full `name` field for all words in sequence
   - Tries first word + last word as first/last name
   - Tries reverse combination

### MongoDB Query Examples

**Single word "Mike":**
```javascript
{
  "$or": [
    { "first_name": { "$regex": "\\bMike", "$options": "i" } },
    { "last_name": { "$regex": "\\bMike", "$options": "i" } },
    { "name": { "$regex": "\\bMike", "$options": "i" } }
  ]
}
```

**Two words "Mike Lee":**
```javascript
{
  "$or": [
    {
      "$and": [
        { "first_name": { "$regex": "\\bMike", "$options": "i" } },
        { "last_name": { "$regex": "\\bLee", "$options": "i" } }
      ]
    },
    {
      "$and": [
        { "first_name": { "$regex": "\\bLee", "$options": "i" } },
        { "last_name": { "$regex": "\\bMike", "$options": "i" } }
      ]
    },
    {
      "name": {
        "$regex": "\\bMike.*\\bLee|\\bLee.*\\bMike",
        "$options": "i"
      }
    }
  ]
}
```

## Performance Considerations

### Regex Performance
- Uses word boundaries (`\b`) for efficient partial matching
- Case-insensitive matching via `$options: "i"`
- Patterns are optimized to avoid unnecessary backtracking

### Recommended Indexes
For optimal performance, ensure these indexes exist:
```javascript
// Single field indexes for filters
db.members.createIndex({ "state": 1 })
db.members.createIndex({ "party": 1 })
db.members.createIndex({ "chamber": 1 })

// Compound index for common query patterns
db.members.createIndex({ "last_name": 1, "first_name": 1 })

// Text index for more complex searches (optional)
db.members.createIndex({
  "name": "text",
  "first_name": "text",
  "last_name": "text"
})
```

### Query Optimization Tips
1. Combine filters when possible (state + party + chamber)
2. Use pagination to limit result sets
3. Consider caching frequently searched names
4. Monitor slow queries and add indexes as needed

## Edge Cases Handled

### Special Characters in Names
- **Apostrophes**: O'Brien, D'Angelo
- **Hyphens**: Smith-Jones, Lee-Park
- **Periods**: John D. Smith, Dr. Smith
- **Parentheses**: Smith (Jr.), Brown (Sr.)
- **Accents**: José, María (if in database)

### Whitespace
- Multiple spaces are normalized
- Leading/trailing whitespace is trimmed
- Tab and newline characters are handled

### Empty Queries
- Empty strings return all members (with pagination)
- Whitespace-only strings are treated as empty

## Testing

Run the unit tests:
```bash
cd backend
python -m pytest members/test_search.py -v
```

Test specific scenarios:
```bash
# Test single word search
python -m pytest members/test_search.py::TestBuildNameSearchQuery::test_single_word_search -v

# Test two word search
python -m pytest members/test_search.py::TestBuildNameSearchQuery::test_two_word_search_forward_order -v

# Test special character handling
python -m pytest members/test_search.py::TestEscapeRegexSpecialChars -v
```

## Migration Notes

### Backward Compatibility
The enhanced search is fully backward compatible with existing API calls:
- All existing queries will continue to work
- Results may differ slightly due to improved matching logic
- No database schema changes required

### API Contract
- Request format: unchanged
- Response format: unchanged
- Pagination: unchanged
- Error handling: unchanged

## Future Enhancements

Potential improvements for future iterations:

1. **Fuzzy Matching**: Handle typos with Levenshtein distance
2. **Phonetic Matching**: Find "Smith" when searching "Smyth"
3. **Nickname Support**: Find "Mike" when searching "Michael"
4. **Relevance Scoring**: Rank exact matches higher than partial matches
5. **Autocomplete**: Suggest names as user types
6. **Search History**: Track common searches for analytics
7. **MongoDB Atlas Search**: Use full-text search for advanced queries

## Support

For issues or questions:
- Check test cases in `members/test_search.py`
- Review implementation in `members/services.py`
- See MongoDB query examples in this document
