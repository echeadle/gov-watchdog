// MongoDB initialization script
// Creates the gov_watchdog database and sets up indexes

db = db.getSiblingDB('gov_watchdog');

// Create collections
db.createCollection('members');
db.createCollection('bills');
db.createCollection('votes');

// Members indexes
db.members.createIndex({ "bioguide_id": 1 }, { unique: true });
db.members.createIndex({ "state": 1 });
db.members.createIndex({ "party": 1 });
db.members.createIndex({ "chamber": 1 });

// Name search indexes - optimized for flexible searching
// 1. Compound index for sorted queries (last name, first name)
db.members.createIndex({ "last_name": 1, "first_name": 1 });

// 2. Case-insensitive indexes for exact and prefix matching
db.members.createIndex(
  { "first_name": 1 },
  { name: "first_name_case_insensitive", collation: { locale: "en", strength: 2 } }
);
db.members.createIndex(
  { "last_name": 1 },
  { name: "last_name_case_insensitive", collation: { locale: "en", strength: 2 } }
);

// 3. Text index for full-text search (any order, partial matching)
db.members.createIndex(
  { "name": "text", "first_name": "text", "last_name": "text" },
  { name: "member_text_search", default_language: "english" }
);

// Bills indexes
db.bills.createIndex({ "bill_id": 1 }, { unique: true });
db.bills.createIndex({ "sponsor_id": 1 });
db.bills.createIndex({ "congress": 1 });
db.bills.createIndex({ "introduced_date": -1 });
db.bills.createIndex({ "title": "text" }, { name: "bill_text_search" });

// Votes indexes
db.votes.createIndex({ "vote_id": 1 }, { unique: true });
db.votes.createIndex({ "bill_id": 1 });
db.votes.createIndex({ "chamber": 1 });
db.votes.createIndex({ "date": -1 });

print('Gov Watchdog database initialized with collections and indexes');
