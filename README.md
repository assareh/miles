<div align="center">
  <img src="branding/miles-logo.png" alt="Miles Logo" width="200"/>
</div>

# Miles Open 💳

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?style=flat&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/assareh)


A privacy-focused, source-available AI assistant for credit card rewards optimization. Miles helps you maximize your points and miles by providing expert advice on card selection, transfer partners, and redemption strategies.

> **License note (important):** Miles Open is released under **CC BY-NC-SA 4.0**.
> - ✅ Personal/non-commercial use is allowed.
> - ❌ Commercial use (including selling, offering as a paid service/SaaS, or using it primarily for commercial advantage) is **not** permitted.
> - 🔁 Derivatives must be licensed under **CC BY-NC-SA 4.0** and must include attribution.

## Features

- **🔒 Fully Private**: Runs entirely on your machine. Your wallet data never leaves your computer.
- **💳 Credit Card Expertise**: Comprehensive database of credit cards, rewards, benefits, and current offers
- **🔄 Auto-Updates**: Credit card data automatically updates every 24 hours from the updater service
- **✈️ Transfer Partners**: Up-to-date information on point transfer options and valuations
- **🎯 Personal Wallet**: Track your cards and get tailored recommendations
- **💰 Custom Valuations**: Set your own point valuations based on your redemption preferences
- **🛠️ Built-in Tools**: Date awareness, benefit search, card matching, web search, and more
- **🎯 Smart Matching**: Fuzzy card name matching understands variations like "Amex Platinum" or "CSP"
- **🔍 RAG Support**: Optional documentation search for enhanced responses (disabled by default)
- **💬 Chat History**: Complete conversation history through Open Web UI
- **🔌 OpenAI Compatible**: Works with LM Studio or Ollama backends

## Quick Start

### Prerequisites

