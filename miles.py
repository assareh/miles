"""Miles - A credit card rewards chatbot using LLM API Server."""

import json
import os
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import requests
from dotenv import load_dotenv

# Load .env early so DEBUG_LLM_REQUESTS is available
load_dotenv()

print("Loading Miles...")

from llm_tools_server import LLMServer

from config import config
from tools import ALL_TOOLS, get_all_tools, initialize_rag_at_startup

# Set up LLM request logging hook if enabled
if os.getenv("DEBUG_LLM_REQUESTS", "").lower() == "true":
    _request_log_file = os.getenv("DEBUG_LLM_REQUESTS_FILE", "llm_requests.json")

    def _log_llm_request(backend: str, payload: dict):
        """Log LLM request payload to file (JSON Lines format)."""
        log_entry = {"timestamp": datetime.now().isoformat(), "backend": backend, "payload": payload}
        with open(_request_log_file, "a") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")
        print(f"[DEBUG] LLM request logged to {_request_log_file}")

    config.REQUEST_HOOK = _log_llm_request
    print("[DEBUG] LLM request logging enabled")

# Global variables
_server = None
_update_thread: threading.Thread | None = None
_shutdown_flag = threading.Event()


def _validate_credit_cards_data(data: Any) -> bool:
    """Validate credit_cards.json structure."""
    if not isinstance(data, list):
        return False
    if len(data) > 0:
        sample_card = data[0]
        required_fields = ["card_name", "issuer"]
        if not all(field in sample_card for field in required_fields):
            return False
    return True


def _validate_transfer_partners_data(data: Any) -> bool:
    """Validate transfer_partners.json structure."""
    return isinstance(data, dict)


def _validate_valuations_data(data: Any) -> bool:
    """Validate valuations.json structure."""
    if not isinstance(data, dict):
        return False
    if "valuations" not in data:
        return False
    valuations = data.get("valuations", {})
    if not isinstance(valuations, dict):
        return False
    # Check at least one valuation has expected structure
    if len(valuations) > 0:
        sample_key = next(iter(valuations))
        sample_val = valuations[sample_key]
        # Accept both object format and simple number format
        if isinstance(sample_val, dict):
            if "value" not in sample_val:
                return False
        elif not isinstance(sample_val, (int, float)):
            return False
    return True


def check_data_terms_acceptance() -> bool:
    """Check if user has accepted data usage terms."""
    terms_file = Path(config.DATA_DIR) / ".terms_accepted"

    if terms_file.exists():
        return True

    print("\n" + "=" * 70)
    print("CREDIT CARD DATA USAGE TERMS")
    print("=" * 70)
    print("\nThe credit card data provided by Miles is licensed under")
    print("CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-")
    print("ShareAlike 4.0 International).")
    print("\nYou may:")
    print("  ✓ Use the data for NON-COMMERCIAL purposes only")
    print("  ✓ Share and adapt with proper attribution")
    print("  ✓ Must share derivatives under the same license")
    print("\nYou may NOT:")
    print("  ✗ Use for commercial purposes")
    print("  ✗ Sublicense or sell the data")
    print("\nFull license: https://creativecommons.org/licenses/by-nc-sa/4.0/")
    print("=" * 70)

    response = input("\nAccept these terms? (y/N): ").strip().lower()

    if response in ["y", "yes"]:
        Path(config.DATA_DIR).mkdir(exist_ok=True)
        terms_file.write_text(f"Accepted: {datetime.now().isoformat()}\n")
        print("✓ Terms accepted\n")
        return True
    else:
        print("\n✗ Terms declined. Data download blocked.")
        print("  Miles requires data files to function.")
        print("  You can manually place data files in the data/ directory")
        print("  and set DATA_API_URL to an empty string in .env")
        return False


