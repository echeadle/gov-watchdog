"""
Integration tests for Member API endpoints.

These tests verify the actual HTTP API endpoints work correctly
with real database queries (using the test database).
"""

import pytest
from django.test import AsyncClient
from config.database import get_database


@pytest.fixture
async def async_client():
    """Create an async test client for making HTTP requests."""
    return AsyncClient()


@pytest.fixture(autouse=True)
async def setup_test_db():
    """
    Ensure database connection is ready.

    Note: These tests use the actual MongoDB database configured
    in settings. For true isolation, you'd want a separate test
    database, but for now we test against the dev database.
    """
    db = await get_database()
    yield db
    # Teardown: could clean up test data here if needed


class TestMemberListAPI:
    """Test the /api/v1/members/ endpoint."""

    @pytest.mark.asyncio
    async def test_list_members_success(self, async_client):
        """Should return paginated list of members."""
        response = await async_client.get("/api/v1/members/")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        # Check we have members
        assert data["total"] > 0
        assert len(data["results"]) > 0

        # Check member structure
        member = data["results"][0]
        assert "bioguide_id" in member
        assert "name" in member
        assert "party" in member
        assert "state" in member
        assert "chamber" in member

    @pytest.mark.asyncio
    async def test_search_by_name(self, async_client):
        """Should filter members by name query."""
        response = await async_client.get("/api/v1/members/?q=Mike")

        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) > 0

        # All results should have "Mike" in the name
        for member in data["results"]:
            name_lower = member["name"].lower()
            assert "mike" in name_lower or "michael" in name_lower

    @pytest.mark.asyncio
    async def test_search_by_full_name(self, async_client):
        """Should find member by full name."""
        # Search for a known senator
        response = await async_client.get("/api/v1/members/?q=Alex+Padilla")

        assert response.status_code == 200
        data = response.json()

        # Should find Alex Padilla
        assert len(data["results"]) > 0
        names = [m["name"] for m in data["results"]]
        assert any("Padilla" in name and "Alex" in name for name in names)

    @pytest.mark.asyncio
    async def test_filter_by_state(self, async_client):
        """Should filter members by state."""
        response = await async_client.get("/api/v1/members/?state=CA")

        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) > 0

        # All results should be from California
        for member in data["results"]:
            assert member["state"] == "CA"

    @pytest.mark.asyncio
    async def test_filter_by_party(self, async_client):
        """Should filter members by party."""
        response = await async_client.get("/api/v1/members/?party=D")

        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) > 0

        # All results should be Democrats
        for member in data["results"]:
            assert member["party"] == "D"

    @pytest.mark.asyncio
    async def test_filter_by_chamber(self, async_client):
        """Should filter members by chamber."""
        response = await async_client.get("/api/v1/members/?chamber=senate")

        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) > 0

        # All results should be senators
        for member in data["results"]:
            assert member["chamber"] == "senate"

        # Total should be around 100 (number of senators)
        assert data["total"] <= 102  # Allow for vacancies/appointments

    @pytest.mark.asyncio
    async def test_combined_filters(self, async_client):
        """Should handle multiple filters together."""
        response = await async_client.get(
            "/api/v1/members/?state=CA&party=D&chamber=senate"
        )

        assert response.status_code == 200
        data = response.json()

        # California has 2 Democratic senators (as of test data)
        assert data["total"] >= 1

        for member in data["results"]:
            assert member["state"] == "CA"
            assert member["party"] == "D"
            assert member["chamber"] == "senate"

    @pytest.mark.asyncio
    async def test_pagination(self, async_client):
        """Should paginate results correctly."""
        # Get first page
        response1 = await async_client.get("/api/v1/members/?page_size=10&page=1")
        data1 = response1.json()

        # Get second page
        response2 = await async_client.get("/api/v1/members/?page_size=10&page=2")
        data2 = response2.json()

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both pages should have results
        assert len(data1["results"]) == 10
        assert len(data2["results"]) > 0

        # Results should be different
        page1_ids = {m["bioguide_id"] for m in data1["results"]}
        page2_ids = {m["bioguide_id"] for m in data2["results"]}
        assert page1_ids != page2_ids

    @pytest.mark.asyncio
    async def test_empty_search_results(self, async_client):
        """Should handle searches with no results gracefully."""
        response = await async_client.get(
            "/api/v1/members/?q=ThisNameDefinitelyDoesNotExist12345"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["results"]) == 0


class TestMemberDetailAPI:
    """Test the /api/v1/members/{bioguide_id}/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_member_success(self, async_client):
        """Should return member details for valid bioguide ID."""
        # Use Alex Padilla's bioguide ID
        response = await async_client.get("/api/v1/members/P000145/")

        assert response.status_code == 200
        data = response.json()

        # Check member structure
        assert data["bioguide_id"] == "P000145"
        assert "name" in data
        assert "party" in data
        assert "state" in data
        assert data["state"] == "CA"
        assert data["chamber"] == "senate"

    @pytest.mark.asyncio
    async def test_get_member_not_found(self, async_client):
        """Should return 404 for invalid bioguide ID."""
        response = await async_client.get("/api/v1/members/INVALID999/")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestMemberStatsAPI:
    """Test the /api/v1/members/stats/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, async_client):
        """Should return aggregate member statistics."""
        response = await async_client.get("/api/v1/members/stats/")

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "total" in data
        assert "by_party" in data
        assert "by_chamber" in data

        # Check reasonable totals
        assert data["total"] > 500  # Should be around 539
        assert data["total"] < 600

        # Check party breakdown
        assert "D" in data["by_party"]
        assert "R" in data["by_party"]

        # Check chamber breakdown
        assert "house" in data["by_chamber"]
        assert "senate" in data["by_chamber"]
        assert data["by_chamber"]["senate"] <= 102


class TestStatesAPI:
    """Test the /api/v1/members/states/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_states_success(self, async_client):
        """Should return list of states with member counts."""
        response = await async_client.get("/api/v1/members/states/")

        assert response.status_code == 200
        data = response.json()

        assert "states" in data
        assert len(data["states"]) >= 50  # All 50 states + territories

        # Check structure of state entries
        state = data["states"][0]
        assert "state" in state
        assert "count" in state
        assert state["count"] > 0

        # California should have many representatives
        ca_states = [s for s in data["states"] if s["state"] == "CA"]
        assert len(ca_states) == 1
        assert ca_states[0]["count"] >= 50  # CA has ~52 House + 2 Senate


class TestMemberBillsAPI:
    """Test the /api/v1/members/{bioguide_id}/bills/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_member_bills_sponsored(self, async_client):
        """Should return bills sponsored by member."""
        # Adam Schiff has many sponsored bills
        response = await async_client.get("/api/v1/members/S001150/bills/?type=sponsored&limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "total" in data
        assert len(data["results"]) > 0

        # Check bill structure
        bill = data["results"][0]
        assert "bill_id" in bill
        assert "title" in bill
        assert "congress" in bill
        assert "type" in bill

    @pytest.mark.asyncio
    async def test_get_member_bills_cosponsored(self, async_client):
        """Should return bills cosponsored by member."""
        response = await async_client.get("/api/v1/members/P000145/bills/?type=cosponsored&limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        # Member may or may not have cosponsored bills

    @pytest.mark.asyncio
    async def test_invalid_bill_type(self, async_client):
        """Should reject invalid bill type parameter."""
        response = await async_client.get("/api/v1/members/P000145/bills/?type=invalid")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