- [LM Studio](https://lmstudio.ai/) or [Ollama](https://ollama.ai/) with a model loaded

### Installation

#### Using uv (recommended - fastest and simplest)

```bash
# Clone the repository
git clone https://github.com/assareh/miles.git
cd miles

# Run the setup script (installs uv, Python, and dependencies)
./setup.sh
```

**What the setup script does:**
- Installs uv (if not already installed)
- Installs Python 3.12.0
- Installs all dependencies including Open Web UI
- Applies Miles branding

#### Manual installation with uv

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/assareh/miles.git
cd miles
uv sync --extra webui
./apply_branding.sh
```

### Running Miles

**Basic usage (default: LM Studio):**
```bash
uv run python miles.py
```

**With Ollama:**
```bash
uv run python miles.py --backend ollama --model openai/gpt-oss-20b
```

**Custom port:**
```bash
uv run python miles.py --port 8080
```

**Without Web UI:**
```bash
uv run python miles.py --no-webui
```

## Configuration

Miles can be configured via:

### 1. Environment Variables (.env file)

Create a `.env` file (use `.env.example` as template):

```bash
# Backend Selection
MILES_BACKEND=lmstudio       # or "ollama"
BACKEND_MODEL=openai/gpt-oss-20b

# Backend Endpoints
LMSTUDIO_ENDPOINT=http://localhost:1234/v1
OLLAMA_ENDPOINT=http://localhost:11434

# Ollama API Key (optional - for web search functionality)
# Get your key from: https://ollama.com
# If not set, web search falls back to DuckDuckGo
OLLAMA_API_KEY=

# Miles Settings
MILES_PORT=8000
MILES_TEMPERATURE=0.0
SYSTEM_PROMPT_PATH=data/system_instruction.md

# Data Configuration
DATA_DIR=data
USER_DATA_FILE=data/user.json
DATA_API_URL=https://api.askmiles.ai

# Debug Settings (optional)
DEBUG_TOOLS=false
DEBUG_TOOLS_LOG_FILE=miles_tools_debug.log
DEBUG_LLM_REQUESTS=false
DEBUG_LLM_REQUESTS_FILE=llm_requests.json

# Open Web UI Settings
WEBUI_NAME=Miles
WEBUI_PORT=8001
WEBUI_AUTH=false
DEFAULT_MODELS=askmiles/miles
AIOHTTP_CLIENT_TIMEOUT=       # Request timeout (blank = no timeout)

# RAG Settings (optional - disabled by default)
# RAG_ENABLED=true
# RAG_DOC_SOURCES=https://example.com/docs
# RAG_CACHE_DIR=doc_index
# RAG_UPDATE_INTERVAL_HOURS=168
```

### 2. Command Line Options

```bash
python miles.py --help

Options:
  --port INTEGER              Port to run Miles on (default: 8000)
  --backend [ollama|lmstudio] Backend to use
  --model TEXT                Model name
  --no-webui                  Don't start Open Web UI
  --debug                     Debug mode
```

## Managing Your Data

### Your Wallet

Edit `data/user.json` to add your credit cards:

```json
{
  "wallet": [
    {
      "card_name": "Chase Sapphire Preferred Credit Card",
      "note": "Personal card for travel"
    },
    {
      "card_name": "American Express Gold Card",
      "note": "For dining and groceries"
    }
  ],
  "custom_valuations": {
    "chase_ultimate_rewards": 1.8,
    "amex_membership_rewards": 1.7
  },
  "credits": {
    "Amazon.com": {
      "added_at": "2025-11-20T21:00:00Z"
    }
  }
}
```

### Custom Valuations

Set your own point valuations in cents per point. Default valuations are loaded from `data/valuations.md`, but you can override them in `user.json`.

### Reference Data

The following files contain the credit card database and transfer partner information:

- `data/credit_cards.json` - Credit card database (auto-downloaded from updater service)
- `data/transfer_partners.json` - Transfer partner information (auto-downloaded)
- `data/valuations.md` - Default point valuations (auto-downloaded)
- `data/system_instruction.md` - System prompt for Miles

**Automatic Updates**: Miles automatically downloads updated credit card data from the updater service on startup and checks for updates every 24 hours while running. This ensures you always have the latest card offers, bonuses, and benefits without manual intervention.

If you need to use custom/offline data, you can modify `DATA_API_URL` in your `.env` file or edit the files directly (they won't be overwritten if the data API is unreachable).

## Automatic Data Updates

Miles keeps your credit card data current with minimal effort:

**On Startup:**
- Downloads latest credit card data, transfer partners, and valuations from the updater service
- Uses smart caching to skip downloads if files are already up-to-date
- Falls back to existing local files if the updater service is unavailable

**While Running:**
- Background thread checks for updates every 24 hours
- Automatically downloads new data when available
- Minimal resource usage (sleeps between checks)

**Smart Caching:**
- Compares file versions and timestamps to avoid unnecessary downloads
- Only downloads files that have actually changed
- Stores cache metadata in `data/.download_cache.json`

**Offline Mode:**
- Works offline with existing data files
- Set `DATA_API_URL` to an empty string to disable updates
- Manually place data files in the `data/` directory

**Self-Hosting:**
- You can run your own updater service by implementing the simple API
- Set `DATA_API_URL` to point to your server
- See [docs/DATA_API.md](docs/DATA_API.md) for the full API specification

## RAG (Retrieval-Augmented Generation)

Miles includes optional RAG support for enhanced responses using documentation search. **RAG is disabled by default** to keep startup fast and dependencies minimal.

### Enabling RAG

To enable RAG, add to your `.env` file:

```bash
# Enable RAG
RAG_ENABLED=true

# Documentation sources (comma-separated URLs)
RAG_DOC_SOURCES=https://example.com/docs,https://another-site.com/guides

# Cache directory (default: doc_index)
RAG_CACHE_DIR=doc_index

# Update check interval in hours (default: 168 = 7 days)
RAG_UPDATE_INTERVAL_HOURS=168
```

### How RAG Works

When enabled:
1. **Startup**: Miles crawls and indexes configured documentation sites
2. **First run**: May take several minutes depending on site size
3. **Subsequent runs**: Uses cached index (updates every 7 days by default)
4. **Queries**: Automatically augments user questions with relevant documentation context

### Advanced RAG Settings

```bash
# Hybrid search weights (must sum to 1.0)
RAG_BM25_WEIGHT=0.4              # Keyword search weight
RAG_SEMANTIC_WEIGHT=0.6          # Semantic search weight

# Search parameters
RAG_TOP_K=5                      # Number of results to retrieve
RAG_RERANK_ENABLED=true          # Enable re-ranking for better results

# Crawling limits
RAG_MAX_CRAWL_DEPTH=2            # Maximum link depth to follow
RAG_MAX_PAGES=500                # Maximum pages to index (or blank for unlimited)
RAG_RATE_LIMIT_DELAY=0.5         # Delay between requests (seconds)
RAG_MAX_WORKERS=3                # Concurrent crawl workers

# URL filtering (regex patterns, comma-separated)
RAG_URL_INCLUDE_PATTERNS=        # Only crawl matching URLs (blank = all)
RAG_URL_EXCLUDE_PATTERNS=.*/category/.*,.*/tag/.*  # Skip matching URLs
```

### Use Cases for RAG

- **Documentation assistants**: Index your product docs, FAQs, or knowledge base
- **Research tools**: Search academic papers or technical documentation
- **Support bots**: Provide context-aware answers from support articles

**Note**: RAG requires additional dependencies (~500MB). Install with:
```bash
uv sync --extra rag
```

## Usage Examples

### With Open Web UI

1. Start Miles: `python miles.py`
2. Open Web UI automatically starts on port 8001
3. Access at `http://localhost:8001`
4. On first visit, create a local admin account
5. Start chatting with Miles!

**Example queries:**
- "Which of my cards should I use for dining?"
- "What's the best travel credit card for 2025?"
- "Where can I transfer Chase Ultimate Rewards points?"
- "Which cards offer Priority Pass lounge access?"
- "What's the current American Express Gold Card bonus?"

### With API Clients

Miles provides an OpenAI-compatible API:

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="askmiles/miles",
    messages=[
        {"role": "user", "content": "What's the best card for groceries?"}
    ]
)

