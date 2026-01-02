"""
Management command to sync Congress members from Congress.gov API.

Usage:
    python manage.py sync_members
    python manage.py sync_members --chamber house
    python manage.py sync_members --chamber senate
"""

import asyncio
import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from config.database import ensure_indexes, get_collection
from members.clients.congress import get_congress_client

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync current Congress members from Congress.gov API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--chamber",
            type=str,
            choices=["house", "senate"],
            help="Only sync specific chamber (default: both)",
        )
        parser.add_argument(
            "--congress",
            type=int,
            default=119,
            help="Congress number (default: 119 for 2025-2027)",
        )

    def handle(self, *args, **options):
        chamber = options.get("chamber")
        congress = options.get("congress", 119)

        self.stdout.write(f"Starting member sync for Congress {congress}...")

        # Run the async sync
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._sync_members(chamber, congress))

    async def _sync_members(self, chamber: str | None, congress: int):
        """Async method to sync members."""
        # Ensure database indexes exist
        await ensure_indexes()

        client = get_congress_client()
        collection = await get_collection("members")

        synced = 0
        errors = 0
        offset = 0
        limit = 250  # Max allowed by API

        chamber_filter = chamber.lower() if chamber else None

        self.stdout.write(f"\nFetching members from Congress {congress}...")

        while True:
            try:
                self.stdout.write(f"  Fetching members (offset {offset})...")
                data = await client.get_current_members(
                    congress=congress, limit=limit, offset=offset
                )

                members = data.get("members", [])
                if not members:
                    break

                for member_data in members:
                    try:
                        # Transform to our schema
                        member = client.transform_member(member_data)

                        # Filter by chamber if specified
                        if chamber_filter and member.get("chamber") != chamber_filter:
                            continue

                        member["updated_at"] = datetime.utcnow()

                        # Upsert into database
                        await collection.update_one(
                            {"bioguide_id": member["bioguide_id"]},
                            {"$set": member},
                            upsert=True,
                        )
                        synced += 1

                    except Exception as e:
                        logger.error(
                            f"Error processing member {member_data.get('bioguideId', 'unknown')}: {e}"
                        )
                        errors += 1

                # Check if we got all results
                pagination = data.get("pagination", {})
                total = pagination.get("count", 0)

                self.stdout.write(
                    f"    Processed {min(offset + limit, total)} / {total} members"
                )

                if offset + limit >= total:
                    break

                offset += limit

                # Small delay to be nice to the API
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error fetching members at offset {offset}: {e}")
                errors += 1
                break

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSync complete! Synced {synced} members with {errors} errors."
            )
        )

        await client.close()
