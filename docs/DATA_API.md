# Data API Specification

This document describes the API that Miles uses to fetch credit card data. You can self-host this API to maintain your own data or if the default service becomes unavailable.

## Configuration

Set the `DATA_API_URL` environment variable to point to your data API service:

```bash
DATA_API_URL=https://your-api.example.com
```

Set to an empty string to disable automatic updates entirely (offline mode):

```bash
DATA_API_URL=
```

## API Endpoints

### GET /api/public/exports/status

Returns the current status of all available datasets, including version information for cache invalidation.

**Response:**

```json
{
  "version": "abc123def456",
  "datasets": {
    "credit_cards": {
      "available": true,
      "last_modified": "2025-01-15T10:30:00Z"
    },
    "transfer_partners": {
      "available": true,
      "last_modified": "2025-01-15T10:30:00Z"
    },
    "valuations": {
      "available": true,
      "last_modified": "2025-01-15T10:30:00Z"
    }
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Global version hash. When this changes, clients should check for updates. |
| `datasets` | object | Status of each dataset type |
| `datasets.*.available` | boolean | Whether this dataset is ready for download |
| `datasets.*.last_modified` | string | ISO 8601 timestamp of last update |

---

### GET /api/public/exports/credit_cards

Returns the credit card database as JSON.

**Response:** Array of credit card objects

```json
[
  {
    "Card Name": "Chase Sapphire Preferred Credit Card",
    "Issuer": "Chase",
    "Annual Fee": "$95",
    "Rewards Program": "Chase Ultimate Rewards",
    "Rewards Rate": "5x on travel through Chase, 3x on dining, 2x on other travel",
    "Sign-Up Bonus": "75,000 points after $4,000 spend in 3 months",
    "First Year Value": "$1,500",
    "Credits": [],
    "Benefits": {
      "Travel": ["Primary rental car insurance", "Trip delay insurance"],
      "Purchase": ["Purchase protection", "Extended warranty"],
      "Other": []
    },
    "Pros": ["Flexible point transfers", "No foreign transaction fees"],
    "Cons": ["Annual fee"],
    "Best For": "Travelers who want flexible rewards",
    "URL": "https://example.com/card-details"
  }
]
```

**Required fields:** `Card Name`, `Issuer`

**Optional fields:** All others (Miles gracefully handles missing data)

**Headers:**
- Supports `If-Modified-Since` for conditional requests
- Returns `304 Not Modified` if data hasn't changed

---

### GET /api/public/exports/transfer_partners

Returns transfer partner relationships as JSON.

**Response:**

```json
{
  "programs": {
    "Chase Ultimate Rewards": {
      "partners": [
        {
          "Partner": "United MileagePlus",
          "Type": "Airline",
          "Transfer Ratio": "1:1",
          "Transfer Time": "Instant"
        },
        {
          "Partner": "Hyatt",
          "Type": "Hotel",
          "Transfer Ratio": "1:1",
          "Transfer Time": "Instant"
        }
      ]
    },
    "Amex Membership Rewards": {
      "partners": [...]
    }
  },
  "transfer_bonuses": [
    {
      "From": "Amex Membership Rewards",
      "To": "British Airways Avios",
      "Bonus": "30%",
      "Expires": "2025-03-31",
      "Notes": "Register required"
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `programs` | object | Map of rewards program name to partner list |
| `programs.*.partners` | array | List of transfer partners |
| `programs.*.partners[].Partner` | string | Partner program name |
| `programs.*.partners[].Type` | string | "Airline" or "Hotel" |
| `programs.*.partners[].Transfer Ratio` | string | e.g., "1:1", "1:1.5" |
| `programs.*.partners[].Transfer Time` | string | e.g., "Instant", "1-2 days" |
| `transfer_bonuses` | array | Currently active transfer bonus promotions |

---

### GET /api/public/exports/valuations

Returns point/mile valuations as JSON.

**Response:** JSON object

```json
{
  "version": "1.0",
  "unit": "cents_per_point",
  "valuations": {
    "chase_ultimate_rewards": {
      "value": 1.5,
      "display_name": "Chase Ultimate Rewards",
      "category": "Transferable Points"
    },
    "amex_membership_rewards": {
      "value": 1.5,
      "display_name": "American Express Membership Rewards",
      "category": "Transferable Points"
    },
    "united_mileageplus": {
      "value": 1.3,
      "display_name": "United MileagePlus",
      "category": "Airline Miles"
    },
    "world_of_hyatt": {
      "value": 1.8,
      "display_name": "World of Hyatt",
      "category": "Hotel Points"
    }
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Format version (currently "1.0") |
| `unit` | string | Value unit (always "cents_per_point") |
| `valuations` | object | Map of program_key to valuation data |
| `valuations.*.value` | number | Valuation in cents per point |
| `valuations.*.display_name` | string | Human-readable program name |
| `valuations.*.category` | string | "Transferable Points", "Airline Miles", "Hotel Points", or "Other Loyalty Programs" |

**Program Keys:**

Program keys are snake_case identifiers (e.g., `chase_ultimate_rewards`, `world_of_hyatt`). These keys are stable and should be used in user configuration files for custom valuations.

---

## Caching Behavior

Miles implements smart caching to minimize requests:

1. On startup, Miles calls `/api/public/exports/status`
2. Compares the `version` field to cached version
3. If versions match, skips all downloads
4. If versions differ, checks each dataset's `last_modified`
5. Only downloads datasets that have changed
6. Stores cache metadata in `data/.download_cache.json`

Miles also checks for updates every 24 hours while running.

---

## Implementing Your Own Data API

A minimal implementation needs to:

1. Serve the three endpoints above
2. Return proper JSON/Markdown content
3. Include `last_modified` timestamps in status response
4. Update the `version` field when any dataset changes

### Example: Static File Server

You can use any static file server with a simple wrapper:

```python
# Minimal Flask example
from flask import Flask, jsonify, send_file
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
DATA_DIR = "./data"

def get_file_mtime(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return datetime.fromtimestamp(os.path.getmtime(path)).isoformat() + "Z"
    return None

def get_version():
    # Hash of all file mtimes
    mtimes = "".join([
        get_file_mtime("credit_cards.json") or "",
        get_file_mtime("transfer_partners.json") or "",
        get_file_mtime("valuations.json") or "",
    ])
    return hashlib.md5(mtimes.encode()).hexdigest()

@app.route("/api/public/exports/status")
def status():
    return jsonify({
        "version": get_version(),
        "datasets": {
            "credit_cards": {
                "available": os.path.exists(f"{DATA_DIR}/credit_cards.json"),
                "last_modified": get_file_mtime("credit_cards.json")
            },
            "transfer_partners": {
                "available": os.path.exists(f"{DATA_DIR}/transfer_partners.json"),
                "last_modified": get_file_mtime("transfer_partners.json")
            },
            "valuations": {
                "available": os.path.exists(f"{DATA_DIR}/valuations.json"),
                "last_modified": get_file_mtime("valuations.json")
            }
        }
    })

@app.route("/api/public/exports/credit_cards")
def credit_cards():
    return send_file(f"{DATA_DIR}/credit_cards.json", mimetype="application/json")

@app.route("/api/public/exports/transfer_partners")
def transfer_partners():
    return send_file(f"{DATA_DIR}/transfer_partners.json", mimetype="application/json")

@app.route("/api/public/exports/valuations")
def valuations():
    return send_file(f"{DATA_DIR}/valuations.json", mimetype="application/json")

if __name__ == "__main__":
    app.run(port=8080)
```

---

## Data Sources

If you're building your own dataset, here are some public sources:

- **Credit card information**: Card issuer websites, NerdWallet, The Points Guy, Doctor of Credit
- **Transfer partners**: Published on each bank's rewards portal
- **Valuations**: The Points Guy monthly valuations, Frequent Miler, community consensus

Note: Respect copyright and terms of service when aggregating data.
