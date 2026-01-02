"""
AI Agent tools for Congress data queries.
"""

from typing import Any

# Tool definitions for Claude API
TOOLS = [
    {
        "name": "search_members",
        "description": "Search for Congress members by name, state, party, or chamber. Use this when the user wants to find a specific member or browse members.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to find members by name",
                },
                "state": {
                    "type": "string",
                    "description": "Two-letter state code to filter by (e.g., 'CA', 'TX')",
                },
                "party": {
                    "type": "string",
                    "description": "Party to filter by: 'D' for Democrat, 'R' for Republican, 'I' for Independent",
                },
                "chamber": {
                    "type": "string",
                    "description": "Chamber to filter by: 'house' or 'senate'",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_member_details",
        "description": "Get detailed information about a specific Congress member. Use this when the user asks about a specific member's profile, contact info, or terms served.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The bioguide ID of the member (e.g., 'P000197' for Nancy Pelosi)",
                },
            },
            "required": ["bioguide_id"],
        },
    },
    {
        "name": "get_member_bills",
        "description": "Get bills sponsored or cosponsored by a Congress member. Use this when the user asks about legislation a member has introduced or supported.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The bioguide ID of the member",
                },
                "bill_type": {
                    "type": "string",
                    "enum": ["sponsored", "cosponsored"],
                    "description": "Whether to get sponsored or cosponsored bills",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of bills to return (default: 10)",
                },
            },
            "required": ["bioguide_id"],
        },
    },
    {
        "name": "get_member_votes",
        "description": "Get voting record for a Congress member. Use this when the user asks about how a member voted on issues.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The bioguide ID of the member",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of votes to return (default: 10)",
                },
            },
            "required": ["bioguide_id"],
        },
    },
]


async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool and return the result."""
    from members.services import MemberService
    from members.models import MemberSearchParams
    from votes.services import VoteService

    if tool_name == "search_members":
        params = MemberSearchParams(
            q=tool_input.get("query"),
            state=tool_input.get("state"),
            party=tool_input.get("party"),
            chamber=tool_input.get("chamber"),
            page=1,
            page_size=10,
        )
        result = await MemberService.search_members(params)
        return {
            "members": result.results,
            "total": result.total,
            "message": f"Found {result.total} members matching your criteria.",
        }

    elif tool_name == "get_member_details":
        bioguide_id = tool_input["bioguide_id"]
        member = await MemberService.get_member(bioguide_id)
        if member:
            return {
                "member": member,
                "message": f"Found member: {member.get('name')}",
            }
        return {
            "error": f"Member {bioguide_id} not found",
            "message": "Could not find a member with that ID.",
        }

    elif tool_name == "get_member_bills":
        bioguide_id = tool_input["bioguide_id"]
        bill_type = tool_input.get("bill_type", "sponsored")
        limit = tool_input.get("limit", 10)

        result = await MemberService.get_member_bills(
            bioguide_id, bill_type=bill_type, limit=limit
        )
        return {
            "bills": result.get("results", []),
            "total": result.get("total", 0),
            "message": f"Found {result.get('total', 0)} {bill_type} bills.",
        }

    elif tool_name == "get_member_votes":
        bioguide_id = tool_input["bioguide_id"]
        limit = tool_input.get("limit", 10)

        result = await VoteService.get_member_votes(bioguide_id, limit=limit)
        return {
            "votes": result.get("results", []),
            "total": result.get("total", 0),
            "message": f"Found {result.get('total', 0)} votes on record.",
        }

    else:
        return {"error": f"Unknown tool: {tool_name}"}
