"""
Unit tests for enhanced member search functionality.

Tests the flexible name search in services._build_name_search_query
and MemberService.search_members.
"""

import pytest

from members.services import _build_name_search_query, _escape_regex_special_chars


class TestEscapeRegexSpecialChars:
    """Test regex character escaping for safe MongoDB queries."""

    def test_escapes_parentheses(self):
        """Should escape parentheses used in names like Jr., Sr."""
        result = _escape_regex_special_chars("Smith (Jr.)")
        # Check that backslashes are present before special chars
        assert r"\(" in result
        assert r"\." in result
        assert r"\)" in result

    def test_escapes_apostrophe(self):
        """Should handle apostrophes in names like O'Brien."""
        # Note: Apostrophes don't need escaping in regex, but test the function
        result = _escape_regex_special_chars("O'Brien")
        assert result == "O'Brien"

    def test_escapes_period(self):
        """Should escape periods in names with initials."""
        result = _escape_regex_special_chars("John D. Smith")
        # Check that period is escaped
        assert r"\." in result
        assert "John D" in result

    def test_escapes_asterisk(self):
        """Should escape asterisk to prevent wildcard matching."""
        result = _escape_regex_special_chars("Test*")
        assert r"\*" in result

    def test_escapes_plus(self):
        """Should escape plus sign."""
        result = _escape_regex_special_chars("C++")
        assert r"\+" in result

    def test_escapes_brackets(self):
        """Should escape square brackets."""
        result = _escape_regex_special_chars("Test[ing]")
        assert r"\[" in result
        assert r"\]" in result

    def test_no_escaping_needed(self):
        """Should handle normal names without modification."""
        result = _escape_regex_special_chars("John Smith")
        assert result == "John Smith"


class TestBuildNameSearchQuery:
    """Test the flexible name search query builder."""

    def test_single_word_search(self):
        """Single word should search first_name, last_name, and full name."""
        query = _build_name_search_query("Mike")

        assert "$or" in query
        conditions = query["$or"]

        # Should have 3 conditions: first_name, last_name, name
        assert len(conditions) == 3

        # Check first_name condition
        assert {"first_name": {"$regex": "\\bMike", "$options": "i"}} in conditions

        # Check last_name condition
        assert {"last_name": {"$regex": "\\bMike", "$options": "i"}} in conditions

        # Check full name condition
        assert {"name": {"$regex": "\\bMike", "$options": "i"}} in conditions

    def test_single_word_with_word_boundary(self):
        """Word boundary should enable partial matching from start of words."""
        query = _build_name_search_query("Mic")

        # Check that pattern uses word boundary
        first_name_pattern = query["$or"][0]["first_name"]["$regex"]
        assert first_name_pattern == "\\bMic"

        # This pattern should match "Michael", "Michelle", "Mick"
        # but not "Dominic" because \b matches start of word

    def test_two_word_search_forward_order(self):
        """Two words should try both 'First Last' and 'Last First' orders."""
        query = _build_name_search_query("Mike Lee")

        assert "$or" in query
        conditions = query["$or"]

        # Should have 3 conditions: forward, reverse, and full name
        assert len(conditions) == 3

        # Check "Mike Lee" as first_name + last_name
        forward_condition = {
            "$and": [
                {"first_name": {"$regex": "\\bMike", "$options": "i"}},
                {"last_name": {"$regex": "\\bLee", "$options": "i"}},
            ]
        }
        assert forward_condition in conditions

        # Check "Lee Mike" as first_name + last_name (reversed)
        reverse_condition = {
            "$and": [
                {"first_name": {"$regex": "\\bLee", "$options": "i"}},
                {"last_name": {"$regex": "\\bMike", "$options": "i"}},
            ]
        }
        assert reverse_condition in conditions

    def test_two_word_search_full_name_pattern(self):
        """Two word search should also check full name field."""
        query = _build_name_search_query("Nancy Pelosi")

        # Find the full name condition
        full_name_condition = next(
            (c for c in query["$or"] if "name" in c and "$and" not in c),
            None,
        )

        assert full_name_condition is not None
        pattern = full_name_condition["name"]["$regex"]

        # Should match both "Nancy...Pelosi" and "Pelosi...Nancy"
        assert "\\bNancy.*\\bPelosi" in pattern or "\\bPelosi.*\\bNancy" in pattern

    def test_three_word_search(self):
        """Three or more words should be handled gracefully."""
        query = _build_name_search_query("Martin Luther King")

        assert "$or" in query
        conditions = query["$or"]

        # Should have multiple patterns
        assert len(conditions) >= 2

        # Should include full name pattern with all three words
        full_name_patterns = [
            c for c in conditions if "name" in c and "$and" not in c
        ]
        assert len(full_name_patterns) > 0

        # Check that pattern includes all words in sequence
        pattern = full_name_patterns[0]["name"]["$regex"]
        assert "\\bMartin" in pattern
        assert "\\bLuther" in pattern
        assert "\\bKing" in pattern

    def test_three_word_search_first_last_combination(self):
        """Three words should try first word + last word combination."""
        query = _build_name_search_query("Mary Jane Smith")

        conditions = query["$or"]

        # Should try "Mary" as first, "Smith" as last
        first_last_forward = {
            "$and": [
                {"first_name": {"$regex": "\\bMary", "$options": "i"}},
                {"last_name": {"$regex": "\\bSmith", "$options": "i"}},
            ]
        }
        assert first_last_forward in conditions

        # Should try "Smith" as first, "Mary" as last (reversed)
        first_last_reverse = {
            "$and": [
                {"first_name": {"$regex": "\\bSmith", "$options": "i"}},
                {"last_name": {"$regex": "\\bMary", "$options": "i"}},
            ]
        }
        assert first_last_reverse in conditions

    def test_empty_search_term(self):
        """Empty or whitespace-only search should return empty query."""
        assert _build_name_search_query("") == {}
        assert _build_name_search_query("   ") == {}
        assert _build_name_search_query("\t\n") == {}

    def test_handles_special_characters(self):
        """Should safely handle names with special regex characters."""
        query = _build_name_search_query("O'Brien")

        # Should not raise an error and should escape properly
        assert "$or" in query

        # The apostrophe should be in the pattern
        first_name_pattern = query["$or"][0]["first_name"]["$regex"]
        assert "O'Brien" in first_name_pattern

    def test_case_insensitive_flag(self):
        """All patterns should have case-insensitive option."""
        query = _build_name_search_query("Mike Lee")

        # Check all conditions have $options: "i"
        for condition in query["$or"]:
            if "$and" in condition:
                for subcondition in condition["$and"]:
                    for field_query in subcondition.values():
                        assert field_query["$options"] == "i"
            else:
                for field_query in condition.values():
                    assert field_query["$options"] == "i"

    def test_partial_matching_examples(self):
        """Test common partial matching scenarios."""
        # "Mic" should match start of "Michael", "Michelle", "Mick"
        query = _build_name_search_query("Mic")
        pattern = query["$or"][0]["first_name"]["$regex"]
        assert pattern == "\\bMic"

        # "Smit" should match "Smith", "Smithson"
        query = _build_name_search_query("Smit")
        pattern = query["$or"][0]["first_name"]["$regex"]
        assert pattern == "\\bSmit"

    def test_whitespace_normalization(self):
        """Should handle extra whitespace gracefully."""
        query1 = _build_name_search_query("  Mike   Lee  ")
        query2 = _build_name_search_query("Mike Lee")

        # Both should produce equivalent queries (ignoring whitespace)
        assert query1 == query2


