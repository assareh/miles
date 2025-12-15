"""Unit tests for data_storage module."""

import json
from unittest import mock

import pytest


# Mock config before importing data_storage
@pytest.fixture(autouse=True)
def mock_config(tmp_path):
    """Mock config to use temp directory for all tests."""
    with mock.patch("data_storage.config") as mock_cfg:
        mock_cfg.DATA_DIR = str(tmp_path)
        mock_cfg.USER_DATA_FILE = str(tmp_path / "user.json")
        yield mock_cfg


class TestLoadJsonFile:
    """Tests for _load_json_file function."""

    def test_load_valid_json(self, tmp_path):
        """Should load and parse valid JSON file."""
        from data_storage import _load_json_file

        file_path = tmp_path / "test.json"
        file_path.write_text('{"key": "value"}')

        result = _load_json_file(str(file_path))
        assert result == {"key": "value"}

    def test_load_missing_file(self, tmp_path):
        """Should return None for missing file."""
        from data_storage import _load_json_file

        result = _load_json_file(str(tmp_path / "missing.json"))
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Should raise ValueError for invalid JSON."""
        from data_storage import _load_json_file

        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json {{{")

        with pytest.raises(ValueError, match="Invalid JSON"):
            _load_json_file(str(file_path))


class TestSaveJsonFile:
    """Tests for _save_json_file function."""

    def test_save_creates_file(self, tmp_path):
        """Should create file with JSON content."""
        from data_storage import _save_json_file

        file_path = tmp_path / "output.json"
        _save_json_file(str(file_path), {"test": 123})

        assert file_path.exists()
        content = json.loads(file_path.read_text())
        assert content == {"test": 123}

    def test_save_creates_directories(self, tmp_path):
        """Should create parent directories if needed."""
        from data_storage import _save_json_file

        file_path = tmp_path / "nested" / "dir" / "file.json"
        _save_json_file(str(file_path), {"nested": True})

        assert file_path.exists()


class TestGetCreditCards:
    """Tests for get_credit_cards function."""

    def test_returns_empty_list_if_no_file(self, tmp_path):
        """Should return empty list if credit_cards.json doesn't exist."""
        from data_storage import get_credit_cards

        result = get_credit_cards()
        assert result == []

    def test_returns_cards_from_file(self, tmp_path):
        """Should return cards from credit_cards.json."""
        from data_storage import get_credit_cards

        cards = [{"card_name": "Test Card", "issuer": "Test Bank"}]
        (tmp_path / "credit_cards.json").write_text(json.dumps(cards))

        result = get_credit_cards()
        assert len(result) == 1
        assert result[0]["card_name"] == "Test Card"


class TestGetCreditCardByName:
    """Tests for get_credit_card_by_name with fuzzy matching."""

    @pytest.fixture
    def sample_cards(self, tmp_path):
        """Create sample credit cards file."""
        cards = [
            {"card_name": "Chase Sapphire Preferred Credit Card", "issuer": "Chase"},
            {"card_name": "The Platinum Card from American Express", "issuer": "American Express"},
            {"card_name": "American Express Gold Card", "issuer": "American Express"},
            {"card_name": "Capital One Venture X Rewards Credit Card", "issuer": "Capital One"},
        ]
        (tmp_path / "credit_cards.json").write_text(json.dumps(cards))
        return cards

    def test_exact_match(self, sample_cards):
        """Should find card with exact name match."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("Chase Sapphire Preferred Credit Card")
        assert result is not None
        assert result["issuer"] == "Chase"

    def test_case_insensitive_match(self, sample_cards):
        """Should match regardless of case."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("chase sapphire preferred credit card")
        assert result is not None
        assert result["issuer"] == "Chase"

    def test_fuzzy_match_amex_platinum(self, sample_cards):
        """Should match 'Amex Platinum' to full card name."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("Amex Platinum")
        assert result is not None
        assert "Platinum" in result["card_name"]
        assert result["issuer"] == "American Express"

    def test_fuzzy_match_csp(self, sample_cards):
        """Should match 'Sapphire Preferred' to Chase card."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("Sapphire Preferred")
        assert result is not None
        assert result["issuer"] == "Chase"

    def test_fuzzy_match_venture_x(self, sample_cards):
        """Should match 'Venture X' to Capital One card."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("Venture X")
        assert result is not None
        assert result["issuer"] == "Capital One"

    def test_no_match_returns_none(self, sample_cards):
        """Should return None for completely unrelated name."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("ZZZZZ QQQQQ XXXXX")
        assert result is None

    def test_empty_cards_returns_none(self, tmp_path):
        """Should return None when no cards exist."""
        from data_storage import get_credit_card_by_name

        result = get_credit_card_by_name("Any Card")
        assert result is None


