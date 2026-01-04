"""
Management command to sync recent votes from Congress.gov API.

Usage:
    python manage.py sync_votes
    python manage.py sync_votes --chamber house
    python manage.py sync_votes --chamber senate --limit 50
    python manage.py sync_votes --congress 119 --session 1
"""

import asyncio
import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from config.database import ensure_indexes, get_collection
from members.clients.congress import get_congress_client
from votes.xml_parser import SenateVoteXMLParser
from votes.member_matcher import MemberMatcher

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync recent votes from Congress.gov API"

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
        parser.add_argument(
            "--session",
            type=int,
            default=1,
            help="Session number (default: 1)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Number of votes to sync per chamber (default: 100)",
        )

    def handle(self, *args, **options):
        chamber = options.get("chamber")
        congress = options.get("congress", 119)
        session = options.get("session", 1)
        limit = options.get("limit", 100)

        self.stdout.write(
            f"\nStarting vote sync for Congress {congress}, Session {session}..."
        )

        # Run the async sync
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._sync_votes(chamber, congress, session, limit)
        )

    async def _sync_votes(
        self, chamber: str | None, congress: int, session: int, limit: int
    ):
        """Async method to sync votes."""
        # Ensure database indexes exist
        await ensure_indexes()

        client = get_congress_client()
        collection = await get_collection("votes")

        total_synced = 0
        total_errors = 0

        # Determine which chambers to sync
        chambers_to_sync = []
        if chamber:
            chambers_to_sync = [chamber.lower()]
        else:
            chambers_to_sync = ["house", "senate"]

        for chamber_name in chambers_to_sync:
            self.stdout.write(
                f"\n📊 Syncing {chamber_name.title()} votes..."
            )

            synced, errors = await self._sync_chamber_votes(
                client, collection, chamber_name, congress, session, limit
            )

            total_synced += synced
            total_errors += errors

            self.stdout.write(
                f"  ✓ Synced {synced} {chamber_name} votes, {errors} errors"
            )

        await client.close()

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Total: {total_synced} votes synced, {total_errors} errors"
            )
        )

    async def _sync_chamber_votes(
        self,
        client,
        collection,
        chamber: str,
        congress: int,
        session: int,
        limit: int,
    ) -> tuple[int, int]:
        """Sync votes for a specific chamber."""
        synced = 0
        errors = 0
        offset = 0
        page_size = 100  # Fetch 100 at a time

        while synced < limit:
            try:
                # Fetch a batch of votes
                if chamber == "house":
                    data = await client.get_house_votes(
                        congress, session, limit=min(page_size, limit - synced), offset=offset
                    )
                else:
                    data = await client.get_senate_votes(
                        congress, session, limit=min(page_size, limit - synced), offset=offset
                    )

                # Get votes from response (different keys for House vs Senate)
                if chamber == "house":
                    votes = data.get("houseRollCallVotes", [])
                else:
                    votes = data.get("senateRollCallVotes", [])

                if not votes:
                    break

                self.stdout.write(
                    f"  Processing batch: offset={offset}, count={len(votes)}"
                )

                # Process each vote
                for vote_data in votes:
                    try:
                        roll_number = vote_data.get("rollCallNumber")
                        if not roll_number:
                            continue

                        # Get sourceDataURL for Senate votes (XML)
                        source_url = vote_data.get("sourceDataURL")

                        # Fetch detailed vote with member votes
                        detailed_vote = await self._fetch_detailed_vote(
                            client, chamber, congress, session, roll_number, source_url
                        )

                        if not detailed_vote:
                            errors += 1
                            continue

                        # Transform and store
                        await self._store_vote(
                            collection, detailed_vote, chamber, congress, session, roll_number
                        )

                        synced += 1

                        # Progress indicator
                        if synced % 10 == 0:
                            self.stdout.write(f"    ... {synced} votes synced")

                    except Exception as e:
                        logger.error(f"Error syncing vote: {e}")
                        errors += 1

                offset += len(votes)

                # Break if we've synced enough
                if synced >= limit:
                    break

            except Exception as e:
                logger.error(f"Error fetching vote batch: {e}")
                errors += 1
                break

        return synced, errors

    async def _fetch_detailed_vote(
        self, client, chamber: str, congress: int, session: int, roll_number: int,
        source_url: str = None
    ) -> dict | None:
        """Fetch detailed vote information including member votes."""
        try:
            if chamber == "house":
                # House votes: Use JSON API
                vote_data = await client.get_house_vote(congress, session, roll_number)
                vote = vote_data.get("houseRollCallVote", vote_data)

                # Fetch member votes separately
                members_data = await client.get_house_vote_members(congress, session, roll_number)
                members_response = members_data.get("houseRollCallVoteMemberVotes", {})

                # Combine vote metadata with member votes
                member_results = members_response.get("results", [])
                vote["members"] = [
                    {
                        "bioguideId": m["bioguideID"],
                        "vote": m["voteCast"],
                        "party": m["voteParty"],
                        "state": m["voteState"],
                    }
                    for m in member_results
                ]

                return vote

            else:
                # Senate votes: Use XML parser (JSON API not available)
                if not source_url:
                    logger.error(f"No sourceDataURL for Senate vote {roll_number}")
                    return None

                parser = SenateVoteXMLParser()
                xml_data = await parser.fetch_and_parse(source_url)

                if not xml_data:
                    return None

                # Match Senate members to bioguide IDs
                matcher = MemberMatcher()
                matched_members = []

                for member in xml_data.get("members", []):
                    bioguide_id = await matcher.match_senate_member(member)

                    if bioguide_id:
                        matched_members.append({
                            "bioguideId": bioguide_id,
                            "vote": member.get("vote_cast", ""),
                            "party": member.get("party", ""),
                            "state": member.get("state", ""),
                        })
                    else:
                        logger.warning(
                            f"Could not match senator: {member.get('first_name')} "
                            f"{member.get('last_name')} ({member.get('state')})"
                        )

                # Transform XML data to match our vote schema
                vote = {
                    "startDate": xml_data.get("vote_date"),
                    "voteQuestion": xml_data.get("vote_question"),
                    "result": xml_data.get("vote_result"),
                    "members": matched_members,
                }

                # Add totals
                totals = xml_data.get("totals", {})
                vote["votePartyTotal"] = [
                    {
                        "yeaTotal": totals.get("yea", 0),
                        "nayTotal": totals.get("nay", 0),
                        "presentTotal": totals.get("present", 0),
                        "notVotingTotal": totals.get("absent", 0),
                    }
                ]

                return vote

        except Exception as e:
            logger.error(
                f"Error fetching detailed {chamber} vote {roll_number}: {e}"
            )
            return None

    async def _store_vote(
        self,
        collection,
        vote_data: dict,
        chamber: str,
        congress: int,
        session: int,
        roll_number: int,
    ):
        """Transform and store vote in MongoDB."""
        vote_id = f"{'h' if chamber == 'house' else 's'}{congress}-{session}-{roll_number}"

        # Transform vote data
        transformed = self._transform_vote(
            vote_data, chamber, congress, session, roll_number
        )
        transformed["updated_at"] = datetime.utcnow()

        # Upsert to database
        await collection.update_one(
            {"vote_id": vote_id},
            {"$set": transformed},
            upsert=True,
        )

    def _transform_vote(
        self,
        vote_data: dict,
        chamber: str,
        congress: int,
        session: int,
        roll_number: int,
    ) -> dict:
        """Transform API vote data to our schema."""
        vote_id = f"{'h' if chamber == 'house' else 's'}{congress}-{session}-{roll_number}"

        # Extract member votes (now populated by _fetch_detailed_vote)
        member_votes = {}
        for member_data in vote_data.get("members", []):
            bioguide_id = member_data.get("bioguideId")
            vote_position = member_data.get("vote")
            if bioguide_id and vote_position:
                member_votes[bioguide_id] = vote_position

        # Calculate totals from votePartyTotal array
        party_totals = vote_data.get("votePartyTotal", [])
        total_yea = 0
        total_nay = 0
        total_present = 0
        total_not_voting = 0

        for party_total in party_totals:
            total_yea += party_total.get("yeaTotal", 0)
            total_nay += party_total.get("nayTotal", 0)
            total_present += party_total.get("presentTotal", 0)
            total_not_voting += party_total.get("notVotingTotal", 0)

        # Extract bill/legislation information (if present)
        bill_id = None

        # Try legislationNumber/legislationType fields first (House votes)
        leg_number = vote_data.get("legislationNumber")
        leg_type = vote_data.get("legislationType")
        if leg_number and leg_type:
            bill_type_lower = leg_type.lower()
            bill_id = f"{bill_type_lower}{leg_number}-{congress}"
        else:
            # Fall back to bill object (if present)
            bill = vote_data.get("bill")
            if bill:
                bill_type = (bill.get("type") or "").lower()
                bill_number = bill.get("number")
                bill_congress = bill.get("congress")
                if bill_type and bill_number and bill_congress:
                    bill_id = f"{bill_type}{bill_number}-{bill_congress}"

        return {
            "vote_id": vote_id,
            "chamber": chamber,
            "congress": congress,
            "session": session,
            "roll_number": roll_number,
            "date": vote_data.get("startDate"),  # API uses "startDate"
            "question": vote_data.get("voteQuestion", ""),  # API uses "voteQuestion"
            "description": vote_data.get("description"),
            "result": vote_data.get("result"),
            "bill_id": bill_id,
            "totals": {
                "yea": total_yea,
                "nay": total_nay,
                "present": total_present,
                "not_voting": total_not_voting,
            },
            "member_votes": member_votes,
        }
