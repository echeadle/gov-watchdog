# Member Search Functionality - Quick Reference

## Overview

The member search feature provides flexible, intelligent name searching with support for various search patterns, partial matching, and advanced filtering.

## Quick Examples

### Basic Searches

```python
# Search by first name
search_members(q="Mike")
→ Returns: Mike Lee, Mike Johnson, Mike Braun

# Search by last name
search_members(q="Smith")
→ Returns: Adam Smith, Tina Smith, Jason Smith

# Full name (any order)
search_members(q="Nancy Pelosi")
search_members(q="Pelosi Nancy")
→ Both return: Nancy Pelosi
```

### Partial Matching

```python
# Partial first name
search_members(q="Mic")
→ Returns: Michael, Michelle, Mick (NOT "Dominic")

# Partial last name
search_members(q="Smit")
→ Returns: Smith, Smithson, etc.
```

### Filtering

```python
# By state
search_members(q="Smith", state="CA")
→ Returns: Only CA Smiths

# By party
search_members(q="Mike", party="R")
→ Returns: Only Republican Mikes

# Combined filters
search_members(q="Smith", state="CA", party="D", chamber="house")
→ Returns: Democratic House members named Smith from CA
```

## Supported Search Patterns

| Pattern | Example | What It Matches |
|---------|---------|-----------------|
| Single word | `"Mike"` | First name, last name, or full name |
| Full name | `"Mike Lee"` | First + last in any order |
| Partial | `"Mic"` | Names starting with "Mic" (word boundary) |
| Multi-word | `"Martin Luther King"` | Complex names with middle names |
| Case-insensitive | `"MIKE"` / `"mike"` | Any case variation |

## Features

- ✅ Single name search (first or last)
- ✅ Full name in any order
- ✅ Partial name matching
- ✅ Case-insensitive
- ✅ Middle names and initials
- ✅ Special characters (apostrophes, hyphens, periods)
- ✅ Combined with state/party/chamber filters
- ✅ Pagination support
- ✅ Fast performance on 1000s of members

## API Endpoints

### Search Members
```
GET /api/v1/members/?q={search_term}
```

**Parameters:**
- `q` - Search query (optional)
- `state` - Two-letter state code (optional)
- `party` - Party code: D, R, I (optional)
- `chamber` - house or senate (optional)
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20, max: 100)

**Example Requests:**
```bash
# Search by name
GET /api/v1/members/?q=Mike

# With filters
GET /api/v1/members/?q=Smith&state=CA&party=D

# Pagination
GET /api/v1/members/?q=Mike&page=2&page_size=10
```

**Response:**
```json
{
  "results": [
    {
      "bioguide_id": "L000577",
      "name": "Mike Lee",
      "party": "R",
      "state": "UT",
      "district": null,
      "chamber": "senate",
      "image_url": "https://..."
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

## Implementation Details

### Architecture

```
_build_name_search_query()  [Main router]
    ├── _normalize_search_term()       [Whitespace handling]
    ├── _escape_regex_special_chars()  [Safety]
    └── Route by word count:
        ├── _build_single_word_query()  [1 word]
        ├── _build_two_word_query()     [2 words]
        └── _build_multi_word_query()   [3+ words]
```

### Search Strategies

**Single Word:** `"Mike"`
- Check `first_name` matches "Mike"
- OR `last_name` matches "Mike"
- OR `name` (full name) matches "Mike"

**Two Words:** `"Mike Lee"`
- Check `first_name="Mike"` AND `last_name="Lee"`
- OR `first_name="Lee"` AND `last_name="Mike"` (reversed)
- OR `name` matches "Mike...Lee" or "Lee...Mike"

**Three+ Words:** `"Martin Luther King"`
- Check `name` matches "Martin...Luther...King" (all words in sequence)
- OR `first_name="Martin"` AND `last_name="King"` (first + last)
- OR `first_name="Martin Luther"` AND `last_name="King"` (first two + last)
- OR other combinations

### Performance

- **Small datasets (<10k):** < 100ms
- **Medium datasets (10k-100k):** 100-500ms
- **Large datasets (>100k):** Consider text indexes

**MongoDB Indexes Recommended:**
```javascript
db.members.createIndex({ last_name: 1, first_name: 1 })
db.members.createIndex({ state: 1, party: 1, chamber: 1 })
```

## Common Use Cases

### Autocomplete/Typeahead
```python
# User types "Mic"
suggestions = search_members(q="Mic", page_size=5)
→ Shows: Michael, Michelle, Mick...
```

### Member Lookup
```python
# Find specific member
results = search_members(q="Nancy Pelosi", page_size=1)
if results.total > 0:
    member = results.results[0]
```

### State Directory
```python
# All California members
ca_members = search_members(state="CA", page_size=100)

# All Texas senators
tx_senators = search_members(state="TX", chamber="senate")
```

### Party Roster
```python
# Republican House members
gop_house = search_members(party="R", chamber="house")

# Democratic senators
dem_senate = search_members(party="D", chamber="senate")
```

## Edge Cases Handled

| Case | Input | Result |
|------|-------|--------|
| Empty search | `""` | Returns all members |
| Extra whitespace | `"  Mike   Lee  "` | Normalized to `"Mike Lee"` |
| Special chars | `"O'Brien"`, `"Smith (Jr.)"` | Properly escaped |
| Hyphenated | `"Mary-Kate"` | Preserved in search |
| No results | `"XYZ123"` | Returns `{"results": [], "total": 0}` |

## Files

- **`services.py`**: Core search implementation
- **`test_search.py`**: Unit tests
- **`search_examples.py`**: Usage examples
- **`SEARCH_IMPROVEMENTS.md`**: Detailed documentation
- **`CHANGELOG_SEARCH.md`**: Change history

## Testing

```bash
# Run tests
python -m pytest backend/members/test_search.py -v

# Run specific test
python -m pytest backend/members/test_search.py::TestBuildNameSearchQuery -v

# With coverage
python -m pytest backend/members/test_search.py --cov=members.services
```

## Future Enhancements

Potential improvements (not yet implemented):

1. **Nickname Support**: Map Mike ↔ Michael, Bob ↔ Robert
2. **Fuzzy Matching**: Handle typos and misspellings
3. **Relevance Scoring**: Rank exact matches higher
4. **Diacritics**: Normalize accented characters
5. **Search Analytics**: Track common queries
6. **Caching**: Cache frequent searches
7. **Text Indexes**: MongoDB full-text search

## Tips for Best Performance

1. **Use specific filters** to reduce result set
   ```python
   # Good: Specific search
   search_members(q="Smith", state="CA")

   # Less optimal: Very broad
   search_members(q="a")
   ```

2. **Use reasonable page sizes**
   ```python
   # Good: Standard pagination
   search_members(q="Smith", page_size=20)

   # Less optimal: Too large
   search_members(q="Smith", page_size=100)
   ```

3. **Be specific in queries**
   ```python
   # Good: Full name or specific term
   search_members(q="Mike Lee")

   # Less optimal: Very short partial
   search_members(q="M")
   ```

## Support

For questions or issues:
- See detailed docs in `SEARCH_IMPROVEMENTS.md`
- Check examples in `search_examples.py`
- Review tests in `test_search.py`
- Ask in team chat or create an issue

---

**Last Updated:** 2026-01-01
**Version:** 2.0
**Backward Compatible:** Yes ✅