def download_data_files():
    """Download data files from the updater service on startup with smart caching."""
    if not check_data_terms_acceptance():
        return

    data_files = [
        ("credit_cards", "credit_cards.json"),
        ("transfer_partners", "transfer_partners.json"),
        ("valuations", "valuations.json"),
    ]

    data_dir = Path(config.DATA_DIR)
    data_dir.mkdir(exist_ok=True)

    cache_file = data_dir / ".download_cache.json"

    # Load cached version info
    cached_data = {}
    if cache_file.exists():
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cached_data = {}

    # Check status endpoint for updates
    status_url = f"{config.DATA_API_URL}/api/public/exports/status"
    server_version = ""
    datasets = {}
    offline_mode = False

    try:
        status_response = requests.get(status_url, timeout=10)
        status_response.raise_for_status()
        status_data = status_response.json()

        server_version = status_data.get("version", "")
        cached_version = cached_data.get("version", "")

        if server_version and server_version == cached_version:
            print(f"Data files are up-to-date (version: {server_version[:8]})")
            return

        print("Checking for data file updates...")
        datasets = status_data.get("datasets", {})

    except requests.ConnectionError as e:
        offline_mode = True
        print(f"⚠ Data updater service is offline: {e}")
        print("  Miles will use cached data files if available.")
    except requests.Timeout:
        offline_mode = True
        print("⚠ Data updater service request timed out after 10 seconds")
        print("  Miles will use cached data files if available.")
    except requests.RequestException as e:
        offline_mode = True
        print(f"⚠ Error checking update status: {e}")
        print("  Miles will use cached data files if available.")

    if offline_mode:
        missing_files = []
        for _, filename in data_files:
            file_path = data_dir / filename
            if not file_path.exists():
                missing_files.append(filename)

        if missing_files:
            print(f"\n⚠ WARNING: Offline mode and missing data files: {', '.join(missing_files)}")
            print("  Miles may not function correctly without these files.")
            print("  Please check your internet connection and restart the application.")
        return

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    for dataset_type, filename in data_files:
        file_path = data_dir / filename
        url = f"{config.DATA_API_URL}/api/public/exports/{dataset_type}"

        dataset_info = datasets.get(dataset_type, {})
        if dataset_info.get("available") is False:
            print(f"  ⊘ Skipped {filename} (not generated on server yet)")
            skipped_count += 1
            continue

        headers = {}
        server_last_modified = dataset_info.get("last_modified")
        cached_last_modified = cached_data.get("datasets", {}).get(dataset_type, {}).get("last_modified")

        if server_last_modified and server_last_modified == cached_last_modified and file_path.exists():
            print(f"  ✓ {filename} is up-to-date")
            skipped_count += 1
            continue

        if cached_last_modified:
            try:
                dt = datetime.fromisoformat(cached_last_modified.replace("Z", "+00:00"))
                http_date = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
                headers["If-Modified-Since"] = http_date
            except (ValueError, AttributeError):
                pass

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 304:
                print(f"  ✓ {filename} is up-to-date (304)")
                skipped_count += 1
                continue

            response.raise_for_status()

            if filename.endswith(".json"):
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"  ⚠ Warning: Invalid JSON in {filename}: {e}")
                    failed_count += 1
                    continue

                is_valid = True
                if dataset_type == "credit_cards":
                    is_valid = _validate_credit_cards_data(data)
                elif dataset_type == "transfer_partners":
                    is_valid = _validate_transfer_partners_data(data)
                elif dataset_type == "valuations":
                    is_valid = _validate_valuations_data(data)

                if not is_valid:
                    print(f"  ⚠ Warning: {filename} failed validation, keeping existing file")
                    failed_count += 1
                    continue

                file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            else:
                content = response.text
                if not content or len(content.strip()) < 10:
                    print(f"  ⚠ Warning: {filename} appears empty or invalid, keeping existing file")
                    failed_count += 1
                    continue

                file_path.write_text(content, encoding="utf-8")

            timestamp_display = ""
            if server_last_modified:
                try:
                    dt = datetime.fromisoformat(server_last_modified.replace("Z", "+00:00"))
                    timestamp_display = f" (updated {dt.strftime('%Y-%m-%d %H:%M:%S UTC')})"
                except (ValueError, AttributeError):
                    pass

            print(f"  ↓ Updated {filename}{timestamp_display}")
            downloaded_count += 1

            if "datasets" not in cached_data:
                cached_data["datasets"] = {}
            cached_data["datasets"][dataset_type] = {"last_modified": server_last_modified}

            if not server_last_modified and "Last-Modified" in response.headers:
                cached_data["datasets"][dataset_type] = {"last_modified": response.headers["Last-Modified"]}

        except requests.RequestException as e:
            print(f"  ⚠ Warning: Failed to download {filename}: {e}")
            failed_count += 1

    if server_version:
        cached_data["version"] = server_version

    if cached_data.get("datasets"):
        try:
            cache_file.write_text(json.dumps(cached_data, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"  ⚠ Warning: Could not save cache file: {e}")

    if downloaded_count > 0 or failed_count > 0:
        print(f"  Summary: {downloaded_count} downloaded, {skipped_count} up-to-date, {failed_count} failed")


def periodic_data_update():
    """Background thread that checks for data updates every 24 hours."""
    check_interval = 24 * 60 * 60  # 24 hours

    while not _shutdown_flag.is_set():
        if _shutdown_flag.wait(timeout=check_interval):
            break

        print("\nChecking for data file updates (scheduled check)...")
        try:
            download_data_files()
        except requests.ConnectionError:
            print("  ⚠ Data updater service is offline, will retry in 24 hours")
        except Exception as e:
            print(f"  ⚠ Warning: Scheduled data update failed: {e}")
            print("  Will retry in 24 hours")


def initialize_miles():
    """Initialization hook called during server startup."""
    global _server, _update_thread

    # Download data files
    download_data_files()

    # Initialize RAG index (this creates the doc_search tool)
    if config.RAG_ENABLED:
        initialize_rag_at_startup()
        print()

    # Update the server's tools list with the dynamically created doc_search tool
    if _server is not None:
        _server.tools = get_all_tools()

    # Start background data update thread
    _update_thread = threading.Thread(target=periodic_data_update, daemon=True, name="DataUpdater")
    _update_thread.start()
    print("Background data update thread started (checks every 24 hours)")
    print()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\nShutting down Miles...")

    _shutdown_flag.set()

    if _update_thread and _update_thread.is_alive():
        print("Stopping background update thread...")
        _update_thread.join(timeout=5)

    sys.exit(0)


@click.command()
@click.option("--port", default=config.DEFAULT_PORT, help="Port to run Miles on")
@click.option(
    "--backend", type=click.Choice(["ollama", "lmstudio"]), default=config.BACKEND_TYPE, help="Backend to use"
)
@click.option("--model", default=config.BACKEND_MODEL, help="Model name to use with backend")
@click.option("--no-webui", is_flag=True, help="Don't start Open Web UI")
@click.option("--debug", is_flag=True, help="Run in debug mode")
def main(port: int, backend: str, model: str, no_webui: bool, debug: bool):
    """Start Miles chatbot server."""
    global _server

    # Update config with CLI options
    config.BACKEND_TYPE = backend
    config.BACKEND_MODEL = model

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create server instance
    _server = LLMServer(
        name="Miles",
        model_name=config.MODEL_NAME,
        tools=ALL_TOOLS,
        config=config,
        default_system_prompt="You are Miles, a helpful AI assistant specializing in credit card rewards.",
        init_hook=initialize_miles,
        logger_names=["miles.tools", "tools"],
    )

    # Run the server
    _server.run(
        port=port,
        debug=debug,
        start_webui=not no_webui,
    )


if __name__ == "__main__":
    main()
