# Miles Testing Guide

Comprehensive testing and validation for the Miles project using the **llm-tools-server evaluation framework**.

## Quick Start

```bash
# Start Miles (in one terminal)
uv run python miles.py

# Run tests (in another terminal)
uv run python test_miles.py
```

## Test Framework

The `test_miles.py` script uses the **llm-tools-server evaluation framework** to provide professional-grade testing capabilities. This framework was specifically designed for LLM API testing and includes:

- **TestCase class**: Define test scenarios with validation criteria
- **Evaluator class**: Orchestrate test execution and health checks
- **Multiple Reporters**: Generate console, HTML, and JSON reports

### Features

- **Automated Testing**: Runs 16 test questions covering all major features
- **Smart Validation**: Checks responses for expected keywords, length, and custom validators
- **Multiple Report Formats**: Console output, HTML reports, and JSON exports
- **Performance Tracking**: Measures response time for each test
- **Metadata Tagging**: Organize tests by category and expected tool usage
- **Flexible**: Supports verbose mode, custom API URLs, and partial test runs

### Usage

#### Basic Test Run

```bash
uv run python test_miles.py
```

This runs all tests with console output. Only failed tests show their full responses.

#### Verbose Mode

```bash
uv run python test_miles.py --verbose
```

Note: The `--verbose` flag is currently accepted but not fully implemented. By default, the test framework shows full responses only for failed tests. To see all responses, review the HTML report generated with `--html`.

#### Generate HTML Report

```bash
uv run python test_miles.py --html results.html
```

Generates a visual HTML report with color-coded results, perfect for sharing or archiving.

#### Generate JSON Report

```bash
uv run python test_miles.py --json results.json
```

Exports results in JSON format for programmatic analysis or CI/CD integration.

#### Custom API URL

```bash
uv run python test_miles.py --url http://localhost:9000
```

Test against a different Miles instance.

#### Run Partial Tests

```bash
uv run python test_miles.py --count 5
```

Run only the first 5 tests (useful for quick validation).

#### Combine Options

```bash
uv run python test_miles.py --verbose --html results.html --json results.json
```

Run with verbose output and generate both HTML and JSON reports.

### Test Cases

The test suite covers all major Miles features:

#### 1. Benefits Search Tests

- **Airline Status**: "any cards that give airline status?"
  - Tests `benefits_search` tool for airline elite status
  - Expects mentions of airline status benefits

- **Primary Rental Car Insurance**: "Find cards with primary rental car insurance"
  - Tests `benefits_search` for specific protection type
  - Expects "primary" coverage distinction

- **Purchase Protection**: "Which cards offer purchase protection?"
  - Tests `benefits_search` for common protection benefit
  - Expects multiple card matches

#### 2. Card Information Tests

- **Specific Card Details**: "can you give me a run down of the credits on the new CSR"
  - Tests `get_credit_card_info` for Chase Sapphire Reserve (2025 Relaunch)
  - Expects detailed credit breakdown ($300 travel, $300 dining, $300 entertainment, etc.)

- **Card Comparison**: "which Amex Platinum is the best one in 2025"
  - Tests ability to compare multiple card variants
  - Expects analysis of different Amex Platinum options

#### 3. Search and Recommendation Tests

- **Category Spending**: "Which card should I use for restaurants?"
  - Tests `get_user_data` and card recommendation logic
  - Expects dining category analysis

- **Multi-Category Search**: "Help me find a card for dining and travel rewards"
  - Tests `credit_card_search` with multiple criteria
  - Expects cards strong in both categories

- **Top Offers**: "What are the top 5 credit card offers right now?"
  - Tests ability to rank and present best current bonuses
  - Expects multiple cards with bonus details

- **Zero Annual Fee**: "What's the best cash back card with no annual fee?"
  - Tests search filtering by annual fee
  - Expects no-fee card recommendations

- **Highest Bonus**: "Which card has the highest signup bonus right now?"
  - Tests bonus comparison across all cards
  - Expects specific card with largest bonus

#### 4. Transfer Partner Tests

- **Transfer From**: "What airlines can I transfer Chase Ultimate Rewards to?"
  - Tests `lookup_transfer_partners` (from Chase UR)
  - Expects list of airline transfer partners with ratios

- **Transfer To**: "What credit cards transfer to United MileagePlus?"
  - Tests `lookup_transfer_partners` (to United)
  - Expects cards that can transfer to United

