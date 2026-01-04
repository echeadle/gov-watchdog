"""
Congress.gov API client.

API Documentation: https://api.congress.gov/
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from django.conf import settings

logger = logging.getLogger(__name__)

# API Configuration
CONGRESS_API_BASE_URL = "https://api.congress.gov/v3"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
BACKOFF_BASE = 1.0


def retry_on_failure(max_retries: int = MAX_RETRIES, backoff_base: float = BACKOFF_BASE):
    """Decorator for retry logic with exponential backoff."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limited
                        delay = backoff_base * (2**attempt)
                        logger.warning(
                            f"Rate limited, waiting {delay}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        last_exception = e
                    elif e.response.status_code >= 500:  # Server error
                        delay = backoff_base * (2**attempt)
                        logger.warning(
                            f"Server error {e.response.status_code}, retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                        last_exception = e
                    else:
                        raise
                except httpx.RequestError as e:
                    delay = backoff_base * (2**attempt)
                    logger.warning(f"Request error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    last_exception = e
            raise last_exception

        return wrapper

    return decorator


class CongressClient:
    """
    Async client for Congress.gov API.

    Handles authentication, rate limiting, and response transformation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or settings.CONGRESS_API_KEY
        if not self.api_key:
            raise ValueError("Congress API key is required")

        self.base_url = CONGRESS_API_BASE_URL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"X-Api-Key": self.api_key},
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @retry_on_failure()
    async def _get(
        self, endpoint: str, params: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make a GET request to the API."""
        client = await self._get_client()
        params = params or {}
        params["format"] = "json"

        logger.debug(f"GET {endpoint} params={params}")
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    # ==================== Member Endpoints ====================

    async def get_current_members(
        self, chamber: str = None, congress: int = 119, limit: int = 250, offset: int = 0
    ) -> dict[str, Any]:
        """
        Get current members of Congress.

        Args:
            chamber: 'house' or 'senate' (optional, filters results)
            congress: Congress number (default: 119 for 2025-2027)
            limit: Number of results (max 250)
            offset: Pagination offset
        """
        endpoint = f"/member/congress/{congress}"
        params = {"limit": min(limit, 250), "offset": offset, "currentMember": "true"}
        return await self._get(endpoint, params)

    async def get_member(self, bioguide_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific member.

        Args:
            bioguide_id: Member's bioguide ID (e.g., 'P000197')
        """
        endpoint = f"/member/{bioguide_id}"
        return await self._get(endpoint)

    async def get_member_sponsored_legislation(
        self, bioguide_id: str, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Get bills sponsored by a member."""
        endpoint = f"/member/{bioguide_id}/sponsored-legislation"
        params = {"limit": limit, "offset": offset}
        return await self._get(endpoint, params)

    async def get_member_cosponsored_legislation(
        self, bioguide_id: str, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Get bills cosponsored by a member."""
        endpoint = f"/member/{bioguide_id}/cosponsored-legislation"
        params = {"limit": limit, "offset": offset}
        return await self._get(endpoint, params)

    # ==================== Bill Endpoints ====================

    async def get_bill(
        self, congress: int, bill_type: str, bill_number: int
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific bill.

        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (hr, s, hjres, sjres, hconres, sconres, hres, sres)
            bill_number: Bill number
        """
        endpoint = f"/bill/{congress}/{bill_type}/{bill_number}"
        return await self._get(endpoint)

    async def get_bill_actions(
        self, congress: int, bill_type: str, bill_number: int, limit: int = 20
    ) -> dict[str, Any]:
        """Get actions taken on a bill."""
        endpoint = f"/bill/{congress}/{bill_type}/{bill_number}/actions"
        return await self._get(endpoint, {"limit": limit})

    async def search_bills(
        self,
        query: Optional[str] = None,
        congress: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search for bills.

        Note: Congress.gov API requires /bill/{congress} format, not query param.
        """
        # Use /bill/{congress} endpoint format (query param doesn't work)
        if congress:
            endpoint = f"/bill/{congress}"
        else:
            endpoint = "/bill"

        params = {"limit": limit, "offset": offset}
        # Note: Congress.gov API doesn't have direct text search
        # Query filtering would need to be done client-side
        return await self._get(endpoint, params)

    async def get_bill_summaries(
        self, congress: int, bill_type: str, bill_number: int
    ) -> dict[str, Any]:
        """
        Get bill summaries from /bill/{congress}/{type}/{number}/summaries.

        Returns CRS-generated summaries at different bill stages.
        Summaries are HTML-formatted and 15k-65k characters.
        """
        endpoint = f"/bill/{congress}/{bill_type}/{bill_number}/summaries"
        return await self._get(endpoint)

    async def get_bill_subjects(
        self, congress: int, bill_type: str, bill_number: int
    ) -> dict[str, Any]:
        """
        Get bill subjects from /bill/{congress}/{type}/{number}/subjects.

        Returns policy area and legislative subjects (topics).
        """
        endpoint = f"/bill/{congress}/{bill_type}/{bill_number}/subjects"
        return await self._get(endpoint)

    # ==================== Vote Endpoints ====================

    async def get_house_votes(
        self, congress: int, session: int, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Get House roll call votes."""
        endpoint = f"/house-vote/{congress}/{session}"
        params = {"limit": limit, "offset": offset}
        return await self._get(endpoint, params)

    async def get_senate_votes(
        self, congress: int, session: int, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Get Senate roll call votes."""
        endpoint = f"/senate-vote/{congress}/{session}"
        params = {"limit": limit, "offset": offset}
        return await self._get(endpoint, params)

    async def get_house_vote(
        self, congress: int, session: int, roll_number: int
    ) -> dict[str, Any]:
        """Get a specific House roll call vote."""
        endpoint = f"/house-vote/{congress}/{session}/{roll_number}"
        return await self._get(endpoint)

    async def get_senate_vote(
        self, congress: int, session: int, roll_number: int
    ) -> dict[str, Any]:
        """Get a specific Senate roll call vote."""
        endpoint = f"/senate-vote/{congress}/{session}/{roll_number}"
        return await self._get(endpoint)

    async def get_house_vote_members(
        self, congress: int, session: int, roll_number: int, limit: int = 500
    ) -> dict[str, Any]:
        """Get member votes for a specific House roll call vote."""
        endpoint = f"/house-vote/{congress}/{session}/{roll_number}/members"
        params = {"limit": limit}
        return await self._get(endpoint, params)

    async def get_senate_vote_members(
        self, congress: int, session: int, roll_number: int, limit: int = 500
    ) -> dict[str, Any]:
        """Get member votes for a specific Senate roll call vote."""
        endpoint = f"/senate-vote/{congress}/{session}/{roll_number}/members"
        params = {"limit": limit}
        return await self._get(endpoint, params)

    # ==================== Data Transformation ====================

    # State name to abbreviation mapping
    STATE_ABBREV = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
        "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
        "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
        "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
        "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
        "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
        "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
        "Puerto Rico": "PR", "Guam": "GU", "American Samoa": "AS",
        "U.S. Virgin Islands": "VI", "Northern Mariana Islands": "MP",
    }

    def transform_member(self, data: dict) -> dict:
        """Transform API member data to our schema."""
        member = data.get("member", data)

        # Get current term info
        # Handle both formats: {"item": [...]} from list endpoint, or [...] from detail endpoint
        terms_data = member.get("terms", [])
        if isinstance(terms_data, dict):
            terms = terms_data.get("item", [])
        else:
            terms = terms_data if isinstance(terms_data, list) else []
        current_term = terms[-1] if terms else {}

        # Determine chamber from current term - normalize to "house" or "senate"
        chamber = current_term.get("chamber", "").lower()
        if "house" in chamber:
            chamber = "house"
        elif "senate" in chamber:
            chamber = "senate"
        elif not chamber:
            chamber = "house" if member.get("district") else "senate"

        # Get name and parse first/last if not provided
        full_name = member.get("directOrderName") or member.get("name", "")
        first_name = member.get("firstName", "")
        last_name = member.get("lastName", "")

        # Parse name if first_name/last_name not provided
        if not first_name or not last_name:
            first_name, last_name = self._parse_name(full_name)

        # Normalize state to 2-letter code
        state = member.get("state", "")
        if len(state) > 2:
            state = self.STATE_ABBREV.get(state, state)

        # Extract contact information from addressInformation
        address_info = member.get("addressInformation", {})
        phone = address_info.get("phoneNumber")
        office_address = address_info.get("officeAddress")

        return {
            "bioguide_id": member.get("bioguideId"),
            "name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "party": self._normalize_party(member.get("partyName", "")),
            "state": state,
            "district": member.get("district"),
            "chamber": chamber,
            "image_url": member.get("depiction", {}).get("imageUrl"),
            "official_url": member.get("officialWebsiteUrl"),
            "phone": phone,
            "address": office_address,
            "terms": [self._transform_term(t) for t in terms],
        }

    def _parse_name(self, full_name: str) -> tuple[str, str]:
        """Parse a full name into first and last name."""
        if not full_name:
            return "", ""

        # Handle "Last, First Middle" format
        if ", " in full_name:
            parts = full_name.split(", ", 1)
            last_name = parts[0].strip()
            first_parts = parts[1].split() if len(parts) > 1 else []
            first_name = first_parts[0] if first_parts else ""
            return first_name, last_name

        # Handle "First Last" format
        parts = full_name.split()
        if len(parts) >= 2:
            return parts[0], parts[-1]
        elif len(parts) == 1:
            return parts[0], ""
        return "", ""

    def _normalize_party(self, party_name: str) -> str:
        """Convert party name to abbreviation."""
        party_map = {
            "Democratic": "D",
            "Republican": "R",
            "Independent": "I",
            "Libertarian": "L",
        }
        return party_map.get(party_name, party_name[:1] if party_name else "")

    def _transform_term(self, term: dict) -> dict:
        """Transform a term record."""
        return {
            "congress": term.get("congress"),
            "chamber": term.get("chamber", "").lower(),
            "start_year": term.get("startYear"),
            "end_year": term.get("endYear"),
            "state": term.get("stateCode", ""),
            "district": term.get("district"),
            "party": self._normalize_party(term.get("partyName", "")),
        }

    @staticmethod
    def strip_html(html_text: str) -> str:
        """
        Strip HTML tags from text and return plain text.

        Args:
            html_text: HTML-formatted text

        Returns:
            Plain text with HTML tags removed
        """
        if not html_text:
            return ""

        soup = BeautifulSoup(html_text, "html.parser")
        # Get text and clean up whitespace
        text = soup.get_text(separator=" ", strip=True)
        # Normalize multiple spaces to single space
        return " ".join(text.split())

    def transform_bill(
        self,
        data: dict,
        summaries_data: Optional[dict] = None,
        subjects_data: Optional[dict] = None,
    ) -> dict | None:
        """
        Transform API bill data to our schema.

        Args:
            data: Bill data from /bill endpoint
            summaries_data: Optional summaries data from /summaries endpoint
            subjects_data: Optional subjects data from /subjects endpoint

        Returns:
            Transformed bill dict or None if not a valid bill
        """
        bill = data.get("bill", data)

        # Check if this is an amendment (has amendmentNumber but no bill number)
        if "amendmentNumber" in bill or bill.get("number") is None:
            # This is an amendment, not a bill - skip it
            return None

        # Safely handle bill type which can be None
        bill_type = bill.get("type") or ""
        bill_type_lower = bill_type.lower() if bill_type else ""

        # If no bill type, this isn't a valid bill
        if not bill_type:
            return None

        result = {
            "bill_id": f"{bill_type_lower}{bill.get('number')}-{bill.get('congress')}",
            "congress": bill.get("congress"),
            "type": bill_type_lower,
            "number": bill.get("number"),
            "title": bill.get("title", ""),
            "short_title": bill.get("shortTitle"),
            "sponsor_id": bill.get("sponsors", [{}])[0].get("bioguideId")
            if bill.get("sponsors")
            else None,
            "introduced_date": bill.get("introducedDate"),
            "latest_action": bill.get("latestAction", {}).get("text"),
            "latest_action_date": bill.get("latestAction", {}).get("actionDate"),
            # Initialize with defaults
            "legislative_subjects": [],
            "summaries": [],
        }

        # Add subjects if provided
        if subjects_data and isinstance(subjects_data, dict):
            try:
                subjects = subjects_data.get("subjects", subjects_data)

                # Ensure subjects is a dict before calling .get()
                if isinstance(subjects, dict):
                    # Extract policy area
                    policy_area = subjects.get("policyArea")
                    if policy_area and isinstance(policy_area, dict):
                        result["policy_area"] = policy_area.get("name")

                    # Extract legislative subjects
                    legislative_subjects = subjects.get("legislativeSubjects", [])
                    if isinstance(legislative_subjects, dict):
                        # Handle paginated response
                        legislative_subjects = legislative_subjects.get("item", [])

                    if isinstance(legislative_subjects, list):
                        result["legislative_subjects"] = [
                            subj.get("name") for subj in legislative_subjects
                            if isinstance(subj, dict) and subj.get("name")
                        ]
            except Exception as e:
                logger.warning(f"Error processing subjects data: {e}")

        # Add summaries if provided
        if summaries_data and isinstance(summaries_data, dict):
            try:
                summaries = summaries_data.get("summaries", summaries_data)
                if isinstance(summaries, dict):
                    # Handle paginated response
                    summaries = summaries.get("item", [])

                if isinstance(summaries, list):
                    result["summaries"] = [
                        {
                            "version_code": s.get("versionCode"),
                            "action_desc": s.get("actionDesc"),
                            "action_date": s.get("actionDate"),
                            "text_html": s.get("text"),
                            "text_plain": self.strip_html(s.get("text", "")),
                            "updated_at": s.get("updateDate"),
                        }
                        for s in summaries
                        if isinstance(s, dict) and s.get("text")
                    ]
            except Exception as e:
                logger.warning(f"Error processing summaries data: {e}")

        return result

    def transform_amendment(self, data: dict) -> dict | None:
        """
        Transform API amendment data to our schema.

        Returns None if the item is not a valid amendment.
        """
        amendment = data.get("amendment", data)

        # Check if this has an amendment number
        amendment_number = amendment.get("amendmentNumber")
        if not amendment_number:
            return None

        congress = amendment.get("congress")
        amendment_type = amendment.get("type", "").lower() if amendment.get("type") else ""

        # Determine amendment type (hamdt = House amendment, samdt = Senate amendment)
        if not amendment_type:
            # Infer from URL if available
            url = amendment.get("url", "")
            if "hamdt" in url:
                amendment_type = "hamdt"
            elif "samdt" in url:
                amendment_type = "samdt"

        return {
            "amendment_id": f"{amendment_type}{amendment_number}-{congress}",
            "amendment_number": amendment_number,
            "congress": congress,
            "type": amendment_type,
            "description": amendment.get("description", ""),
            "purpose": amendment.get("purpose", ""),
            "chamber": "house" if amendment_type == "hamdt" else "senate" if amendment_type == "samdt" else None,
            "introduced_date": amendment.get("introducedDate"),
            "latest_action": amendment.get("latestAction", {}).get("text"),
            "latest_action_date": amendment.get("latestAction", {}).get("actionDate"),
            "url": amendment.get("url"),
        }


# Singleton instance
_congress_client: Optional[CongressClient] = None


def get_congress_client() -> CongressClient:
    """Get or create the Congress API client singleton."""
    global _congress_client
    if _congress_client is None:
        _congress_client = CongressClient()
    return _congress_client
