"""
XML parser for Senate roll call votes.

Senate votes are only available as XML from Senate.gov, not via Congress.gov JSON API.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SenateVoteXMLParser:
    """Parse Senate roll call vote XML files."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def fetch_and_parse(self, xml_url: str) -> Optional[dict]:
        """
        Fetch XML from URL and parse it.

        Args:
            xml_url: URL to the Senate vote XML file

        Returns:
            Parsed vote data dict, or None if error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(xml_url)
                response.raise_for_status()
                xml_content = response.text

            return self.parse_xml(xml_content)

        except Exception as e:
            logger.error(f"Error fetching/parsing Senate XML from {xml_url}: {e}")
            return None

    def parse_xml(self, xml_content: str) -> dict:
        """
        Parse Senate vote XML content.

        Args:
            xml_content: Raw XML string

        Returns:
            Dict with vote metadata and member votes
        """
        root = ET.fromstring(xml_content)

        # Extract vote metadata
        vote_data = {
            "congress": self._get_text(root, "congress"),
            "session": self._get_text(root, "session"),
            "vote_number": self._get_text(root, "vote_number"),
            "vote_date": self._parse_date(self._get_text(root, "vote_date")),
            "vote_question": self._get_text(root, "vote_question_text"),
            "vote_result": self._get_text(root, "vote_result"),
            "vote_result_text": self._get_text(root, "vote_result_text"),
            "vote_document": self._get_text(root, "vote_document_text"),
        }

        # Extract member votes
        members = []
        for member_elem in root.findall(".//member"):
            member = {
                "first_name": self._get_text(member_elem, "first_name"),
                "last_name": self._get_text(member_elem, "last_name"),
                "party": self._get_text(member_elem, "party"),
                "state": self._get_text(member_elem, "state"),
                "vote_cast": self._get_text(member_elem, "vote_cast"),
                "lis_member_id": self._get_text(member_elem, "lis_member_id"),
            }
            members.append(member)

        vote_data["members"] = members

        # Extract totals from count section
        count_elem = root.find(".//count")
        if count_elem is not None:
            vote_data["totals"] = {
                "yea": int(self._get_text(count_elem, "yeas", "0")),
                "nay": int(self._get_text(count_elem, "nays", "0")),
                "present": int(self._get_text(count_elem, "present", "0")),
                "absent": int(self._get_text(count_elem, "absent", "0")),
            }
        else:
            # Parse from vote_result_text (e.g., "Agreed to (73-15)")
            vote_data["totals"] = self._parse_totals_from_result(
                vote_data.get("vote_result_text", "")
            )

        return vote_data

    def _get_text(self, element: ET.Element, tag: str, default: str = "") -> str:
        """Get text content from XML element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse Senate vote date string to ISO format.

        Senate dates are like: "January 8, 2024, 05:27 PM"
        """
        if not date_str:
            return None

        try:
            # Parse the date
            dt = datetime.strptime(date_str, "%B %d, %Y, %I:%M %p")
            # Return ISO format with timezone (Senate is in Eastern Time)
            return dt.strftime("%Y-%m-%dT%H:%M:%S-05:00")
        except ValueError:
            logger.warning(f"Could not parse Senate date: {date_str}")
            return date_str

    def _parse_totals_from_result(self, result_text: str) -> dict:
        """
        Parse vote totals from result text.

        Example: "Cloture Motion Agreed to (73-15)"
        """
        totals = {"yea": 0, "nay": 0, "present": 0, "absent": 0}

        # Try to extract numbers from parentheses
        import re

        match = re.search(r"\((\d+)-(\d+)\)", result_text)
        if match:
            totals["yea"] = int(match.group(1))
            totals["nay"] = int(match.group(2))

        return totals