- **Transfer Comparison**: "Compare the transfer options between Chase and Amex"
  - Tests multiple `lookup_transfer_partners` calls
  - Expects comparative analysis of both programs

#### 5. Valuation Tests

- **Miles Valuations**: "What's the value of different airline miles?"
  - Tests knowledge of valuation data
  - Expects cents-per-point values for airlines

#### 6. User-Specific Tests

- **Personal Benefits**: "I'm flying American today. What benefits do I have"
  - Tests `get_user_data` to check user's wallet
  - Expects American Airlines-specific benefits from user's cards

### Understanding Results

#### Output Format

```
Test 1/15: Search for cards offering airline elite status benefits
Question: "any cards that give airline status?"
✓ PASSED (3.45s)
```

- **✓ PASSED**: Test met all validation criteria
- **✗ FAILED**: Test did not meet validation criteria
- **Response time**: How long Miles took to respond

#### Validation Criteria

Each test validates:

1. **Response Length**: Minimum character count (ensures substantive answer)
2. **Expected Keywords**: Key terms that should appear in the response
3. **Response Quality**: No error messages or empty responses

#### Failed Test Example

```
Test 5/15: Recommend best card for dining category spending
Question: "Which card should I use for restaurants?"
✗ FAILED (2.13s)
  - Missing expected keywords: dining

Response:
I can help you with that. Let me check your wallet...
```

This indicates Miles didn't mention "dining" in the response, which is unexpected.

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed or were skipped

Use in CI/CD:

```bash
uv run python test_miles.py || echo "Tests failed!"
```

## Expected Test Results

### What to Expect

With a properly running Miles instance and a well-performing LLM backend:

- **Success Rate**: 80-100% (depending on LLM capabilities)
- **Response Times**: 2-10 seconds per test (varies by backend)
- **Total Runtime**: ~2-5 minutes for full suite

### Common Issues

#### API Not Running

```
✗ Miles API is not running or not healthy
Please start Miles with: uv run python miles.py
```

**Solution**: Start Miles in another terminal before running tests.

#### Slow Responses

If tests are timing out (>120 seconds), check:
- Backend LLM is running (Ollama/LM Studio)
- Model is loaded and responding
- System resources (CPU/GPU/memory)

#### Missing Keywords

If tests fail validation:
- Check if the LLM is following tool instructions properly
- Verify data files are up-to-date (`data/credit_cards.json`, etc.)
- Try a different/better model if available

### Test Data Requirements

Tests assume:

1. **Credit Cards Data**: `data/credit_cards.json` is populated
2. **Transfer Partners**: `data/transfer_partners.json` is available
3. **Valuations**: `data/valuations.md` exists
4. **User Data** (optional): `data/user.json` for user-specific tests

Download data files automatically on startup or manually:

```bash
uv run python miles.py  # Downloads on first run
```

## Manual Testing

For interactive testing:

```bash
# Using curl
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "askmiles/miles",
    "messages": [{"role": "user", "content": "What are the best travel cards?"}],
    "stream": false
  }'
```

Or use Open Web UI:

```bash
uv run python miles.py  # Starts Web UI on http://localhost:8001
```

## Debugging Failed Tests

### Enable Tool Debug Logging

```bash
# Set environment variable
export DEBUG_TOOLS=true
export DEBUG_TOOLS_LOG_FILE=tools_debug.log

# Run Miles
uv run python miles.py

# In another terminal, run tests
uv run python test_miles.py

# Check tool execution logs
tail -f tools_debug.log
```

This logs all tool calls and responses in JSON format.

### Verbose Test Output

```bash
uv run python test_miles.py -v
```

Note: Verbose mode is currently not fully implemented. To review all test responses, generate an HTML report with `--html results.html` which includes full responses for all tests.

### Single Question Testing

Use curl or Open Web UI to test individual questions interactively.

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Miles Tests
  run: |
    # Start Miles in background
    uv run python miles.py --no-webui &
    MILES_PID=$!

    # Wait for startup
    sleep 10

    # Run tests
    uv run python test_miles.py

    # Cleanup
    kill $MILES_PID
