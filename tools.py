"""Tool definitions for Miles using LangChain framework."""

import json
from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool
from llm_tools_server import BUILTIN_TOOLS, create_web_search_tool

import data_storage
from config import config


@tool
def get_user_data() -> str:
    """Get the user's wallet, point valuations, and merchant credits.

    Returns comprehensive user data including:
    - wallet: List of credit cards the user owns with full details
    - valuations: Point valuations in cents per point
    - credits: Merchant credits and gift cards

    Returns:
        JSON string containing wallet, valuations, and credits
    """
    try:
        wallet = data_storage.get_user_wallet()
        valuations = data_storage.get_user_valuations()
        credits = data_storage.get_user_credits()
        user_data = data_storage.get_user_data()

        result = {
            "wallet": wallet,
            "valuations": {
                "last_updated_utc": user_data.get("last_updated"),
                "unit": "cents_per_point",
                "valuations": valuations,
            },
            "credits": {"last_updated_utc": user_data.get("last_updated"), "credits": credits},
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_valuations(programs: list[str] | None = None) -> str:
    """Get point and mile valuations in cents per point.

    Returns the user's valuations (merged with defaults) for loyalty programs.
    Optionally filter to specific programs.

    Args:
        programs: Optional list of program keys or names to filter
                  (e.g., ["chase_ultimate_rewards", "united_mileageplus"])

    Returns:
        JSON string with valuations in cents per point
    """
    try:
        valuations = data_storage.get_user_valuations()
        valuations_metadata = data_storage.get_valuations_with_metadata()

        # Filter by programs if specified
        if programs:
            if not isinstance(programs, list):
                return json.dumps({"error": "programs must be a list"})

            # Normalize program names for matching
            def normalize_key(s):
                return s.lower().replace(" ", "_").replace("-", "_")

            # Build lookup from normalized key to actual key
            normalized_lookup = {}
            for key in valuations:
                normalized_lookup[normalize_key(key)] = key
                # Also add display name mapping if available
                val_data = valuations_metadata.get("valuations", {}).get(key, {})
                if isinstance(val_data, dict) and val_data.get("display_name"):
                    normalized_lookup[normalize_key(val_data["display_name"])] = key

            filtered_valuations = {}
            for program in programs:
                normalized = normalize_key(program)
                if normalized in normalized_lookup:
                    actual_key = normalized_lookup[normalized]
                    filtered_valuations[actual_key] = valuations[actual_key]

            valuations = filtered_valuations

        result = {
            "last_updated_utc": datetime.now(UTC).isoformat(),
            "unit": "cents_per_point",
            "valuations": valuations,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_credit_card_info(card_name: str) -> str:
    """Get detailed information about a specific credit card.

    Use this tool when you need complete information about a specific card including
    rewards, benefits, fees, and current offers.

    Args:
        card_name: Name of the credit card (e.g., "Chase Sapphire Preferred")

    Returns:
        JSON string with complete card details or error message
    """
    try:
        # Input validation
        if not card_name or not isinstance(card_name, str):
            return json.dumps({"error": "Invalid card name: must be a non-empty string"})

        # Validate length
        if len(card_name) > 200:
            return json.dumps({"error": "Card name too long (max 200 characters)"})

        # Prevent path traversal and other injection attempts
        if any(char in card_name for char in ["../", "..\\", "\0", "\n", "\r"]):
            return json.dumps({"error": "Invalid characters in card name"})

        card = data_storage.get_credit_card_by_name(card_name)

        if not card:
            return json.dumps(
                {"error": f"Card not found: {card_name}", "suggestion": "Please check the card name and try again"}
            )

        return json.dumps(card, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def credit_card_search(query: str, max_results: int = 5, recently_updated: int | None = None) -> str:
    """Search for credit cards based on natural language query.

    Performs keyword-based search across card names, issuers, rewards categories,
    and benefits. Returns ranked results.

    Args:
        query: Natural language search query (e.g., "travel cards", "dining rewards")
        max_results: Maximum number of results to return (default: 5)
        recently_updated: Filter to cards updated within the last N days (e.g., 30 for last month)

    Returns:
        JSON string with search results including match scores and reasons
    """
    try:
        # Input validation
        if not query or not isinstance(query, str):
            return json.dumps({"error": "Invalid query: must be a non-empty string"})

        # Validate query length
        if len(query) > 500:
            return json.dumps({"error": "Query too long (max 500 characters)"})

        # Validate max_results is reasonable
        if not isinstance(max_results, int) or max_results < 1:
            return json.dumps({"error": "max_results must be a positive integer"})

        if max_results > 50:
            max_results = 50  # Cap at 50 to prevent resource exhaustion
        cards = data_storage.get_credit_cards()

        # Filter by recently_updated if specified
        if recently_updated is not None:
            if not isinstance(recently_updated, int) or recently_updated < 1:
                return json.dumps({"error": "recently_updated must be a positive integer"})

            cutoff_date = datetime.now() - timedelta(days=recently_updated)
            filtered_cards = []
            for card in cards:
                last_updated = card.get("last_updated")
                if last_updated:
                    try:
                        # Parse MM/DD/YY format
                        card_date = datetime.strptime(last_updated, "%m/%d/%y")
                        if card_date >= cutoff_date:
                            filtered_cards.append(card)
                    except ValueError:
                        # Skip cards with invalid date format
                        pass
            cards = filtered_cards
        query_lower = query.lower()
        matches = []

        for card in cards:
            score = 0
            match_reasons = []

            # Search in card name
            if query_lower in card.get("card_name", "").lower():
                score += 10
                match_reasons.append("Card name match")

            # Search in issuer
            if query_lower in card.get("issuer", "").lower():
                score += 5
                match_reasons.append("Issuer match")

            # Search in rewards currency
            if query_lower in card.get("rewards_currency", "").lower():
                score += 3
                match_reasons.append("Rewards currency match")

            # Search in reward categories
            for multiplier in card.get("reward_multipliers", []):
                category = multiplier.get("category", "").lower()
                if query_lower in category:
                    score += 2
                    match_reasons.append(f"Category: {multiplier.get('category')}")

            # Search in benefits
            benefits = card.get("benefits", {})

            # Check credits
            for credit in benefits.get("credits", []):
                if query_lower in credit.get("type", "").lower():
                    score += 2
                    match_reasons.append(f"Credit: {credit.get('type')}")

            # Check lounge access
            for lounge in benefits.get("lounge", []):
                if query_lower in lounge.get("type", "").lower():
                    score += 2
                    match_reasons.append(f"Lounge: {lounge.get('type')}")

            # Check card type (personal/business)
            if query_lower in card.get("card_type", "").lower():
                score += 3
                match_reasons.append("Card type match")

            # Add to matches if score > 0
            if score > 0:
                matches.append(
                    {
                        "card_name": card.get("card_name"),
                        "issuer": card.get("issuer"),
                        "rewards_currency": card.get("rewards_currency"),
                        "annual_fee": card.get("annual_fee"),
                        "card_type": card.get("card_type"),
                        "score": score,
                        "match_reasons": match_reasons[:3],  # Top 3 reasons
                    }
                )

        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)

        # Limit results
        matches = matches[:max_results]

        result = {"search_results": matches, "total_results": len(matches), "query": query}

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def lookup_transfer_partners(program_name: str, direction: str = "from") -> str:
    """Look up transfer partners for a loyalty program.

    Use this to find where you can transfer points or miles.

    Args:
        program_name: Name of the loyalty program (e.g., "Chase Ultimate Rewards", "Air France")
        direction: 'from' to find where you can transfer TO, 'to' to find what can transfer TO this program

    Returns:
        JSON string with transfer partner information including ratios and valuations
    """
    try:
        # Input validation
        if not program_name or not isinstance(program_name, str):
            return json.dumps({"error": "Invalid program name: must be a non-empty string"})

        if len(program_name) > 200:
            return json.dumps({"error": "Program name too long (max 200 characters)"})

        # Validate direction is one of the allowed values
        if direction not in ["from", "to"]:
            return json.dumps({"error": "Invalid direction: must be 'from' or 'to'"})

        transfer_data = data_storage.get_transfer_partners()
        valuations = data_storage.get_user_valuations()

        program_name_lower = program_name.lower()

        if direction == "from":
            # Find where you can transfer FROM this program
            for prog_key, partners in transfer_data.items():
                if program_name_lower in prog_key.lower():
                    # Found the source program
                    result_partners = []

                    for partner in partners:
                        loyalty_program = partner.get("Loyalty Program", "")
                        ratio = partner.get("Ratio", 1.0)
                        best = partner.get("Best", False)
                        notes = partner.get("Notes", "")
                        bonus = partner.get("Bonus", "")

                        # Look up valuation for destination
                        dest_key = loyalty_program.lower().replace(" ", "_").replace("-", "_")
                        valuation = valuations.get(dest_key, 1.0)

                        partner_info = {
                            "loyalty_program": loyalty_program,
                            "best": best,
                            "ratio": ratio,
                            "notes": notes,
                            "valuation": valuation,
                            "summary": f"{ratio}:1, {valuation} cents per point",
                        }

                        if bonus:
                            partner_info["bonus"] = bonus
                            # Add bonus_expiration if present
                            bonus_exp = partner.get("bonus_expiration")
                            if bonus_exp:
                                partner_info["bonus_expiration"] = bonus_exp

                        result_partners.append(partner_info)

                    # Sort by valuation descending
                    result_partners.sort(key=lambda x: x["valuation"], reverse=True)

                    result = {
                        "type": "from_program",
                        "source_program": prog_key,
                        "last_updated_utc": datetime.now(UTC).isoformat(),
                        "dest_programs": result_partners,
                    }

                    return json.dumps(result, indent=2)

        else:  # direction == "to"
            # Find what can transfer TO this program
            source_programs = []

            for prog_key, partners in transfer_data.items():
                for partner in partners:
                    loyalty_program = partner.get("Loyalty Program", "")

                    if program_name_lower in loyalty_program.lower():
                        # This program can receive transfers from prog_key
                        ratio = partner.get("Ratio", 1.0)
                        best = partner.get("Best", False)
                        notes = partner.get("Notes", "")
                        bonus = partner.get("Bonus", "")

                        # Look up valuation for source
                        source_key = prog_key.lower().replace(" ", "_").replace("-", "_")
                        source_val = valuations.get(source_key, 1.0)

                        source_info = {
                            "loyalty_program": prog_key,
                            "ratio": ratio,
                            "best": best,
                            "notes": notes,
                            "summary": f"{ratio}:1, {source_val} cents per point",
                        }

                        if bonus:
                            source_info["bonus"] = bonus
                            # Add bonus_expiration if present
                            bonus_exp = partner.get("bonus_expiration")
                            if bonus_exp:
                                source_info["bonus_expiration"] = bonus_exp

                        source_programs.append(source_info)

            if source_programs:
                # Get valuation for destination program
                dest_key = program_name.lower().replace(" ", "_").replace("-", "_")
                dest_valuation = valuations.get(dest_key, 1.0)

                result = {
                    "type": "to_program",
                    "dest_program": program_name,
                    "valuation": dest_valuation,
                    "last_updated_utc": datetime.now(UTC).isoformat(),
                    "source_programs": source_programs,
                }

                return json.dumps(result, indent=2)

        # No results found
        return json.dumps(
            {
                "type": "none",
                "last_updated_utc": datetime.now(UTC).isoformat(),
                "results": [],
                "message": f"No transfer partners found for '{program_name}'",
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_transfer_bonuses(from_program: str = "") -> str:
    """Get all currently active transfer bonuses across all programs.

    Returns transfer partnerships with bonus promotions. Use when users ask
    about current transfer promotions, bonuses, or want to see what deals
    are available right now.

    Args:
        from_program: Optional filter to bonuses from a specific program
                      (e.g., "Chase", "Amex"). Leave empty for all programs.

    Returns:
        JSON string with active transfer bonuses including bonus multipliers,
        effective ratios, and expiration notes.
    """
    try:
        # Input validation
        if from_program and not isinstance(from_program, str):
            return json.dumps({"error": "Invalid from_program: must be a string"})

        if from_program and len(from_program) > 200:
            return json.dumps({"error": "Program name too long (max 200 characters)"})

        transfer_data = data_storage.get_transfer_partners()

        from_program_lower = from_program.lower() if from_program else ""
        bonuses = []

        for source_program, partners in transfer_data.items():
            # Filter by source program if specified
            if from_program_lower and from_program_lower not in source_program.lower():
                continue

            for partner in partners:
                bonus = partner.get("Bonus")

                # Skip if no bonus or bonus is not a valid multiplier
                if bonus is None or bonus == "None" or bonus == "Varies":
                    continue

                # Ensure bonus is a number
                if not isinstance(bonus, (int, float)):
                    continue

                # Skip if bonus is 1.0 or less (no actual bonus)
                if bonus <= 1.0:
                    continue

                loyalty_program = partner.get("Loyalty Program", "")
                ratio = partner.get("Ratio", 1.0)
                notes = partner.get("Notes", "")

                # Calculate bonus percentage
                bonus_pct = (bonus - 1.0) * 100

                bonus_info = {
                    "from_program": source_program,
                    "to_program": loyalty_program,
                    "bonus_multiplier": bonus,
                    "bonus_percentage": f"{bonus_pct:.0f}%",
                    "normal_ratio": f"{ratio}:1",
                    "effective_ratio": f"{ratio}:{bonus * ratio}",
                    "notes": notes,
                }

                # Add bonus_expiration if present
                bonus_exp = partner.get("bonus_expiration")
                if bonus_exp:
                    bonus_info["bonus_expiration"] = bonus_exp

                bonuses.append(bonus_info)

        # Sort by bonus percentage descending
        bonuses.sort(key=lambda x: x["bonus_multiplier"], reverse=True)

        result = {
            "bonuses": bonuses,
            "count": len(bonuses),
            "last_updated_utc": datetime.now(UTC).isoformat(),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_top_card_offers(n: int = 5, card_type: str = "all") -> str:
    """Get the top N credit card offers sorted by First Year Value Estimate.

    Use this when users ask about best current credit card offers, top sign-up
    bonuses, or highest value cards to apply for. Returns cards ranked by their
    first year value estimate.

    Args:
        n: Number of top offers to return (default: 5)
        card_type: Filter by 'business', 'personal', or 'all' (default: 'all')

    Returns:
        JSON string with 'offers' key containing list of top card offers
    """
    try:
        # Input validation
        if not isinstance(n, int) or n < 1:
            return json.dumps({"error": "n must be a positive integer"})

        if n > 50:
            n = 50  # Cap at 50 to prevent resource exhaustion

        if card_type not in ["business", "personal", "all"]:
            return json.dumps({"error": "card_type must be 'business', 'personal', or 'all'"})

        cards = data_storage.get_credit_cards()
        offers = []

        for card in cards:
            # Filter by card type
            dataset_card_type = card.get("card_type", "").lower()
            if card_type == "business" and dataset_card_type != "business":
                continue
            if card_type == "personal" and dataset_card_type != "personal":
                continue

            # Must have a first year value estimate
            fyve = card.get("first_year_value_estimate")
            if fyve is None:
                continue

            try:
                fyve_num = float(fyve)
            except (ValueError, TypeError):
                continue

            offers.append(
                {
                    "card_name": card.get("card_name"),
                    "issuer": card.get("issuer"),
                    "first_year_value_estimate": fyve_num,
                    "sign_up_bonus": card.get("sign_up_bonus"),
                    "annual_fee": card.get("annual_fee"),
                    "application_link": card.get("application_link"),
                    "rewards_currency_type": card.get("rewards_currency"),
                    "benefits": card.get("benefits"),
                    "fm_mini_review": card.get("fm_mini_review"),
                }
            )

        # Sort by first year value, descending
        offers.sort(key=lambda x: x["first_year_value_estimate"], reverse=True)

        result = {"offers": offers[:n]}
        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def benefits_search(query: str) -> str:
    """Search for credit cards that offer a specific benefit.

    Use this to find cards with specific perks like lounge access, credits,
    protections, or elite status.

    Args:
        query: Benefit to search for (e.g., "Priority Pass", "cell phone protection", "lounge access")

    Returns:
        JSON string with matching cards and their benefits
    """
    try:
        # Input validation
        if not query or not isinstance(query, str):
            return json.dumps({"error": "Invalid query: must be a non-empty string"})

        if len(query) > 500:
            return json.dumps({"error": "Query too long (max 500 characters)"})

        cards = data_storage.get_credit_cards()
        query_lower = query.lower()
        matches = []

        for card in cards:
            benefits = card.get("benefits", {})
            matched = False

            # Search in credits
            for credit in benefits.get("credits", []):
                if query_lower in credit.get("type", "").lower():
                    matched = True
                    break

            # Search in lounge access
            if not matched:
                for lounge in benefits.get("lounge", []):
                    if query_lower in lounge.get("type", "").lower():
                        matched = True
                        break

            # Search in other benefits
            if not matched:
                for other in benefits.get("other", []):
                    if query_lower in other.lower():
                        matched = True
                        break

            # Search in protections
            if not matched:
                protections = benefits.get("protections", {})
                for prot_category in ["purchase_protections", "travel_protections", "insurance_protections"]:
                    for prot in protections.get(prot_category, []):
                        prot_type = prot.get("type", "").lower()
                        prot_desc = prot.get("description", "").lower()
                        if query_lower in prot_type or query_lower in prot_desc:
                            matched = True
                            break
                    if matched:
                        break

            # Search in elite status - use structured data properly
            if not matched:
                status = benefits.get("status", {})

                # Map query terms to status categories
                category_keywords = {
                    "hotel": "hotel_elite_status",
                    "airline": "airline_elite_status",
                    "rental": "rental_car_elite_status",
                    "car": "rental_car_elite_status",
                }

                # Check if query is asking for a specific status category
                query_words = query_lower.split()
                target_categories = []
                remaining_words = []

                for word in query_words:
                    if word in category_keywords:
                        target_categories.append(category_keywords[word])
                    elif word not in ["elite", "status"]:  # Skip structural words
                        remaining_words.append(word)

                # If query contains category keywords (like "airline" or "hotel"),
                # return ALL cards with that status type (not just keyword-matched ones)
                if target_categories:
                    for category in target_categories:
                        if status.get(category) and len(status.get(category, [])) > 0:
                            matched = True
                            break
                # If no specific category but query contains "status" or "elite",
                # check if card has ANY elite status
                elif any(word in query_words for word in ["status", "elite"]):
                    for status_category in [
                        "hotel_elite_status",
                        "airline_elite_status",
                        "rental_car_elite_status",
                        "other_elite_status",
                    ]:
                        if status.get(status_category) and len(status.get(status_category, [])) > 0:
                            # If there are remaining search words, do keyword match
                            if remaining_words:
                                for stat in status.get(status_category, []):
                                    stat_text = f"{stat.get('program', '')} {stat.get('tier', '')} {stat.get('description', '')}".lower()
                                    if any(word in stat_text for word in remaining_words):
                                        matched = True
                                        break
                            else:
                                # No additional keywords - match any card with status
                                matched = True
                                break
                        if matched:
                            break
                else:
                    # Fallback to keyword search for non-status queries
                    for status_category in [
                        "hotel_elite_status",
                        "airline_elite_status",
                        "rental_car_elite_status",
                        "other_elite_status",
                    ]:
                        for stat in status.get(status_category, []):
                            if query_lower in str(stat).lower():
                                matched = True
                                break
                        if matched:
                            break

            if matched:
                matches.append(
                    {
                        "card_name": card.get("card_name"),
                        "issuer": card.get("issuer"),
                        "rewards_currency": card.get("rewards_currency"),
                        "annual_fee": card.get("annual_fee"),
                        "foreign_transaction_fee": card.get("foreign_transaction_fee"),
                        "fm_mini_review": card.get("fm_mini_review"),
                        "benefits": benefits,
                        "card_type": card.get("card_type"),
                        "last_updated_utc": card.get("last_updated_utc"),
                    }
                )

        result = {
            "matches": matches,
            "query": query,
            "total_matches": len(matches),
            "last_updated_utc": datetime.now(UTC).isoformat(),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


# RAG documentation search
_doc_index = None
_doc_search_tool = None


def initialize_rag_at_startup() -> None:
    """Initialize RAG index at startup if enabled.

    This ensures the index is built before the first request,
    avoiding delays for the first user. Creates a doc_search tool
    that the model can use to search documentation.
    """
    if not config.RAG_ENABLED:
        print("RAG disabled (set RAG_ENABLED=true to enable)")
        return

    try:
        from llm_tools_server import create_doc_search_tool
        from llm_tools_server.rag import DocSearchIndex, RAGConfig

        global _doc_index, _doc_search_tool

        # Validate that RAG sources are configured
        if not config.RAG_DOC_SOURCES or not config.RAG_DOC_SOURCES[0]:
            print("\nWarning: RAG_ENABLED=true but RAG_DOC_SOURCES not configured")
            print("  Set RAG_DOC_SOURCES in .env (comma-separated URLs)")
            return

        print("")
        print("=" * 60)
        print("⏳ PLEASE WAIT: Loading indexes may take a few minutes")
        print("=" * 60)
        print("")
        print("Initializing documentation search index...")
        print(f"  Sources: {', '.join(config.RAG_DOC_SOURCES)}")

        rag_config = RAGConfig(
            base_url=config.RAG_DOC_SOURCES[0],
            cache_dir=config.RAG_CACHE_DIR,
            manual_urls=config.RAG_DOC_SOURCES[1:] if len(config.RAG_DOC_SOURCES) > 1 else [],
            manual_urls_only=False,
            max_crawl_depth=config.RAG_MAX_CRAWL_DEPTH,
            rate_limit_delay=config.RAG_RATE_LIMIT_DELAY,
            max_workers=config.RAG_MAX_WORKERS,
            max_pages=config.RAG_MAX_PAGES,
            url_include_patterns=config.RAG_URL_INCLUDE_PATTERNS,
            url_exclude_patterns=config.RAG_URL_EXCLUDE_PATTERNS,
            hybrid_bm25_weight=config.RAG_BM25_WEIGHT,
            hybrid_semantic_weight=config.RAG_SEMANTIC_WEIGHT,
            search_top_k=config.RAG_TOP_K,
            rerank_enabled=config.RAG_RERANK_ENABLED,
            embedding_model=config.RAG_EMBEDDING_MODEL,
            update_check_interval_hours=config.RAG_UPDATE_INTERVAL_HOURS,
            # Periodic updates for long-running applications
            periodic_update_enabled=config.RAG_PERIODIC_UPDATE_ENABLED,
            periodic_update_interval_hours=config.RAG_PERIODIC_UPDATE_INTERVAL_HOURS,
        )

        _doc_index = DocSearchIndex(rag_config)

        if _doc_index.needs_update():
            print("Building RAG index (this may take a few minutes)...")
            _doc_index.crawl_and_index()
            print("✓ RAG index built successfully")
        else:
            print("Loading cached RAG index...")
            _doc_index.load_index()
            print("✓ RAG index loaded successfully")

        # Create the doc_search tool using llm-tools-server's factory function
        _doc_search_tool = create_doc_search_tool(
            _doc_index,
            name="doc_search",
            description=(
                "Search 16,000+ indexed documents from trusted credit card and travel rewards blogs. "
                "ALWAYS use this BEFORE web search. This is your PRIMARY knowledge base for: "
                "redemption strategies, award booking tips, program policies (cancellation fees, change fees, etc.), "
                "airline/hotel program nuances, and 'how to' questions. Try 1-2 different search queries "
                "with varied keywords before considering web search."
            ),
        )
        print("✓ doc_search tool enabled")

        # Log periodic update status
        if config.RAG_PERIODIC_UPDATE_ENABLED:
            print(f"✓ Periodic updates enabled (every {config.RAG_PERIODIC_UPDATE_INTERVAL_HOURS}h)")

    except ImportError as e:
        print(f"\nWarning: RAG dependencies not available: {e}")
        print("  Install with: uv sync --extra rag")
    except Exception as e:
        print(f"\nError initializing RAG: {e}")


# =============================================================================
# Tool Exports
# =============================================================================

# Create web search tool (requires config for API key)
web_search = create_web_search_tool(config)

# Miles-specific tools
MILES_TOOLS = [
    get_user_data,
    get_valuations,
    get_credit_card_info,
    credit_card_search,
    lookup_transfer_partners,
    get_transfer_bonuses,
    get_top_card_offers,
    benefits_search,
]


def get_all_tools():
    """Get all available tools, including dynamically initialized ones.

    Combines:
    - BUILTIN_TOOLS from llm-tools-server (get_current_datetime, calculate, etc.)
    - Miles-specific tools (credit card tools)
    - Config-dependent tools (web_search)
    - Dynamically initialized tools (doc_search if RAG enabled)
    """
    tools = list(BUILTIN_TOOLS)  # Start with builtin tools from llm-tools-server
    tools.extend(MILES_TOOLS)  # Add Miles-specific tools
    tools.append(web_search)  # Add web search (requires config)

    # Add doc search tool if RAG is enabled and initialized
    if _doc_search_tool is not None:
        tools.append(_doc_search_tool)

    return tools


# For backward compatibility - basic tools available at import time
ALL_TOOLS = list(BUILTIN_TOOLS) + MILES_TOOLS + [web_search]
