"""Local data storage module for Miles.

This module handles reading and writing data from local JSON files,
replacing the Firestore functionality from the cloud version.
"""

import json
import os
from datetime import UTC, datetime
from typing import Any

from rapidfuzz import fuzz, process

from config import config

# RapidFuzz score threshold for confident matches (0-100)
# Default of 85 was determined through casual testing to balance
# flexibility (e.g., "Amex Platinum" → "The Platinum Card from American Express")
# with accuracy (avoiding false matches)
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", "85"))


def _load_json_file(file_path: str) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}") from e


def _save_json_file(file_path: str, data: Any) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_credit_cards() -> list[dict]:
    """Load all credit card data from the local JSON file."""
    file_path = os.path.join(config.DATA_DIR, "credit_cards.json")
    data = _load_json_file(file_path)
    return data if data is not None else []


def get_credit_card_by_name(card_name: str) -> dict | None:
    """Get a specific credit card by name with fuzzy matching.

    Uses RapidFuzz for intelligent matching that handles:
    - Case-insensitive exact matches
    - Partial names (e.g., "Amex Platinum" -> "The Platinum Card from American Express")
    - Common abbreviations and informal names
    """
    cards = get_credit_cards()
    if not cards:
        return None

    card_name_lower = card_name.lower().strip()

    # Build lookup dict: card_name -> card_data
    card_lookup = {card.get("card_name", ""): card for card in cards if card.get("card_name")}
    card_names = list(card_lookup.keys())

    # First, try exact case-insensitive match (fast path)
    for name in card_names:
        if card_name_lower == name.lower():
            return card_lookup[name]

    # Use RapidFuzz for fuzzy matching
    # WRatio automatically picks the best algorithm based on string lengths
    result = process.extractOne(
        card_name,
        card_names,
        scorer=fuzz.WRatio,
        score_cutoff=FUZZY_MATCH_THRESHOLD,
    )

    if result:
        matched_name, _score, _ = result
        return card_lookup[matched_name]

    return None


def get_transfer_partners() -> dict:
    """Load transfer partners data from the local JSON file."""
    file_path = os.path.join(config.DATA_DIR, "transfer_partners.json")
    data = _load_json_file(file_path)
    return data if data is not None else {}


def get_default_valuations() -> dict[str, float]:
    """Load default point valuations from the valuations.json file.

    Returns a dictionary of program_key -> value (in cents).

    The JSON format is:
    {
        "version": "1.0",
        "unit": "cents_per_point",
        "valuations": {
            "chase_ultimate_rewards": {
                "value": 1.5,
                "display_name": "Chase Ultimate Rewards",
                "category": "Transferable Points"
            }
        }
    }
    """
    file_path = os.path.join(config.DATA_DIR, "valuations.json")
    data = _load_json_file(file_path)

    if data is None:
        return {}

    valuations = {}
    raw_valuations = data.get("valuations", {})

    for program_key, val_data in raw_valuations.items():
        if isinstance(val_data, dict):
            # Full object format with value, display_name, category
            valuations[program_key] = val_data.get("value", 0)
        elif isinstance(val_data, (int, float)):
            # Simple value format (backwards compatibility)
            valuations[program_key] = val_data

    return valuations


def get_valuations_with_metadata() -> dict:
    """Load valuations with full metadata (display_name, category).

    Returns the complete valuations data structure for rich display.
    """
    file_path = os.path.join(config.DATA_DIR, "valuations.json")
    data = _load_json_file(file_path)

    if data is None:
        return {"version": "1.0", "unit": "cents_per_point", "valuations": {}}

    return data


def get_user_data() -> dict:
    """Load user data (wallet, credits, custom valuations) from user.json."""
    file_path = config.USER_DATA_FILE
    data = _load_json_file(file_path)

    if data is None:
        # Return empty structure if file doesn't exist
        return {
            "wallet": [],
            "custom_valuations": {},
            "credits": {},
            "last_updated": datetime.now(UTC).isoformat(),
        }

    return data


def save_user_data(data: dict) -> None:
    """Save user data to user.json."""
    data["last_updated"] = datetime.now(UTC).isoformat()
    _save_json_file(config.USER_DATA_FILE, data)


def get_user_wallet() -> list[dict]:
    """Get the user's wallet with full card information."""
    user_data = get_user_data()
    wallet_cards = user_data.get("wallet", [])

    # Enrich wallet cards with full card data
    enriched_wallet = []
    for wallet_entry in wallet_cards:
        card_name = wallet_entry.get("card_name", "")
        card_data = get_credit_card_by_name(card_name)

        if card_data:
            # Merge wallet entry note with card data
            enriched_card = card_data.copy()
            if wallet_entry.get("note"):
                enriched_card["user_note"] = wallet_entry["note"]
            enriched_wallet.append(enriched_card)

    return enriched_wallet


def get_user_valuations() -> dict[str, float]:
    """Get point valuations, merging default valuations with user's custom ones."""
    default_vals = get_default_valuations()
    user_data = get_user_data()
    custom_vals = user_data.get("custom_valuations", {})

    # Merge: custom valuations override defaults
    merged = default_vals.copy()
    merged.update(custom_vals)

    return merged


def get_user_credits() -> dict[str, dict]:
    """Get the user's merchant credits/gift cards."""
    user_data = get_user_data()
    return user_data.get("credits", {})


def add_card_to_wallet(card_name: str, note: str = "") -> bool:
    """Add a card to the user's wallet."""
    # Verify the card exists
    card = get_credit_card_by_name(card_name)
    if not card:
        return False

    user_data = get_user_data()
    wallet = user_data.get("wallet", [])

    # Check if card already in wallet
    for existing_card in wallet:
        if existing_card.get("card_name", "").lower() == card_name.lower():
            # Update note if provided
            if note:
                existing_card["note"] = note
            save_user_data(user_data)
            return True

    # Add new card
    wallet.append({"card_name": card["card_name"], "note": note})  # Use canonical name from data
    user_data["wallet"] = wallet
    save_user_data(user_data)
    return True


def remove_card_from_wallet(card_name: str) -> bool:
    """Remove a card from the user's wallet."""
    user_data = get_user_data()
    wallet = user_data.get("wallet", [])

    card_name_lower = card_name.lower()
    original_length = len(wallet)

    # Filter out the card
    wallet = [c for c in wallet if c.get("card_name", "").lower() != card_name_lower]

    if len(wallet) < original_length:
        user_data["wallet"] = wallet
        save_user_data(user_data)
        return True

    return False


def set_custom_valuation(currency: str, value: float) -> None:
    """Set a custom point valuation for a currency."""
    user_data = get_user_data()
    custom_vals = user_data.get("custom_valuations", {})

    # Normalize currency name to snake_case
    key = currency.lower().replace(" ", "_").replace("-", "_")
    custom_vals[key] = value

    user_data["custom_valuations"] = custom_vals
    save_user_data(user_data)


def add_merchant_credit(merchant: str) -> None:
    """Add a merchant credit/gift card."""
    user_data = get_user_data()
    credits = user_data.get("credits", {})

    credits[merchant] = {"added_at": datetime.now(UTC).isoformat()}

    user_data["credits"] = credits
    save_user_data(user_data)


def remove_merchant_credit(merchant: str) -> bool:
    """Remove a merchant credit/gift card."""
    user_data = get_user_data()
    credits = user_data.get("credits", {})

    if merchant in credits:
        del credits[merchant]
        user_data["credits"] = credits
        save_user_data(user_data)
        return True

    return False