```

## Test Coverage

The test suite covers:

- ✅ All 6 tools (`get_user_data`, `get_credit_card_info`, `credit_card_search`, `lookup_transfer_partners`, `benefits_search`, `get_current_date`)
- ✅ Search capabilities (benefits, cards, transfers)
- ✅ Data retrieval (card details, user wallet, valuations)
- ✅ Multi-step reasoning (comparisons, recommendations)
- ✅ User-specific queries (benefits based on wallet)

Not covered:

- ❌ Streaming responses (tests use non-streaming mode)
- ❌ Error recovery (invalid inputs, API errors)
- ❌ Concurrent requests
- ❌ Authentication (Miles doesn't require auth)

## Extending Tests

### Adding New Test Cases

To add new test cases, edit `test_miles.py` and add to the `TEST_CASES` list:

```python
from llm_tools_server.eval import TestCase

TEST_CASES.append(
    TestCase(
        question="Your test question here",
        description="What this tests",
        expected_keywords=["keyword1", "keyword2"],
        min_response_length=100,
        timeout=120,
        metadata={"category": "your_category", "tool": "expected_tool"},
    )
)
```

### Using Custom Validators

For advanced validation logic, you can add custom validators:

```python
def validate_card_recommendation(response: str) -> tuple[bool, list[str]]:
    """Validate that response includes specific card details."""
    issues = []

    # Check for card name
    if not any(card in response.lower() for card in ["sapphire", "platinum", "venture"]):
        issues.append("No specific card recommendation found")

    # Check for annual fee mention
    if "annual fee" not in response.lower():
        issues.append("Missing annual fee information")

    return len(issues) == 0, issues

# Use in test case
TestCase(
    question="What's the best travel card?",
    description="Card recommendation test",
    custom_validator=validate_card_recommendation,
    metadata={"category": "recommendation"},
)
```

### Framework Components

The test script uses three main components from `llm-tools-server.eval`:

1. **TestCase**: Defines test criteria
   - `question`: The prompt to send
   - `description`: Human-readable test purpose
   - `expected_keywords`: Words that should appear
   - `unexpected_keywords`: Words that should NOT appear
   - `min_response_length` / `max_response_length`: Size constraints
   - `timeout`: Max wait time (default: 120s)
   - `custom_validator`: Custom validation function
   - `metadata`: Categorization tags

2. **Evaluator**: Executes tests
   - `check_health()`: Verify API is running
   - `run_tests(test_cases)`: Execute test suite
   - `get_summary(results)`: Calculate metrics

3. **Reporters**: Generate output
   - `ConsoleReporter`: Terminal output with colors
   - `HTMLReporter`: Visual web report
   - `JSONReporter`: Machine-readable export

## Troubleshooting

### Tests Pass But Responses Are Low Quality

The test script validates basic criteria (keywords, length) but doesn't assess quality deeply. Review responses manually:

```bash
uv run python test_miles.py --verbose > test_output.txt
```

Then read through `test_output.txt` to assess Miles' actual answers.

### Inconsistent Results

LLM responses can vary. If a test passes sometimes but not always:

1. Check if the model is non-deterministic (temperature > 0)
2. Review the question phrasing - make it more specific
3. Adjust expected keywords to be more flexible

### All Tests Fail

1. Verify Miles is running: `curl http://localhost:8000/health`
2. Check data files exist: `ls -la data/`
3. Test a single question manually with curl
4. Check backend LLM is running and configured correctly

## Performance Benchmarks

Typical performance on different backends:

| Backend | Model | Avg Response Time | Success Rate |
|---------|-------|------------------|--------------|
| Ollama | llama3.1:8b | 3-5s | 85-95% |
| Ollama | qwen2.5:14b | 4-7s | 90-100% |
| LM Studio | various | varies | varies |

Response times and success rates depend heavily on:
- Model capabilities (especially tool calling)
- Hardware (CPU vs GPU)
- System load

## Getting Help

If tests consistently fail or you see unexpected behavior:

1. Check GitHub issues: https://github.com/anthropics/claude-code/issues
2. Review data files for accuracy
3. Test with a known-good LLM model
4. Enable debug logging to see tool execution details

## Framework Documentation

For more details about the llm-tools-server evaluation framework:
- [llm-tools-server GitHub Repository](https://github.com/anthropics/llm-tools-server)
- Framework components: `TestCase`, `Evaluator`, `HTMLReporter`, `JSONReporter`, `ConsoleReporter`
- Advanced features: Custom validators, metadata tagging, multiple report formats

---

**Last Updated**: 2025-11-22