print(response.choices[0].message.content)
```

### With curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "askmiles/miles",
    "messages": [{"role": "user", "content": "Which card should I get for travel?"}]
  }'
```

## Tools

Miles comes with built-in tools that it uses automatically:

### 1. Current Date Tool
Get the current date for time-sensitive offers and bonuses.

### 2. User Data Tool
Access your wallet, valuations, and merchant credits in one call.

### 3. Credit Card Info Tool
Get detailed information about any credit card in the database.

### 4. Credit Card Search Tool
Search for cards by category, issuer, benefits, or rewards program.

### 5. Transfer Partners Tool
Look up where you can transfer points from any program, or what programs transfer to a specific airline/hotel.

### 6. Benefits Search Tool
Find cards that offer specific benefits like lounge access, credits, or protections.

### 7. Top Card Offers Tool
Get the best current credit card offers ranked by first-year value, with options to filter by personal or business cards.

### 8. Transfer Bonuses Tool
View active transfer bonus promotions between credit card points and airline/hotel programs.

### 9. Web Search Tool
Search the web for current information. Uses Ollama search API if `OLLAMA_API_KEY` is set, otherwise falls back to DuckDuckGo.

### 10. Documentation Search Tool (RAG)
When RAG is enabled, search indexed documentation for detailed guides and strategies.

## Customization

### Branding

To add your own Miles logo:

1. Create or obtain your logo in various sizes
2. Save to `branding/favicons/` (see `branding/README.md` for required files)
3. Run `./apply_branding.sh` to apply

### System Prompt

Edit `data/system_instruction.md` to customize Miles' behavior and personality.

## API Endpoints

- `GET /health` - Health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completion (OpenAI-compatible)

## Requirements

- **uv** package manager (installed automatically by setup.sh)
- Python 3.12.0 (managed automatically by uv)
- LM Studio or Ollama with a compatible model
- ~2GB disk space for dependencies

## Troubleshooting

**Miles can't connect to LM Studio/Ollama:**
- Ensure your backend is running
- Verify the endpoint in config matches your backend
- Check that the model name is correct

**Tools not working:**
- Verify the backend model supports function calling
- Check that data files exist in the `data/` directory
- Check the updater service connection if data files are missing

**Data not downloading:**
- Check your internet connection
- Verify `DATA_API_URL` is set correctly in `.env`
- Miles will use existing local files if updater is unavailable
- You can manually place data files in `data/` directory

**Open Web UI won't start:**
- Ensure Python 3.11-3.12 (not 3.14+)
- Install manually: `uv sync --extra webui`
- Or run with `--no-webui` flag

## Testing

Miles includes a comprehensive test suite to validate functionality and build confidence.

### Quick Test

```bash
# Start Miles (in one terminal)
uv run python miles.py

# Run tests (in another terminal)
uv run python test_miles.py
```

### Test Coverage

The test suite (`test_miles.py`) runs 18 test questions covering:

