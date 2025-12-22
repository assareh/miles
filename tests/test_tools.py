"""Unit tests for tools module."""

import json
from datetime import datetime, timedelta
from unittest import mock

import pytest


# Mock config before importing tools
@pytest.fixture(autouse=True)
def mock_config(tmp_path):
    """Mock config to use temp directory for all tests."""
    with mock.patch("data_storage.config") as mock_cfg:
        mock_cfg.DATA_DIR = str(tmp_path)
        mock_cfg.USER_DATA_FILE = str(tmp_path / "user.json")
        yield mock_cfg


class TestCreditCardSearchRecentlyUpdated:
    """Tests for credit_card_search recently_updated filter."""

    @pytest.fixture
    def sample_cards_with_dates(self, tmp_path):
        """Create sample credit cards with various last_updated dates."""
        today = datetime.now()
        cards = [
            {
                "card_name": "Recently Updated Card",
                "issuer": "Chase",
                "last_updated": (today - timedelta(days=5)).strftime("%m/%d/%y"),
                "rewards_currency": "Ultimate Rewards",
            },
            {
                "card_name": "Month Old Card",
                "issuer": "Amex",
                "last_updated": (today - timedelta(days=45)).strftime("%m/%d/%y"),
                "rewards_currency": "Membership Rewards",
            },
            {
                "card_name": "Old Card",
                "issuer": "Capital One",
                "last_updated": (today - timedelta(days=120)).strftime("%m/%d/%y"),
                "rewards_currency": "Miles",
            },
            {
                "card_name": "Very Old Card",
                "issuer": "Citi",
                "last_updated": (today - timedelta(days=200)).strftime("%m/%d/%y"),
                "rewards_currency": "ThankYou Points",
            },
            {
                "card_name": "Card Without Date",
                "issuer": "Discover",
                "rewards_currency": "Cash Back",
            },
        ]
        (tmp_path / "credit_cards.json").write_text(json.dumps(cards))
        return cards

    def test_recently_updated_30_days(self, sample_cards_with_dates):
        """Should filter to cards updated in last 30 days."""
        from tools import credit_card_search

        result = json.loads(credit_card_search.invoke({"query": "card", "recently_updated": 30}))

        assert "search_results" in result
        card_names = [c["card_name"] for c in result["search_results"]]
        assert "Recently Updated Card" in card_names
        assert "Month Old Card" not in card_names
        assert "Old Card" not in card_names

    def test_recently_updated_90_days(self, sample_cards_with_dates):
        """Should filter to cards updated in last 90 days."""
        from tools import credit_card_search

        result = json.loads(credit_card_search.invoke({"query": "card", "recently_updated": 90}))

        assert "search_results" in result
        card_names = [c["card_name"] for c in result["search_results"]]
        assert "Recently Updated Card" in card_names
        assert "Month Old Card" in card_names
        assert "Old Card" not in card_names

    def test_recently_updated_excludes_cards_without_date(self, sample_cards_with_dates):
        """Should exclude cards without last_updated field when filtering."""
        from tools import credit_card_search

        result = json.loads(credit_card_search.invoke({"query": "card", "recently_updated": 365}))

        card_names = [c["card_name"] for c in result["search_results"]]
        assert "Card Without Date" not in card_names

    def test_recently_updated_none_returns_all(self, sample_cards_with_dates):
        """Should return all cards when recently_updated is None."""
        from tools import credit_card_search

        result = json.loads(credit_card_search.invoke({"query": "card"}))

        assert "search_results" in result
        # Without recently_updated filter, all matching cards should appear
        assert result["total_results"] >= 4

    def test_recently_updated_invalid_returns_error(self, sample_cards_with_dates):
        """Should return error for invalid recently_updated value."""
        from tools import credit_card_search

        result = json.loads(credit_card_search.invoke({"query": "card", "recently_updated": -1}))

        assert "error" in result

    def test_recently_updated_with_other_filters(self, sample_cards_with_dates):
        """Should work with other search filters."""
        from tools import credit_card_search

        result = json.loads(credit_card_search.invoke({"query": "Chase", "recently_updated": 30}))

        assert "search_results" in result
        # Should only find Chase cards updated recently
        for card in result["search_results"]:
            assert "chase" in card["card_name"].lower() or "chase" in card.get("issuer", "").lower()


