#!/usr/bin/env python
"""Test script for Miles - Validates functionality using llm-tools-server eval framework.

This script uses the llm-tools-server evaluation framework to test Miles functionality
with automated validation, reporting, and performance tracking.
"""

import argparse
import os
import sys
import webbrowser

from llm_tools_server.eval import ConsoleReporter, Evaluator, HTMLReporter, JSONReporter, TestCase

# Test configuration
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_MODEL = "askmiles/miles"
TEST_TIMEOUT = 180  # seconds per test (complex queries with multiple tool calls can take time)

# Test suite - all test cases for Miles
TEST_CASES = [
    TestCase(
        question="can you give me a run down of the credits on the new CSR",
        description="Get detailed credit information for Chase Sapphire Reserve (2025 version)",
        expected_keywords=["sapphire", "credit", "travel"],
        min_response_length=150,
        timeout=TEST_TIMEOUT,
        metadata={"category": "card_info", "tool": "get_credit_card_info"},
    ),
    TestCase(
        question="What's the value of different airline miles?",
        description="Explain airline miles valuations",
        expected_keywords=["value", "cent", "mile"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "valuation", "tool": "knowledge_base"},
    ),
    TestCase(
        question="where can i transfer bilt points",
        description="Find Bilt Rewards transfer partners",
        expected_keywords=["bilt", "transfer", "alaska"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "transfer_partners", "tool": "lookup_transfer_partners"},
    ),
    TestCase(
        question="any cards that give airline status?",
        description="Search for cards offering airline elite status benefits",
        expected_keywords=["airline", "status"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "benefits_search", "tool": "benefits_search"},
    ),
    TestCase(
        question="I'm flying American today. What benefits do I have",
        description="Check user's American Airlines benefits from their cards",
        expected_keywords=["american"],
        min_response_length=50,
        timeout=TEST_TIMEOUT,
        metadata={"category": "user_benefits", "tool": "get_user_data"},
    ),
    TestCase(
        question="which Amex Platinum is the best one in 2025",
        description="Compare different Amex Platinum card variants",
        expected_keywords=["platinum", "amex"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "card_comparison", "tool": "get_credit_card_info"},
    ),
    TestCase(
        question="Which card should I use for restaurants?",
        description="Recommend best card for dining category spending",
        expected_keywords=["dining", "restaurant"],
        min_response_length=50,
        timeout=TEST_TIMEOUT,
        metadata={"category": "recommendation", "tool": "get_user_data"},
    ),
    TestCase(
        question="Help me find a card for dining and travel rewards",
        description="Search for cards with good dining and travel rewards",
        expected_keywords=["dining", "travel", "reward"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "card_search", "tool": "credit_card_search"},
    ),
    TestCase(
        question="What are the top 5 credit card offers right now?",
        description="List current top credit card signup bonuses",
        expected_keywords=["bonus", "offer"],
        min_response_length=150,
        timeout=TEST_TIMEOUT,
        metadata={"category": "top_offers", "tool": "get_top_card_offers"},
    ),
    TestCase(
        question="What airlines can I transfer Chase Ultimate Rewards to?",
        description="List Chase UR transfer partners",
        expected_keywords=["chase", "transfer", "airline"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "transfer_partners", "tool": "lookup_transfer_partners"},
    ),
    TestCase(
        question="What credit cards transfer to United MileagePlus?",
        description="Find cards that can transfer to United",
        expected_keywords=["united", "transfer"],
        min_response_length=50,
        timeout=TEST_TIMEOUT,
        metadata={"category": "transfer_partners", "tool": "lookup_transfer_partners"},
    ),
    TestCase(
        question="Find cards with primary rental car insurance",
        description="Search for cards with primary (not secondary) rental car coverage",
        expected_keywords=["primary", "rental", "car"],
        min_response_length=50,
        timeout=TEST_TIMEOUT,
        metadata={"category": "benefits_search", "tool": "benefits_search"},
    ),
    TestCase(
        question="Which cards offer purchase protection?",
        description="Search for cards with purchase protection benefits",
        expected_keywords=["purchase", "protection"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "benefits_search", "tool": "benefits_search"},
    ),
    TestCase(
        question="What's the best cash back card with no annual fee?",
        description="Find no-annual-fee cash back cards",
        expected_keywords=["cash", "annual fee"],
        min_response_length=50,
        timeout=TEST_TIMEOUT,
        metadata={"category": "card_search", "tool": "credit_card_search"},
    ),
    TestCase(
        question="Compare the transfer options between Chase and Amex",
        description="Compare transfer partners between Chase UR and Amex MR",
        expected_keywords=["chase", "amex", "transfer"],
        min_response_length=150,
        timeout=TEST_TIMEOUT,
        metadata={"category": "transfer_comparison", "tool": "lookup_transfer_partners"},
    ),
    TestCase(
        question="Which card has the highest signup bonus right now?",
        description="Find card with the largest current signup bonus",
        expected_keywords=["bonus", "signup"],
        min_response_length=50,
        timeout=TEST_TIMEOUT,
        metadata={"category": "top_offers", "tool": "get_top_card_offers"},
    ),
    TestCase(
        question="What are the best business card bonuses?",
        description="List top business credit card offers",
        expected_keywords=["business", "bonus"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "top_offers", "tool": "get_top_card_offers"},
    ),
    TestCase(
        question="Top personal card offers right now?",
        description="List top personal credit card offers",
        expected_keywords=["personal", "bonus", "offer"],
        min_response_length=100,
        timeout=TEST_TIMEOUT,
        metadata={"category": "top_offers", "tool": "get_top_card_offers"},
    ),
]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Miles functionality using llm-tools-server eval framework")
    parser.add_argument(
        "--url",
        default=DEFAULT_API_URL,
        help=f"API base URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print full responses for all tests",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        help="Number of tests to run (default: all)",
    )
    parser.add_argument(
        "--html",
        type=str,
        help="Generate HTML report at specified path",
    )
    parser.add_argument(
        "--json",
        type=str,
        help="Generate JSON report at specified path",
    )

    args = parser.parse_args()

    # Select tests to run
    tests_to_run = TEST_CASES[: args.count] if args.count else TEST_CASES

    # Initialize evaluator
    evaluator = Evaluator(
        api_url=args.url,
        model=args.model,
        stream=False,
    )

    # Check API health
    print("Miles Test Suite")
    print("=" * 80)
    print(f"\nAPI URL: {args.url}")
    print(f"Model: {args.model}")
    print(f"Tests to run: {len(tests_to_run)}")
    print("\nChecking API health...")

    if not evaluator.check_health():
        print("\n✗ Miles API is not running or not healthy")
        print("\nPlease start Miles with: uv run python miles.py")
        return 1

    print("✓ API is healthy\n")

    # Run tests with real-time progress
    print("=" * 80)
    print(f"Running {len(tests_to_run)} Tests")
    print("=" * 80)
    print()

    results = []
    for i, test_case in enumerate(tests_to_run, 1):
        print(f"Test {i}/{len(tests_to_run)}: {test_case.description}")
        print(f'Question: "{test_case.question}"')
        print("Running...", end="", flush=True)

        # Run single test
        test_results = evaluator.run_tests([test_case])
        result = test_results[0]
        results.append(result)

        # Print result immediately
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        status_color = "\033[92m" if result.passed else "\033[91m"
        reset_color = "\033[0m"
        print(f"\r{status_color}{status}{reset_color} ({result.response_time:.2f}s)")

        # Show failure details immediately
        if not result.passed:
            if hasattr(result, "validation_errors") and result.validation_errors:
                for error in result.validation_errors:
                    print(f"  - {error}")
            if hasattr(result, "response") and result.response:
                print(f"\nResponse:\n{result.response}\n")

        print()

    # Generate final summary report
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    console_reporter = ConsoleReporter()
    console_reporter.generate(results)

    # Generate HTML report if requested
    if args.html:
        print(f"\nGenerating HTML report: {args.html}")
        html_reporter = HTMLReporter()
        html_reporter.generate(results, args.html, title="Miles Evaluation Results")
        print(f"✓ HTML report saved to {args.html}")

        # Open HTML report in browser
        html_path = os.path.abspath(args.html)
        print("Opening report in browser...")
        webbrowser.open(f"file://{html_path}")

    # Generate JSON report if requested
    if args.json:
        print(f"\nGenerating JSON report: {args.json}")
        json_reporter = JSONReporter()
        json_reporter.generate(results, args.json)
        print(f"✓ JSON report saved to {args.json}")

    # Get summary
    summary = evaluator.get_summary(results)

    # Return exit code based on results
    if summary["failed"] == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
