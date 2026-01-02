"""
Member Search Examples - Quick Reference Guide

This file demonstrates various search patterns and their expected behavior.
Use these examples as a reference when testing or extending search functionality.
"""

from members.models import MemberSearchParams
from members.services import MemberService


# ==============================================================================
# BASIC SEARCH PATTERNS
# ==============================================================================


async def example_single_word_searches():
    """
    Single word searches match against first_name, last_name, or full name.
    """
    # Search by first name
    results = await MemberService.search_members(MemberSearchParams(q="Mike"))
    # Expected: Mike Lee, Mike Johnson, Mike Braun, etc.

    # Search by last name
    results = await MemberService.search_members(MemberSearchParams(q="Smith"))
    # Expected: Adam Smith, Tina Smith, Jason Smith, etc.

    # Search by nickname or common name
    results = await MemberService.search_members(MemberSearchParams(q="Bob"))
    # Expected: Bob Menendez, Bob Casey, etc.


async def example_full_name_searches():
    """
    Full name searches work in any order: "First Last" or "Last First".
    """
    # Standard order
    results = await MemberService.search_members(
        MemberSearchParams(q="Nancy Pelosi")
    )
    # Expected: Nancy Pelosi

    # Reversed order (same result)
    results = await MemberService.search_members(
        MemberSearchParams(q="Pelosi Nancy")
    )
    # Expected: Nancy Pelosi

    # Another example
    results = await MemberService.search_members(MemberSearchParams(q="Chuck Schumer"))
    # Expected: Chuck Schumer


async def example_partial_matching():
    """
    Partial matches work from the beginning of words (word boundary matching).
    """
    # Partial first name
    results = await MemberService.search_members(MemberSearchParams(q="Mic"))
    # Expected: Michael Bennett, Michelle Steel, Mick Mulvaney
    # NOT: Dominic (because "Mic" doesn't start a word in "Dominic")

    # Partial last name
    results = await MemberService.search_members(MemberSearchParams(q="Smit"))
    # Expected: Adam Smith, Jason Smith, etc.

    # Very short partial
    results = await MemberService.search_members(MemberSearchParams(q="Jo"))
    # Expected: John, Joseph, Jordan, etc.


# ==============================================================================
# ADVANCED SEARCH PATTERNS
# ==============================================================================


async def example_complex_names():
    """
    Handles middle names, initials, and hyphenated names.
    """
    # Three-word names
    results = await MemberService.search_members(
        MemberSearchParams(q="Martin Luther King")
    )
    # Tries multiple strategies:
    # 1. Full name: "Martin Luther King"
    # 2. First + Last: "Martin" + "King"
    # 3. First Two + Last: "Martin Luther" + "King"

    # Names with initials
    results = await MemberService.search_members(
        MemberSearchParams(q="John Q. Public")
    )
    # Handles periods correctly (escaped in regex)

    # Hyphenated names
    results = await MemberService.search_members(
        MemberSearchParams(q="Mary-Kate")
    )
    # Preserves hyphen in search

    # Names with apostrophes
    results = await MemberService.search_members(MemberSearchParams(q="O'Brien"))
    # Handles apostrophe correctly


async def example_case_insensitive():
    """
    All searches are case-insensitive.
    """
    # All these return the same results
    results1 = await MemberService.search_members(MemberSearchParams(q="MIKE"))
    results2 = await MemberService.search_members(MemberSearchParams(q="mike"))
    results3 = await MemberService.search_members(MemberSearchParams(q="Mike"))
    results4 = await MemberService.search_members(MemberSearchParams(q="MiKe"))

    # All should be identical
    assert results1 == results2 == results3 == results4


# ==============================================================================
# FILTERING AND COMBINATIONS
# ==============================================================================


async def example_state_filters():
    """
    Combine name search with state filtering.
    """
    # Find all Smiths from California
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", state="CA")
    )

    # Find all Mikes from Texas
    results = await MemberService.search_members(
        MemberSearchParams(q="Mike", state="TX")
    )

    # Find members from New York (no name filter)
    results = await MemberService.search_members(MemberSearchParams(state="NY"))