class TestGetValuations:
    """Tests for get_valuations tool with programs filter."""

    @pytest.fixture
    def sample_valuations(self, tmp_path):
        """Create sample valuations file."""
        content = {
            "version": "1.0",
            "unit": "cents_per_point",
            "valuations": {
                "chase_ultimate_rewards": {
                    "value": 1.80,
                    "display_name": "Chase Ultimate Rewards",
                    "category": "Transferable Points",
                },
                "amex_membership_rewards": {
                    "value": 1.75,
                    "display_name": "American Express Membership Rewards",
                    "category": "Transferable Points",
                },
                "united_mileageplus": {
                    "value": 1.20,
                    "display_name": "United MileagePlus",
                    "category": "Airline Miles",
                },
                "hilton_honors": {
                    "value": 0.50,
                    "display_name": "Hilton Honors",
                    "category": "Hotel Points",
                },
            },
        }
        (tmp_path / "valuations.json").write_text(json.dumps(content))
        return content

    def test_get_all_valuations(self, sample_valuations):
        """Should return all valuations when no filter specified."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({}))

        assert "valuations" in result
        assert "unit" in result
        assert result["unit"] == "cents_per_point"
        assert len(result["valuations"]) == 4

    def test_filter_by_program_keys(self, sample_valuations):
        """Should filter to specific programs by key."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({"programs": ["chase_ultimate_rewards", "united_mileageplus"]}))

        assert "valuations" in result
        assert len(result["valuations"]) == 2
        assert "chase_ultimate_rewards" in result["valuations"]
        assert "united_mileageplus" in result["valuations"]
        assert "hilton_honors" not in result["valuations"]

    def test_filter_by_display_name(self, sample_valuations):
        """Should filter by display name (case-insensitive)."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({"programs": ["Chase Ultimate Rewards"]}))

        assert "valuations" in result
        assert len(result["valuations"]) == 1
        assert "chase_ultimate_rewards" in result["valuations"]

    def test_filter_normalized_names(self, sample_valuations):
        """Should normalize program names (spaces to underscores, case-insensitive)."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({"programs": ["chase-ultimate-rewards"]}))

        assert "valuations" in result
        assert "chase_ultimate_rewards" in result["valuations"]

    def test_filter_nonexistent_programs(self, sample_valuations):
        """Should return empty for nonexistent programs."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({"programs": ["nonexistent_program"]}))

        assert "valuations" in result
        assert len(result["valuations"]) == 0

    def test_filter_mixed_existing_and_nonexistent(self, sample_valuations):
        """Should return only existing programs from mixed list."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({"programs": ["chase_ultimate_rewards", "nonexistent"]}))

        assert "valuations" in result
        assert len(result["valuations"]) == 1
        assert "chase_ultimate_rewards" in result["valuations"]

    def test_invalid_programs_type(self, sample_valuations):
        """Should raise ValidationError for invalid programs type.

        Pydantic validates input before the function runs, so passing
        a string instead of a list raises a ValidationError.
        """
        from pydantic import ValidationError

        from tools import get_valuations

        with pytest.raises(ValidationError, match="Input should be a valid list"):
            get_valuations.invoke({"programs": "not_a_list"})

    def test_includes_timestamp(self, sample_valuations):
        """Should include last_updated_utc in response."""
        from tools import get_valuations

        result = json.loads(get_valuations.invoke({}))

        assert "last_updated_utc" in result


class TestToolsExported:
    """Tests for tool exports."""

    def test_get_valuations_in_miles_tools(self, tmp_path):
        """get_valuations should be exported in MILES_TOOLS."""
        from tools import MILES_TOOLS

        tool_names = [t.name for t in MILES_TOOLS]
        assert "get_valuations" in tool_names

    def test_credit_card_search_has_recently_updated(self, tmp_path):
        """credit_card_search should have recently_updated parameter."""
        from tools import credit_card_search

        # Check the tool's schema includes recently_updated
        schema = credit_card_search.args_schema.model_json_schema()
        assert "recently_updated" in schema.get("properties", {})
