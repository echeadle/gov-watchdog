"""
Management command to update member contact information from Congress.gov API.

This fetches detailed member data (including phone and address) for all members
in the database by calling the individual member detail endpoint.

Usage:
    python manage.py update_contact_info
    python manage.py update_contact_info --limit 10
"""

import asyncio
import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from config.database import get_collection
from members.clients.congress import get_congress_client

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update contact information for all members from Congress.gov API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of members to update (for testing)",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")

        self.stdout.write("Starting contact info update...")

        # Run the async update
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._update_contact_info(limit))

    async def _update_contact_info(self, limit: int | None):
        """Async method to update contact info."""
        client = get_congress_client()
        collection = await get_collection("members")

        # Get all members (or limited subset)
        query = {}
        cursor = collection.find(query, {"bioguide_id": 1, "name": 1})

        if limit:
            cursor = cursor.limit(limit)

        members = await cursor.to_list(None)
        total = len(members)

        self.stdout.write(f"\nUpdating contact info for {total} members...\n")

        updated = 0
        errors = 0
        skipped = 0

        for idx, member_doc in enumerate(members, 1):
            bioguide_id = member_doc.get("bioguide_id")
            name = member_doc.get("name", "Unknown")

            try:
                self.stdout.write(f"  [{idx}/{total}] {name} ({bioguide_id})...")

                # Fetch detailed member data from API
                data = await client.get_member(bioguide_id)
                member_data = client.transform_member(data)

                # Extract just the contact info
                phone = member_data.get("phone")
                address = member_data.get("address")

                if phone or address:
                    # Update only phone and address fields
                    await collection.update_one(
                        {"bioguide_id": bioguide_id},
                        {
                            "$set": {
                                "phone": phone,
                                "address": address,
                                "updated_at": datetime.utcnow(),
                            }
                        },
                    )
                    updated += 1
                    self.stdout.write(
                        f"    ✓ Updated: phone={phone is not None}, address={address is not None}"
                    )
                else:
                    skipped += 1
                    self.stdout.write("    - No contact info available")

                # Small delay to be nice to the API
                if idx % 10 == 0:
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(f"Error updating {bioguide_id}: {e}")
                errors += 1
                self.stdout.write(self.style.ERROR(f"    ✗ Error: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Update complete! Updated {updated}/{total} members ({skipped} skipped, {errors} errors)"
            )
        )

        await client.close()