async def example_party_filters():
    """
    Combine name search with party filtering.
    """
    # Find all Republican Mikes
    results = await MemberService.search_members(
        MemberSearchParams(q="Mike", party="R")
    )

    # Find all Democratic Smiths
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", party="D")
    )

    # Find all Independents (no name filter)
    results = await MemberService.search_members(MemberSearchParams(party="I"))


async def example_chamber_filters():
    """
    Combine name search with chamber filtering.
    """
    # Find all senators named Lee
    results = await MemberService.search_members(
        MemberSearchParams(q="Lee", chamber="senate")
    )

    # Find all House members named Smith
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", chamber="house")
    )


async def example_multiple_filters():
    """
    Combine multiple filters for precise searching.
    """
    # Democratic senators from California
    results = await MemberService.search_members(
        MemberSearchParams(state="CA", party="D", chamber="senate")
    )

    # Republican House members named Smith
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", party="R", chamber="house")
    )

    # Any member named Mike from Texas
    results = await MemberService.search_members(
        MemberSearchParams(q="Mike", state="TX")
    )


# ==============================================================================
# PAGINATION
# ==============================================================================


async def example_pagination():
    """
    Handle large result sets with pagination.
    """
    # First page (default: 20 results)
    page1 = await MemberService.search_members(
        MemberSearchParams(q="Smith", page=1, page_size=20)
    )

    # Second page
    page2 = await MemberService.search_members(
        MemberSearchParams(q="Smith", page=2, page_size=20)
    )

    # Custom page size
    page1_custom = await MemberService.search_members(
        MemberSearchParams(q="Smith", page=1, page_size=10)
    )

    # Check pagination info
    print(f"Total results: {page1.total}")
    print(f"Total pages: {page1.total_pages}")
    print(f"Current page: {page1.page}")
    print(f"Results on this page: {len(page1.results)}")


# ==============================================================================
# EDGE CASES
# ==============================================================================


async def example_edge_cases():
    """
    Edge cases that are handled gracefully.
    """
    # Empty search (returns all members)
    results = await MemberService.search_members(MemberSearchParams(q=""))

    # Whitespace-only search (returns all members)
    results = await MemberService.search_members(MemberSearchParams(q="   "))

    # Extra whitespace in query (normalized)
    results = await MemberService.search_members(
        MemberSearchParams(q="  Mike   Lee  ")
    )
    # Equivalent to "Mike Lee"

    # Special characters in names
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith (Jr.)")
    )
    # Parentheses are escaped properly

    # No results found
    results = await MemberService.search_members(
        MemberSearchParams(q="Zzzzzz12345")
    )
    # Returns empty results list, total=0


# ==============================================================================
# RESPONSE STRUCTURE
# ==============================================================================


async def example_response_structure():
    """
    Understanding the response structure.
    """
    response = await MemberService.search_members(MemberSearchParams(q="Mike"))

    # Response structure:
    # {
    #     "results": [
    #         {
    #             "bioguide_id": "L000577",
    #             "name": "Mike Lee",
    #             "party": "R",
    #             "state": "UT",
    #             "district": null,
    #             "chamber": "senate",
    #             "image_url": "https://..."
    #         },
    #         ...
    #     ],
    #     "total": 5,
    #     "page": 1,
    #     "page_size": 20,
    #     "total_pages": 1
    # }

    # Access individual results
    for member in response.results:
        print(f"{member['name']} ({member['party']}-{member['state']})")

    # Check if there are more pages
    if response.page < response.total_pages:
        print(f"More results available on page {response.page + 1}")


# ==============================================================================
# COMMON USE CASES
# ==============================================================================


