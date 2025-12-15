#!/bin/bash
#
# Apply Miles branding to Open Web UI
# This script copies custom CSS and favicon files to the Open Web UI installation
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRANDING_DIR="$SCRIPT_DIR/branding"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🎨 Applying Miles branding to Open Web UI..."
echo ""

# Find Open Web UI installation (check .venv first for uv, then venv for pip)
OPENWEBUI_STATIC=""
for VENV_DIR in ".venv" "venv"; do
    if [ -d "$SCRIPT_DIR/$VENV_DIR/lib/python3.12/site-packages/open_webui/static" ]; then
        OPENWEBUI_STATIC="$SCRIPT_DIR/$VENV_DIR/lib/python3.12/site-packages/open_webui/static"
        break
    elif [ -d "$SCRIPT_DIR/$VENV_DIR/lib/python3.11/site-packages/open_webui/static" ]; then
        OPENWEBUI_STATIC="$SCRIPT_DIR/$VENV_DIR/lib/python3.11/site-packages/open_webui/static"
        break
    else
        # Try to find it dynamically
        FOUND=$(find "$SCRIPT_DIR/$VENV_DIR/lib" -type d -path "*/open_webui/static" 2>/dev/null | head -1)
        if [ -n "$FOUND" ]; then
            OPENWEBUI_STATIC="$FOUND"
            break
        fi
    fi
done

OPENWEBUI_FRONTEND_STATIC=""
for VENV_DIR in ".venv" "venv"; do
    if [ -d "$SCRIPT_DIR/$VENV_DIR/lib/python3.12/site-packages/open_webui/frontend/static" ]; then
        OPENWEBUI_FRONTEND_STATIC="$SCRIPT_DIR/$VENV_DIR/lib/python3.12/site-packages/open_webui/frontend/static"
        break
    elif [ -d "$SCRIPT_DIR/$VENV_DIR/lib/python3.11/site-packages/open_webui/frontend/static" ]; then
        OPENWEBUI_FRONTEND_STATIC="$SCRIPT_DIR/$VENV_DIR/lib/python3.11/site-packages/open_webui/frontend/static"
        break
    else
        # Try to find it dynamically
        FOUND=$(find "$SCRIPT_DIR/$VENV_DIR/lib" -type d -path "*/open_webui/frontend/static" 2>/dev/null | head -1)
        if [ -n "$FOUND" ]; then
            OPENWEBUI_FRONTEND_STATIC="$FOUND"
            break
        fi
    fi
done

# Check if Open Web UI is installed
if [ -z "$OPENWEBUI_STATIC" ] || [ ! -d "$OPENWEBUI_STATIC" ]; then
    echo -e "${RED}✗ Error: Open Web UI not found${NC}"
    echo "  Please install it first with: uv sync --extra webui"
    exit 1
fi

echo -e "${GREEN}✓ Found Open Web UI installation${NC}"
echo "  Main static: $OPENWEBUI_STATIC"
if [ -n "$OPENWEBUI_FRONTEND_STATIC" ]; then
    echo "  Frontend static: $OPENWEBUI_FRONTEND_STATIC"
fi
echo ""

# Patch WEBUI_NAME logic to allow clean custom names
echo "🔧 Patching WEBUI_NAME configuration..."
OPENWEBUI_ENV="$(dirname "$OPENWEBUI_STATIC")/env.py"
if [ -f "$OPENWEBUI_ENV" ]; then
    # Remove the logic that appends " (Open WebUI)" to custom names
    sed -i.bak '/if WEBUI_NAME != "Open WebUI":/,/WEBUI_NAME += " (Open WebUI)"/d' "$OPENWEBUI_ENV"
    echo -e "${GREEN}✓ WEBUI_NAME patched for clean branding${NC}"
else
    echo -e "${YELLOW}⚠ Warning: env.py not found${NC}"
fi
echo ""

# Apply custom CSS
echo "📝 Applying custom Miles CSS theme..."
if [ -f "$BRANDING_DIR/custom.css" ]; then
    cp "$BRANDING_DIR/custom.css" "$OPENWEBUI_STATIC/custom.css"
    [ -n "$OPENWEBUI_FRONTEND_STATIC" ] && cp "$BRANDING_DIR/custom.css" "$OPENWEBUI_FRONTEND_STATIC/custom.css"
    echo -e "${GREEN}✓ Custom CSS applied${NC}"
else
    echo -e "${RED}✗ custom.css not found in branding directory${NC}"
    exit 1
fi

# Apply favicons
echo "🖼️  Applying Miles favicons and logos..."