class TestSearchMembersIntegration:
    """
    Integration test examples for the enhanced search.

    Note: These are example test cases that would need a test database
    with sample data to run. They demonstrate the expected behavior.
    """

    def test_search_by_first_name_only(self):
        """
        Example: Searching 'Mike' should find all members with first name Mike.

        Expected results:
        - Mike Lee (R-UT)
        - Mike Johnson (R-LA)
        - Mike Braun (R-IN)
        - etc.
        """
        # params = MemberSearchParams(q="Mike")
        # result = await MemberService.search_members(params)
        # assert result.total >= 3
        # assert any("Mike Lee" in r["name"] for r in result.results)
        pass

    def test_search_by_last_name_only(self):
        """
        Example: Searching 'Smith' should find all members with last name Smith.

        Expected results:
        - Adam Smith (D-WA)
        - Tina Smith (D-MN)
        - Jason Smith (R-MO)
        - etc.
        """
        pass

    def test_search_full_name_forward(self):
        """
        Example: Searching 'Nancy Pelosi' should find Nancy Pelosi.
        """
        pass

    def test_search_full_name_reverse(self):
        """
        Example: Searching 'Pelosi Nancy' should also find Nancy Pelosi.
        """
        pass

    def test_partial_name_search(self):
        """
        Example: Searching 'Mic' should find Michael, Michelle, Mick, etc.
        """
        pass

    def test_search_with_state_filter(self):
        """
        Example: Searching 'Smith' + state='CA' should only find CA Smiths.
        """
        pass

    def test_search_with_party_filter(self):
        """
        Example: Searching 'Mike' + party='R' should only find Republican Mikes.
        """
        pass

    def test_search_case_insensitive(self):
        """
        Example: Searching 'MIKE', 'mike', 'Mike' should all return same results.
        """
        pass


if __name__ == "__main__":
    # Run unit tests
    pytest.main([__file__, "-v"])
