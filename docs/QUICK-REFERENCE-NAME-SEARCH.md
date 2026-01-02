# Quick Reference: Member Name Search

## Python Query Examples

### 1. Exact Name Match (Case-Insensitive)
```python
# Search by last name
members = await db.members.find(
    {"last_name": "pelosi"}  # lowercase input OK
).collation({"locale": "en", "strength": 2}).to_list(length=100)

# Search by first name
members = await db.members.find(
    {"first_name": "NANCY"}  # uppercase input OK
).collation({"locale": "en", "strength": 2}).to_list(length=100)
```

**Important**: Always include `.collation({"locale": "en", "strength": 2})` for case-insensitive searches!

---

### 2. Autocomplete / Prefix Search
```python
# Last name starts with "Mc"
members = await db.members.find(
    {"last_name": {"$regex": "^Mc", "$options": "i"}}
).collation({"locale": "en", "strength": 2}).limit(10).to_list(length=10)

# First name starts with "John"
members = await db.members.find(
    {"first_name": {"$regex": "^John", "$options": "i"}}
).collation({"locale": "en", "strength": 2}).limit(10).to_list(length=10)
```

**Note**: The `^` is required for index to work efficiently!

---

### 3. Full-Text Search (Any Field)
```python
# Search for "Eleanor Holmes" in any name field
members = await db.members.find(
    {"$text": {"$search": "Eleanor Holmes"}}
).to_list(length=100)

# With relevance scoring
members = await db.members.find(
    {"$text": {"$search": "Biden"}},
    {"score": {"$meta": "textScore"}}
).sort([("score", {"$meta": "textScore"})]).to_list(length=100)
```

---

### 4. Combined Filters
```python
# California members with last name starting with "P"
members = await db.members.find({
    "state": "CA",
    "last_name": {"$regex": "^P", "$options": "i"}
}).collation({"locale": "en", "strength": 2}).to_list(length=100)
```

---

### 5. Sorted Alphabetical List
```python
# Get all members sorted by last name, first name
members = await db.members.find().sort([
    ("last_name", 1),
    ("first_name", 1)
]).to_list(length=1000)

# With pagination
members = await db.members.find().sort([
    ("last_name", 1),
    ("first_name", 1)
]).skip(100).limit(50).to_list(length=50)
```

---

## MongoDB Shell Examples

### Exact Match
```javascript
db.members.find({ last_name: "Biden" })
  .collation({ locale: "en", strength: 2 })
```

### Autocomplete
```javascript
db.members.find({ last_name: /^Schum/i })
  .collation({ locale: "en", strength: 2 })
  .limit(10)
```

### Text Search
```javascript
db.members.find({ $text: { $search: "Eleanor Holmes" } })
```

### Verify Index Usage
```javascript
db.members.find({ last_name: "smith" })
  .collation({ locale: "en", strength: 2 })
  .explain("executionStats")
```

---

## Common Mistakes to Avoid

### ❌ DON'T: Forget collation
```python
# This won't find "Biden" if searching for "biden"
db.members.find({"last_name": "biden"})
```

### ✅ DO: Use collation
```python
db.members.find({"last_name": "biden"})
  .collation({"locale": "en", "strength": 2})
```

---

### ❌ DON'T: Use middle-of-string regex
```python
# Cannot use index - very slow!
db.members.find({"last_name": /iden/i})
```

### ✅ DO: Use prefix regex
```python
# Uses index efficiently
db.members.find({"last_name": /^Bid/i})
  .collation({"locale": "en", "strength": 2})
```

---

## Index Reference

| Index Name | Fields | Purpose |
|------------|--------|---------|
| `last_name_1_first_name_1` | `last_name, first_name` | Sorting, compound queries |
| `first_name_case_insensitive` | `first_name` | Case-insensitive first name search |
| `last_name_case_insensitive` | `last_name` | Case-insensitive last name search |
| `member_text_search` | `name, first_name, last_name` | Full-text search |

---

## Performance Tips

1. **Prefix searches** with `^` are fast (uses index)
2. **Middle/end searches** without `^` are slow (collection scan)
3. **Always use collation** for case-insensitive searches
4. **Text search** is flexible but slower than exact/prefix
5. **Combine filters** to use multiple indexes

---

## When to Use Which Index

| Use Case | Index to Use | Example |
|----------|--------------|---------|
| User types "biden" in search box | Text search | `$text: {$search: "biden"}` |
| Autocomplete last name | Case-insensitive last_name | `/^Bid/i` + collation |
| Autocomplete first name | Case-insensitive first_name | `/^Joe/i` + collation |
| Sorted member list | Compound index | `sort({last_name: 1, first_name: 1})` |
| Exact name lookup | Case-insensitive indexes | Both fields + collation |
| "Search everything" box | Text search | `$text: {$search: "..."}` |

---

## Full Example Service Class

See `/home/echeadle/Projects/Jan_01/gov-watchdog/backend/examples/member_search_examples.py` for complete, production-ready examples.