- **Benefits Search**: Airline status, rental car insurance, purchase protection
- **Card Information**: Detailed card queries, credit breakdowns, card comparisons
- **Search & Recommendations**: Category spending, multi-category search, top offers
- **Transfer Partners**: Transfer from/to programs, partner comparisons
- **Valuations**: Miles and points valuations
- **User-Specific**: Personal wallet benefits

### Verbose Mode

```bash
uv run python test_miles.py --verbose
```

Shows full responses for all tests (useful for quality assessment).

### Expected Results

**Note**: Results and timing vary significantly based on your configuration:

- **Backend LLM Speed**: Faster models complete in ~50-70s per test, slower models may take 120-180s
- **RAG Configuration**: Tests without RAG use only web search; with RAG enabled, results and timing will differ
- **Success Rate**: 60-90% (complex queries may timeout on slower backends)
- **Total Runtime**: 15-45 minutes for full suite (depends on LLM processing speed)

**Example with LM Studio (gpt-oss-20b, no RAG):**
- Simple queries: ~50-65 seconds
- Complex multi-tool queries: ~90-180 seconds
- Some timeouts expected on slower systems

For detailed testing documentation, see [TESTING.md](TESTING.md).

## Architecture

```
miles/
├── miles.py              # Main Flask application
├── config.py             # Configuration management
├── tools.py              # Tool definitions (LangChain)
├── data_storage.py       # Local JSON data access
├── test_miles.py         # Test suite for validation
├── pyproject.toml        # Project metadata and dependencies (uv)
├── setup.sh              # Automated setup script
├── apply_branding.sh     # Branding application script
├── lint.sh               # Code formatting and linting
├── README.md             # This file
├── TESTING.md            # Detailed testing guide
├── CLAUDE.md             # Developer guide for Claude/AI assistants
│
├── data/                 # Reference data and user data
│   ├── credit_cards.json        # Auto-downloaded from updater service
│   ├── transfer_partners.json   # Auto-downloaded from updater service
│   ├── valuations.md            # Auto-downloaded from updater service
│   ├── system_instruction.md    # System prompt for Miles
│   ├── user.json                # Your wallet and preferences
│   └── user.json.example
│
├── branding/             # UI customization assets
│   ├── custom.css
│   ├── favicons/
│   ├── carousel_images/
│   └── README.md
│
├── doc_index/            # RAG documentation cache (if enabled)
│
└── .venv/                # Python virtual environment (managed by uv)
```

**Key Dependencies:**
- [llm-tools-server](https://github.com/anthropics/llm-tools-server) - Base server framework
- Flask - Web server
- LangChain - Tool framework
- Open Web UI - Chat interface
- sentence-transformers - RAG embeddings (install with `--extra rag`)
- faiss-cpu - Vector search (install with `--extra rag`)

## Model Recommendations

For best results, use models that support function/tool calling:

- **Recommended**: openai/gpt-oss-20b (default)
- **Alternative**: Any recent Llama 3+ model with tool support
- **Context Length**: Set to maximum supported (128K+ recommended)
- **Temperature**: 0.0 for consistent, factual responses

## Privacy & Security

- **All data stays local**: Your financial data never leaves your machine
- **External calls**: Miles only makes external API calls to:
  - Your local LLM backend (LM Studio/Ollama)
  - The updater service (for public credit card data)
  - Web search APIs (only when using the web search tool, if configured)
- **No tracking**: No analytics or telemetry
- **Your financial data**: Stored only in `data/user.json` on your machine - never sent anywhere
- **No authentication needed**: Runs on localhost only
- **Updater service**: Only downloads public credit card information (offers, benefits, transfer partners) - never accesses your personal data

## Support

If you find Miles helpful, consider supporting its development:

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/assareh)

Your support helps maintain and improve Miles!

## License

Miles Open is source-available and licensed under the Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International License (CC BY-NC-SA 4.0).

In practical terms:
- ✅ You may copy, redistribute, and modify this project for **non-commercial** purposes.
- ✅ You must provide **attribution** and indicate changes.
- 🔁 If you distribute modifications, you must do so under **CC BY-NC-SA 4.0**.
- ❌ You may not use this project for **commercial purposes**, including offering it as a paid product or service.

See the [LICENSE](LICENSE) file for full details. For the human-readable summary, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

---

**Note**: Miles provides information and recommendations based on available data. Always verify current offers and terms directly with card issuers before applying.
