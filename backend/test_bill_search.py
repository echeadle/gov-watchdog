#!/usr/bin/env python
"""
Quick test script for bill search functionality.

Run with: python test_bill_search.py
"""

import asyncio
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from bills.services import BillService
from config.database import ensure_indexes


async def test_bill_search():
    """Test the bill search functionality."""
    print("=" * 60)
    print("Testing Bill Search API")
    print("=" * 60)

    # Ensure indexes are created
    print("\n1. Setting up database indexes...")
    await ensure_indexes()
    print("   ✓ Indexes created")

    # Test 1: Search without filters (should trigger sync)
    print("\n2. Testing search without filters (should sync recent bills)...")
    result = await BillService.search_bills(congress=119, page_size=5)
    print(f"   ✓ Found {result['total']} bills")
    print(f"   ✓ Returned {len(result['results'])} results")

    if result["results"]:
        bill = result["results"][0]
        print(f"\n   Sample bill:")
        print(f"   - ID: {bill.get('bill_id')}")
        print(f"   - Title: {bill.get('title', '')[:80]}...")
        print(f"   - Sponsor: {bill.get('sponsor_id')}")
        print(f"   - Subjects: {len(bill.get('legislative_subjects', []))}")
        print(f"   - Summaries: {len(bill.get('summaries', []))}")

        # Show summary text if available
        if bill.get("summaries"):
            summary = bill["summaries"][0]
            print(f"\n   Sample summary:")
            print(f"   - Version: {summary.get('action_desc')}")
            print(f"   - Text (first 200 chars): {summary.get('text_plain', '')[:200]}...")

    # Test 2: Keyword search
    print("\n3. Testing keyword search (q=tax)...")
    result = await BillService.search_bills(query="tax", congress=119, page_size=5)
    print(f"   ✓ Found {result['total']} bills matching 'tax'")
    if result["results"]:
        print(f"   ✓ Sample: {result['results'][0].get('title', '')[:80]}...")

    # Test 3: Party filter
    print("\n4. Testing party filter (party=D)...")
    result = await BillService.search_bills(party="D", congress=119, page_size=5)
    print(f"   ✓ Found {result['total']} bills sponsored by Democrats")

    # Test 4: Subject filter (if subjects exist)
    print("\n5. Checking for available subjects...")
    result = await BillService.search_bills(congress=119, page_size=20)
    subjects = set()
    for bill in result["results"]:
        subjects.update(bill.get("legislative_subjects", []))

    if subjects:
        sample_subject = list(subjects)[0]
        print(f"   ✓ Found subjects: {len(subjects)} unique subjects")
        print(f"   ✓ Sample subject: {sample_subject}")

        print(f"\n6. Testing subject filter (subject={sample_subject})...")
        result = await BillService.search_bills(
            subject=sample_subject, congress=119, page_size=5
        )
        print(f"   ✓ Found {result['total']} bills with subject '{sample_subject}'")

    # Test 5: Combined search
    print("\n7. Testing combined search (q=climate, party=D, congress=119)...")
    result = await BillService.search_bills(
        query="climate", party="D", congress=119, page_size=5
    )
    print(f"   ✓ Found {result['total']} bills")
    if result["results"]:
        print(f"   ✓ Sample: {result['results'][0].get('title', '')[:80]}...")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_bill_search())
