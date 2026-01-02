---
name: member-comparison
description: Compares Congress members side-by-side. Use when analyzing voting alignment, policy positions, or comparing two or more representatives.
allowed-tools: Read, Grep, Glob
---

# Member Comparison Skill

## Purpose
This skill provides tools for comparing Congress members across multiple dimensions: voting records, sponsored legislation, policy positions, and biographical data.

## Comparison Dimensions

### 1. Voting Alignment
```python
async def compare_voting_records(
    member1_id: str,
    member2_id: str,
    congress: int = 118
) -> dict:
    # Get votes where both members voted
    shared_votes = await db.votes.find({
        "congress": congress,
        f"votes.{member1_id}": {"$exists": True},
        f"votes.{member2_id}": {"$exists": True},
    }).to_list(None)

    same = 0
    different = 0
    details = []

    for vote in shared_votes:
        v1 = vote["votes"].get(member1_id)
        v2 = vote["votes"].get(member2_id)

        if v1 in ["Yea", "Nay"] and v2 in ["Yea", "Nay"]:
            if v1 == v2:
                same += 1
            else:
                different += 1
                details.append({
                    "vote_id": vote["vote_id"],
                    "question": vote["question"],
                    "date": vote["date"],
                    "member1_vote": v1,
                    "member2_vote": v2,
                })

    total = same + different
    return {
        "alignment_score": same / total if total > 0 else 0,
        "same_votes": same,
        "different_votes": different,
        "total_shared_votes": total,
        "key_disagreements": details[:10],
    }
```

### 2. Legislative Focus
```python
async def compare_legislative_focus(
    member1_id: str,
    member2_id: str
) -> dict:
    # Get policy areas for each member's bills
    async def get_policy_areas(member_id):
        bills = await db.bills.find({"sponsor_id": member_id}).to_list(None)
        areas = {}
        for bill in bills:
            area = bill.get("policy_area", "Other")
            areas[area] = areas.get(area, 0) + 1
        return areas

    areas1 = await get_policy_areas(member1_id)
    areas2 = await get_policy_areas(member2_id)

    all_areas = set(areas1.keys()) | set(areas2.keys())

    return {
        "member1_focus": areas1,
        "member2_focus": areas2,
        "shared_areas": list(set(areas1.keys()) & set(areas2.keys())),
        "unique_to_member1": list(set(areas1.keys()) - set(areas2.keys())),
        "unique_to_member2": list(set(areas2.keys()) - set(areas1.keys())),
    }
```

### 3. Party Loyalty Comparison
```python
async def compare_party_loyalty(
    member1_id: str,
    member2_id: str,
    congress: int = 118
) -> dict:
    loyalty1 = await calculate_party_loyalty(member1_id, congress)
    loyalty2 = await calculate_party_loyalty(member2_id, congress)

    return {
        "member1_loyalty": loyalty1,
        "member2_loyalty": loyalty2,
        "difference": abs(loyalty1 - loyalty2),
        "more_loyal": member1_id if loyalty1 > loyalty2 else member2_id,
    }
```

### 4. Cosponsorship Network
```python
async def compare_cosponsorship(
    member1_id: str,
    member2_id: str
) -> dict:
    # Bills where member1 is sponsor and member2 is cosponsor
    m1_sponsored_m2_cosponsor = await db.bills.count_documents({
        "sponsor_id": member1_id,
        "cosponsors": member2_id,
    })

    # Bills where member2 is sponsor and member1 is cosponsor
    m2_sponsored_m1_cosponsor = await db.bills.count_documents({
        "sponsor_id": member2_id,
        "cosponsors": member1_id,
    })

    return {
        "mutual_cosponsorship": m1_sponsored_m2_cosponsor + m2_sponsored_m1_cosponsor,
        "member1_cosponsored_member2": m1_sponsored_m2_cosponsor,
        "member2_cosponsored_member1": m2_sponsored_m1_cosponsor,
    }
```

## API Endpoint

### GET /api/v1/members/compare
```python
@api_view(['GET'])
async def compare_members(request):
    member1_id = request.query_params.get('member1')
    member2_id = request.query_params.get('member2')
    congress = int(request.query_params.get('congress', 118))

    member1 = await get_member(member1_id)
    member2 = await get_member(member2_id)

    comparison = {
        "members": [format_member(member1), format_member(member2)],
        "voting": await compare_voting_records(member1_id, member2_id, congress),
        "legislation": await compare_legislative_focus(member1_id, member2_id),
        "party_loyalty": await compare_party_loyalty(member1_id, member2_id, congress),
        "cosponsorship": await compare_cosponsorship(member1_id, member2_id),
    }

    return Response(comparison)
```

## Response Format
```json
{
  "members": [
    {"bioguide_id": "A000001", "name": "...", "party": "D", "state": "CA"},
    {"bioguide_id": "B000002", "name": "...", "party": "R", "state": "TX"}
  ],
  "voting": {
    "alignment_score": 0.35,
    "same_votes": 120,
    "different_votes": 223,
    "key_disagreements": [...]
  },
  "legislation": {
    "shared_areas": ["Healthcare", "Education"],
    "member1_focus": {"Healthcare": 15, "Environment": 8},
    "member2_focus": {"Defense": 12, "Economy": 10}
  },
  "party_loyalty": {
    "member1_loyalty": 0.92,
    "member2_loyalty": 0.88
  },
  "cosponsorship": {
    "mutual_cosponsorship": 3
  }
}
```

## Frontend Component
```typescript
interface ComparisonProps {
  member1Id: string;
  member2Id: string;
}

const MemberComparison = ({ member1Id, member2Id }: ComparisonProps) => {
  const { data, isLoading } = useQuery({
    queryKey: ['comparison', member1Id, member2Id],
    queryFn: () => memberService.compare(member1Id, member2Id),
  });

  return (
    <div className="grid grid-cols-3 gap-4">
      <MemberCard member={data?.members[0]} />
      <ComparisonMetrics data={data} />
      <MemberCard member={data?.members[1]} />
    </div>
  );
};
```
