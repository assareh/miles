# Changelog

All notable changes to Miles will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-08

### Added

- **Top Card Offers Tool**: New `get_top_card_offers` tool to find the best current credit card offers ranked by first-year value estimate. Supports filtering by personal, business, or all cards.
- **Transfer Bonuses Tool**: New `get_transfer_bonuses` tool to view active transfer bonus promotions between credit card points and airline/hotel loyalty programs.
- **Fuzzy Card Name Matching**: Card lookups now use RapidFuzz for intelligent matching. Queries like "Amex Platinum", "American Express Platinum Card", or "Plat" now correctly find "The Platinum Card from American Express".
- **Documentation Search Tool**: Added `doc_search` tool (requires RAG to be enabled) for searching indexed documentation.
- **Periodic RAG Updates**: When RAG is enabled, documentation index can now automatically update on a configurable schedule (`RAG_PERIODIC_UPDATE_ENABLED`, `RAG_PERIODIC_UPDATE_INTERVAL_HOURS`).
- **Open Web UI Timeout Setting**: Added `AIOHTTP_CLIENT_TIMEOUT` environment variable to configure request timeouts for tool-heavy queries.
- **LLM Request Debugging**: New `DEBUG_LLM_REQUESTS` option to log all LLM API payloads for debugging.

### Changed

- **Tool Selection Priority**: Documentation search (`doc_search`) is now prioritized over web search for better response quality when RAG is enabled.
- **Migrated to llm-tools-server Framework**: Refactored to use the llm-tools-server framework for improved maintainability and features.

### Fixed

- **Config Import Bug**: Fixed `module 'config' has no attribute 'DATA_DIR'` error in data_storage.py that caused all tool calls to fail.
- **Card Matching Reliability**: Resolved issues where the LLM would fail to find cards due to name variations (e.g., "American Express Platinum Card" vs "The Platinum Card from American Express").

### Dependencies

- Added `rapidfuzz>=3.0.0` for fuzzy string matching.

## [0.1.0] - 2025-11-15

### Added

- Initial release of Miles
- Credit card information lookup with comprehensive database
- Transfer partner lookup with valuations
- Benefits search across all cards
- User wallet and custom valuations support
- Automatic data updates from updater service
- Open Web UI integration for chat interface
- OpenAI-compatible API endpoints
- RAG support for documentation search (optional)
- LM Studio and Ollama backend support
- Comprehensive test suite
