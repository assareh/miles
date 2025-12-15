#!/bin/bash
set -e

echo "=== Miles Setup Script ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
    echo -e "${GREEN}✓${NC} uv installed successfully"
    echo ""
    echo -e "${YELLOW}Please run this script again or add uv to your PATH:${NC}"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 0
fi

echo -e "${GREEN}✓${NC} uv is installed"
echo ""

# Install Python and dependencies
echo -e "${YELLOW}Installing Python 3.12.0 and dependencies...${NC}"
uv sync --extra webui

echo ""
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Create .env file if it doesn't exist
echo -e "${YELLOW}Setting up configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env from .env.example"
        echo "  You can customize .env with your backend settings"
    else
        echo -e "${RED}✗ Error: .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} .env already exists"
fi
echo ""

# Create user.json file if it doesn't exist
echo -e "${YELLOW}Setting up user data...${NC}"
if [ ! -f "data/user.json" ]; then
    if [ -f "data/user.json.example" ]; then
        cp data/user.json.example data/user.json
        echo -e "${GREEN}✓${NC} Created data/user.json from user.json.example"
        echo "  Add your credit cards to data/user.json to get personalized recommendations"
    else
        echo -e "${YELLOW}⚠ Warning: data/user.json.example not found${NC}"
        echo "  Creating empty user.json"
        mkdir -p data
        echo '{"wallet":[],"custom_valuations":{},"credits":{}}' > data/user.json
    fi
else
    echo -e "${GREEN}✓${NC} data/user.json already exists"
fi
echo ""

# Apply Miles branding to Open Web UI
echo -e "${YELLOW}Applying Miles branding...${NC}"
if [ -f "./apply_branding.sh" ]; then
    ./apply_branding.sh
else
    echo -e "${YELLOW}⚠ Warning: apply_branding.sh not found, skipping branding${NC}"
fi

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "To start Miles, run:"
echo "  uv run python miles.py"
echo ""
echo "Or without the WebUI:"
echo "  uv run python miles.py --no-webui"
echo ""
echo "Before running, make sure you have:"
echo "  1. LM Studio or Ollama running with a model loaded"
echo "  2. (Optional) Edit data/user.json to add your credit cards for personalized recommendations"
echo ""