class TestGetTransferPartners:
    """Tests for get_transfer_partners function."""

    def test_returns_empty_dict_if_no_file(self, tmp_path):
        """Should return empty dict if transfer_partners.json doesn't exist."""
        from data_storage import get_transfer_partners

        result = get_transfer_partners()
        assert result == {}

    def test_returns_data_from_file(self, tmp_path):
        """Should return data from transfer_partners.json."""
        from data_storage import get_transfer_partners

        data = {"programs": {"Chase Ultimate Rewards": {"partners": []}}}
        (tmp_path / "transfer_partners.json").write_text(json.dumps(data))

        result = get_transfer_partners()
        assert "programs" in result


class TestGetDefaultValuations:
    """Tests for get_default_valuations parsing."""

    def test_parses_valuations_json_format(self, tmp_path):
        """Should parse standard JSON valuations format."""
        from data_storage import get_default_valuations

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
            },
        }
        (tmp_path / "valuations.json").write_text(json.dumps(content))

        result = get_default_valuations()
        assert result["chase_ultimate_rewards"] == 1.80
        assert result["amex_membership_rewards"] == 1.75
        assert result["united_mileageplus"] == 1.20

    def test_handles_missing_file(self, tmp_path):
        """Should return empty dict if file missing."""
        from data_storage import get_default_valuations

        result = get_default_valuations()
        assert result == {}

    def test_handles_simple_value_format(self, tmp_path):
        """Should handle simple numeric values (backwards compatibility)."""
        from data_storage import get_default_valuations

        content = {
            "version": "1.0",
            "unit": "cents_per_point",
            "valuations": {"chase_ultimate_rewards": 1.50, "world_of_hyatt": 1.80},
        }
        (tmp_path / "valuations.json").write_text(json.dumps(content))

        result = get_default_valuations()
        assert result["chase_ultimate_rewards"] == 1.50
        assert result["world_of_hyatt"] == 1.80

    def test_get_valuations_with_metadata(self, tmp_path):
        """Should return full metadata structure."""
        from data_storage import get_valuations_with_metadata

        content = {
            "version": "1.0",
            "unit": "cents_per_point",
            "valuations": {
                "chase_ultimate_rewards": {
                    "value": 1.50,
                    "display_name": "Chase Ultimate Rewards",
                    "category": "Transferable Points",
                }
            },
        }
        (tmp_path / "valuations.json").write_text(json.dumps(content))

        result = get_valuations_with_metadata()
        assert result["version"] == "1.0"
        assert result["unit"] == "cents_per_point"
        assert "chase_ultimate_rewards" in result["valuations"]
        assert result["valuations"]["chase_ultimate_rewards"]["display_name"] == "Chase Ultimate Rewards"


class TestUserData:
    """Tests for user data functions."""

    def test_get_user_data_returns_defaults_if_missing(self, tmp_path):
        """Should return default structure if user.json missing."""
        from data_storage import get_user_data

        result = get_user_data()
        assert "wallet" in result
        assert "custom_valuations" in result
        assert "credits" in result
        assert result["wallet"] == []

    def test_save_and_load_user_data(self, tmp_path):
        """Should save and load user data correctly."""
        from data_storage import get_user_data, save_user_data

        data = {"wallet": [{"card_name": "Test Card"}], "custom_valuations": {"test": 1.5}, "credits": {}}
        save_user_data(data)

        result = get_user_data()
        assert result["wallet"] == [{"card_name": "Test Card"}]
        assert result["custom_valuations"]["test"] == 1.5
        assert "last_updated" in result


class TestUserValuations:
    """Tests for get_user_valuations merging."""

    def test_merges_default_and_custom(self, tmp_path):
        """Should merge default valuations with custom overrides."""
        from data_storage import get_user_valuations, save_user_data

        # Set up default valuations
        (tmp_path / "valuations.md").write_text("Chase UR: 1.80 cents\nAmex MR: 1.75 cents\n")

        # Set up custom valuation that overrides one
        save_user_data({"wallet": [], "custom_valuations": {"chase_ur": 2.00}, "credits": {}})

        result = get_user_valuations()
        assert result["chase_ur"] == 2.00  # Custom override
        assert result["amex_mr"] == 1.75  # Default preserved