async def use_case_autocomplete():
    """
    Implement autocomplete/typeahead functionality.
    """
    # User types "Mic" - show suggestions
    suggestions = await MemberService.search_members(
        MemberSearchParams(q="Mic", page_size=5)
    )
    # Returns: Michael, Michelle, Mick, etc.


async def use_case_member_lookup():
    """
    Find a specific member by name.
    """
    # User searches for "Nancy Pelosi"
    results = await MemberService.search_members(
        MemberSearchParams(q="Nancy Pelosi", page_size=1)
    )

    if results.total > 0:
        member = results.results[0]
        print(f"Found: {member['name']} ({member['bioguide_id']})")
    else:
        print("Member not found")


async def use_case_state_directory():
    """
    Show all members from a specific state.
    """
    # Get all California members
    ca_members = await MemberService.search_members(
        MemberSearchParams(state="CA", page_size=100)
    )

    # Get all Texas senators
    tx_senators = await MemberService.search_members(
        MemberSearchParams(state="TX", chamber="senate")
    )


async def use_case_party_roster():
    """
    Show all members of a specific party.
    """
    # Get all Republican House members
    gop_house = await MemberService.search_members(
        MemberSearchParams(party="R", chamber="house", page_size=100)
    )

    # Get all Democratic senators
    dem_senate = await MemberService.search_members(
        MemberSearchParams(party="D", chamber="senate", page_size=100)
    )


# ==============================================================================
# PERFORMANCE TIPS
# ==============================================================================


async def performance_tips():
    """
    Tips for optimal search performance.
    """
    # 1. Use specific filters to reduce result set
    # GOOD: Combines name + state filter
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", state="CA")
    )

    # LESS OPTIMAL: Broad search returning many results
    results = await MemberService.search_members(MemberSearchParams(q="a"))

    # 2. Use appropriate page sizes
    # GOOD: Reasonable page size
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", page_size=20)
    )

    # LESS OPTIMAL: Very large page size
    results = await MemberService.search_members(
        MemberSearchParams(q="Smith", page_size=100)
    )

    # 3. Be specific in searches
    # GOOD: Full name or specific term
    results = await MemberService.search_members(MemberSearchParams(q="Mike Lee"))

    # LESS OPTIMAL: Very short partial match
    results = await MemberService.search_members(MemberSearchParams(q="M"))


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


async def print_search_results(params: MemberSearchParams):
    """Helper function to print search results in a readable format."""
    response = await MemberService.search_members(params)

    print(f"\n{'='*80}")
    print(f"Search: {params.q or 'All Members'}")
    if params.state:
        print(f"State: {params.state}")
    if params.party:
        print(f"Party: {params.party}")
    if params.chamber:
        print(f"Chamber: {params.chamber.title()}")
    print(f"{'='*80}")
    print(f"Total Results: {response.total}")
    print(f"Page {response.page} of {response.total_pages}\n")

    for i, member in enumerate(response.results, 1):
        district = f" (District {member['district']})" if member.get("district") else ""
        print(
            f"{i:2d}. {member['name']:30s} "
            f"({member['party']}-{member['state']}) "
            f"{member['chamber'].title()}{district}"
        )

    print(f"\n{'='*80}\n")


# ==============================================================================
# EXAMPLE USAGE
# ==============================================================================


async def main():
    """
    Example usage - uncomment to test.
    """
    # Basic searches
    # await print_search_results(MemberSearchParams(q="Mike"))
    # await print_search_results(MemberSearchParams(q="Smith"))

    # Full name searches
    # await print_search_results(MemberSearchParams(q="Nancy Pelosi"))
    # await print_search_results(MemberSearchParams(q="Pelosi Nancy"))

    # Partial matches
    # await print_search_results(MemberSearchParams(q="Mic"))

    # With filters
    # await print_search_results(MemberSearchParams(q="Smith", state="CA"))
    # await print_search_results(MemberSearchParams(q="Mike", party="R"))

    # Complex searches
    # await print_search_results(
    #     MemberSearchParams(q="Smith", state="CA", party="D", chamber="house")
    # )

    pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