# Check if favicon files exist
if [ ! -d "$BRANDING_DIR/favicons" ] || [ -z "$(ls -A "$BRANDING_DIR/favicons" 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ Warning: No favicon files found in branding/favicons/${NC}"
    echo "  Please add your Miles logo files to the branding/favicons/ directory"
    echo "  See branding/README.md for required files"
else
    FAVICON_FILES=(
        "miles.svg:favicon.svg"
        "favicon.png:favicon.png"
        "favicon.png:favicon.ico"
        "favicon.png:favicon-dark.png"
        "favicon-96x96.png:favicon-96x96.png"
        "apple-touch-icon.png:apple-touch-icon.png"
        "favicon.png:logo.png"
        "web-app-manifest-192x192.png:web-app-manifest-192x192.png"
        "web-app-manifest-512x512.png:web-app-manifest-512x512.png"
        "splash.png:splash.png"
        "splash-dark.png:splash-dark.png"
    )

    for mapping in "${FAVICON_FILES[@]}"; do
        source_file="${mapping%%:*}"
        dest_file="${mapping##*:}"

        if [ -f "$BRANDING_DIR/favicons/$source_file" ]; then
            cp "$BRANDING_DIR/favicons/$source_file" "$OPENWEBUI_STATIC/$dest_file"
            [ -n "$OPENWEBUI_FRONTEND_STATIC" ] && cp "$BRANDING_DIR/favicons/$source_file" "$OPENWEBUI_FRONTEND_STATIC/$dest_file"
        else
            echo -e "${YELLOW}⚠ Warning: $source_file not found, skipping${NC}"
        fi
    done

    # Also copy favicon.png to the frontend root directory (outside static/)
    if [ -n "$OPENWEBUI_FRONTEND_STATIC" ] && [ -f "$BRANDING_DIR/favicons/favicon.png" ]; then
        cp "$BRANDING_DIR/favicons/favicon.png" "$OPENWEBUI_FRONTEND_STATIC/../favicon.png"
    fi

    echo -e "${GREEN}✓ Favicons and logos applied${NC}"
fi

# Apply carousel/splash screen images
echo "🖼️  Applying carousel images for onboarding splash screen..."

CAROUSEL_SOURCE_DIR="$BRANDING_DIR/carousel_images"
if [ -d "$CAROUSEL_SOURCE_DIR" ] && [ -n "$(ls -A "$CAROUSEL_SOURCE_DIR" 2>/dev/null)" ]; then
    CAROUSEL_TARGET=""
    if [ -n "$OPENWEBUI_FRONTEND_STATIC" ] && [ -d "$OPENWEBUI_FRONTEND_STATIC/../assets/images" ]; then
        CAROUSEL_TARGET="$OPENWEBUI_FRONTEND_STATIC/../assets/images"
    elif [ -d "$OPENWEBUI_STATIC/../assets/images" ]; then
        CAROUSEL_TARGET="$OPENWEBUI_STATIC/../assets/images"
    fi

    if [ -n "$CAROUSEL_TARGET" ]; then
        # Replace default carousel images with Miles-branded ones
        [ -f "$CAROUSEL_SOURCE_DIR/image1.jpg" ] && cp "$CAROUSEL_SOURCE_DIR/image1.jpg" "$CAROUSEL_TARGET/adam.jpg"
        [ -f "$CAROUSEL_SOURCE_DIR/image2.jpg" ] && cp "$CAROUSEL_SOURCE_DIR/image2.jpg" "$CAROUSEL_TARGET/galaxy.jpg"
        [ -f "$CAROUSEL_SOURCE_DIR/image3.jpg" ] && cp "$CAROUSEL_SOURCE_DIR/image3.jpg" "$CAROUSEL_TARGET/earth.jpg"
        [ -f "$CAROUSEL_SOURCE_DIR/image4.jpg" ] && cp "$CAROUSEL_SOURCE_DIR/image4.jpg" "$CAROUSEL_TARGET/space.jpg"
        echo -e "${GREEN}✓ Carousel images applied${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: Could not find carousel images directory${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Note: No custom carousel images found (using defaults)${NC}"
fi

# Apply text changes (page title and sign-in text)
echo "📝 Applying Miles branding to text..."

# Change page title
sed -i.bak 's/<title>Open WebUI<\/title>/<title>Miles<\/title>/g' "$OPENWEBUI_STATIC/../index.html" 2>/dev/null || true
[ -n "$OPENWEBUI_FRONTEND_STATIC" ] && sed -i.bak 's/<title>Open WebUI<\/title>/<title>Miles<\/title>/g' "$OPENWEBUI_FRONTEND_STATIC/../index.html" 2>/dev/null || true

# Replace "Open WebUI" with "Miles" in all JavaScript files
echo "📝 Replacing 'Open WebUI' with 'Miles' in JavaScript bundles..."
APP_DIR=""
if [ -n "$OPENWEBUI_FRONTEND_STATIC" ]; then
    APP_DIR="$OPENWEBUI_FRONTEND_STATIC/../_app"
elif [ -d "$OPENWEBUI_STATIC/../_app" ]; then
    APP_DIR="$OPENWEBUI_STATIC/../_app"
fi

if [ -n "$APP_DIR" ] && [ -d "$APP_DIR" ]; then
    # Find all .js files and replace "Open WebUI" with "Miles"
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Open WebUI/Miles/g' {} \;

    # Replace splash screen text with Miles branding
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Explore the cosmos/Maximize your miles/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Unlock mysteries/Unlock premium rewards/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Chart new frontiers/Chart your travel goals/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Dive into knowledge/Dive into rewards/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Discover wonders/Discover redemptions/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Ignite curiosity/Ignite your wanderlust/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Forge new paths/Forge smart strategies/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Unravel secrets/Unravel point values/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Pioneer insights/Pioneer your journey/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/Embark on adventures/Embark on adventures/g' {} \;
    find "$APP_DIR" -name "*.js" -type f -exec sed -i.bak 's/wherever you are/with every card/g' {} \;

    # Clean up backup files
    find "$APP_DIR" -name "*.bak" -type f -delete

    echo -e "${GREEN}✓ Text branding applied${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Could not find app directory for text replacement${NC}"
fi

echo ""
echo -e "${GREEN}✅ Miles branding applied successfully!${NC}"
echo ""
echo "Note: If you add custom favicon files later, run this script again to apply them."
echo "See branding/README.md for required files."
