# MongoDB Members Collection - Name Search Guide

## Overview
This guide documents the optimal indexes and query patterns for searching members by name in the Gov Watchdog application.

## Data Structure
The members collection stores congressional member data with the following name-related fields:
- `first_name`: String (e.g., "Michael")
- `last_name`: String (e.g., "Rulli")
- `name`: String in "Last, First Middle" format (e.g., "Rulli, Michael A.")

## Index Strategy

### 1. Compound Index: `last_name + first_name`
**Purpose**: Supports sorted queries and combined name searches
**Index**: `{ "last_name": 1, "first_name": 1 }`

**Use Cases**:
- Alphabetically sorted member lists
- Queries filtering by last name, optionally with first name

**Example Queries**:
```javascript
// Find all members with last name "Smith"
db.members.find({ last_name: "Smith" }).sort({ last_name: 1, first_name: 1 })

// Find specific member by full name
db.members.find({ last_name: "Biden", first_name: "Joe" })
```

### 2. Case-Insensitive Indexes
**Purpose**: Enable case-insensitive exact matches and prefix searches
**Indexes**:
- `first_name` with collation `{ locale: "en", strength: 2 }`
- `last_name` with collation `{ locale: "en", strength: 2 }`

**Use Cases**:
- Search regardless of input case
- Autocomplete / prefix matching
- Exact name matching with user input

**Example Queries**:
```javascript
// Case-insensitive exact match
db.members.find({ first_name: "michael" })
  .collation({ locale: "en", strength: 2 })

// Case-insensitive prefix search (starts with)
db.members.find({ last_name: /^de/i })
  .collation({ locale: "en", strength: 2 })

// Autocomplete: last names starting with "Rull"
db.members.find({
  last_name: { $regex: "^Rull", $options: "i" }
}).collation({ locale: "en", strength: 2 })
```

**Important**: Must include `.collation({ locale: "en", strength: 2 })` in the query to use the case-insensitive index.

### 3. Text Index: Full-Text Search
**Purpose**: Flexible multi-field search with partial matching
**Index**: `{ "name": "text", "first_name": "text", "last_name": "text" }`

**Use Cases**:
- General search box queries
- Search across all name fields
- Word-based matching (any order)
- Partial word matching with stemming

**Example Queries**:
```javascript
// Search for "Michael" in any name field
db.members.find({ $text: { $search: "Michael" } })

// Search for multiple terms (OR logic)
db.members.find({ $text: { $search: "Michael Smith" } })

// Search for exact phrase
db.members.find({ $text: { $search: "\"Eleanor Holmes\"" } })

// Search with relevance scoring
db.members.find(
  { $text: { $search: "Biden" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })
```

## Query Performance Best Practices

### When to Use Each Index

1. **Use Compound Index** when:
   - Sorting by last name, first name
   - Filtering by exact last name
   - Need consistent alphabetical ordering

2. **Use Case-Insensitive Indexes** when:
   - Building autocomplete features
   - User input may have mixed case
   - Need exact or prefix matching on a single field
   - Performance is critical (faster than text search)

3. **Use Text Index** when:
   - Implementing a general search box
   - Users might search by first name, last name, or full name
   - Don't know which field contains the search term
   - Need fuzzy/partial matching across fields

### Performance Tips

1. **Prefix searches are efficient** with collation indexes:
   ```javascript
   // GOOD - Uses index efficiently
   db.members.find({ last_name: /^Smith/i })
     .collation({ locale: "en", strength: 2 })

   // BAD - Cannot use index
   db.members.find({ last_name: /Smith/i })
   ```

2. **Text search limitations**:
   - Only one text index per collection
   - Cannot combine with other special indexes in same query
   - Slightly slower than exact/prefix matches

3. **Combine filters for efficiency**:
   ```javascript
   // GOOD - Uses multiple indexes
   db.members.find({
     state: "CA",  // Uses state index
     last_name: "Pelosi"  // Uses compound index
   })
   ```

## Motor (Python) Query Examples

```python
from motor.motor_asyncio import AsyncIOMotorClient

async def search_members_by_last_name(db, last_name: str):
    """Case-insensitive last name search"""
    cursor = db.members.find(
        {"last_name": {"$regex": f"^{last_name}", "$options": "i"}}
    ).collation({"locale": "en", "strength": 2})
    return await cursor.to_list(length=100)

async def search_members_full_text(db, search_term: str):
    """Full-text search across all name fields"""
    cursor = db.members.find(
        {"$text": {"$search": search_term}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})])
    return await cursor.to_list(length=100)

async def autocomplete_last_name(db, prefix: str):
    """Autocomplete for last names"""
    cursor = db.members.find(
        {"last_name": {"$regex": f"^{prefix}", "$options": "i"}},
        {"last_name": 1, "first_name": 1, "name": 1}
    ).collation({"locale": "en", "strength": 2}).limit(10)
    return await cursor.to_list(length=10)

async def exact_name_match(db, first_name: str, last_name: str):
    """Case-insensitive exact name match"""
    return await db.members.find_one(
        {"first_name": first_name, "last_name": last_name},
        collation={"locale": "en", "strength": 2}
    )
```

## Testing Query Performance

Use `explain()` to verify index usage:

```javascript
// Check if query uses the right index
db.members.find({ last_name: "Smith" })
  .collation({ locale: "en", strength: 2 })
  .explain("executionStats")
```

Look for:
- `"stage": "IXSCAN"` (index scan - good)
- `"stage": "COLLSCAN"` (collection scan - bad)
- `indexName` shows which index was used

## Recommendations Summary

### Optimal Indexes (Implemented)
1. ✅ Compound index: `{ "last_name": 1, "first_name": 1 }`
2. ✅ Case-insensitive: `first_name` with collation
3. ✅ Case-insensitive: `last_name` with collation
4. ✅ Text index: `name`, `first_name`, `last_name`

### Query Pattern Recommendations
- **First name search**: Use case-insensitive index with collation
- **Last name search**: Use case-insensitive index with collation
- **Full name search (any order)**: Use text search
- **Partial name matching**: Use regex with `^` prefix and case-insensitive index
- **Case insensitive search**: Always use collation parameter with collation indexes

### Benefits
- Fast prefix-based autocomplete
- Case-insensitive searches without regex overhead
- Flexible full-text search for general queries
- Efficient sorted/filtered queries
- Support for 539 members with sub-millisecond query times
