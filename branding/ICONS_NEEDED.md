# Miles Branding Icons Checklist

This file lists all the icon files needed for complete Miles branding in Open Web UI.

## Required Icon Files

Place all files in the `branding/favicons/` directory.

### Essential Icons

- [ ] **miles.svg** - Main logo in SVG format (vector, scalable)
  - Used as: Primary logo in the UI
  - Format: SVG
  - Recommended: Simple, clean design that works at any size

- [ ] **favicon.png** - Standard favicon
  - Size: 32x32 pixels
  - Format: PNG with transparent background
  - Used as: Browser tab icon, also used for favicon.ico and favicon-dark.png

- [ ] **favicon-96x96.png** - Larger favicon
  - Size: 96x96 pixels
  - Format: PNG with transparent background
  - Used as: High-DPI displays

### Apple/iOS Icons

- [ ] **apple-touch-icon.png** - Apple touch icon
  - Size: 180x180 pixels
  - Format: PNG (can have solid background color)
  - Used as: iOS home screen icon when user adds to home screen

### Progressive Web App (PWA) Icons

- [ ] **web-app-manifest-192x192.png** - Small PWA icon
  - Size: 192x192 pixels
  - Format: PNG
  - Used as: PWA icon for mobile devices

- [ ] **web-app-manifest-512x512.png** - Large PWA icon
  - Size: 512x512 pixels
  - Format: PNG
  - Used as: PWA icon for tablets and desktop

### Splash Screen Logos

- [ ] **splash.png** - Splash screen logo (light mode)
  - Size: Recommended 512x512 pixels (or larger)
  - Format: PNG with transparent background
  - Used as: Loading/splash screen logo in light mode

- [ ] **splash-dark.png** - Splash screen logo (dark mode)
  - Size: Recommended 512x512 pixels (or larger)
  - Format: PNG with transparent background
  - Used as: Loading/splash screen logo in dark mode
  - Note: Often same as splash.png but optimized for dark backgrounds

## Optional Files

### Carousel/Onboarding Images

Place these in `branding/carousel_images/` directory:

- [ ] **image1.jpg** - First carousel slide
  - Size: 1920x1080 pixels (or similar 16:9 ratio)
  - Format: JPG
  - Content: Welcome screen or product feature

- [ ] **image2.jpg** - Second carousel slide
  - Size: 1920x1080 pixels
  - Format: JPG
  - Content: Key feature or benefit

- [ ] **image3.jpg** - Third carousel slide
  - Size: 1920x1080 pixels
  - Format: JPG
  - Content: Getting started guide

- [ ] **image4.jpg** - Fourth carousel slide
  - Size: 1920x1080 pixels
  - Format: JPG
  - Content: Call to action or final feature

## Quick Start Guide

### If You Have a Single Logo File:

1. **Start with one logo** (SVG or high-res PNG)
2. **Use an online tool** to generate all sizes:
   - https://realfavicongenerator.net/
   - https://www.favicon-generator.org/
   - Or use ImageMagick: `convert logo.png -resize 32x32 favicon.png`

### Recommended Tools:

- **Vector editing**: Inkscape (free), Adobe Illustrator
- **Raster editing**: GIMP (free), Photoshop
- **Batch resizing**: ImageMagick, Preview (Mac), IrfanView (Windows)
- **Online generators**: RealFaviconGenerator, Favicon.io

### Example ImageMagick Commands:

```bash
# Assuming you have a source logo.png at 1024x1024
convert logo.png -resize 32x32 favicon.png
convert logo.png -resize 96x96 favicon-96x96.png
convert logo.png -resize 180x180 apple-touch-icon.png
convert logo.png -resize 192x192 web-app-manifest-192x192.png
convert logo.png -resize 512x512 web-app-manifest-512x512.png
convert logo.png -resize 512x512 splash.png
convert logo.png -resize 512x512 splash-dark.png

# For SVG, just copy your source
cp logo.svg miles.svg
```

## Tips

1. **Start simple**: Just provide `favicon.png` and `miles.svg` - the branding script will warn about missing files but continue
2. **Transparent backgrounds**: Most icons should have transparent backgrounds (except apple-touch-icon can have solid color)
3. **Test at different sizes**: Make sure your logo is readable at 32x32 pixels
4. **Dark mode**: Ensure splash-dark.png is visible on dark backgrounds
5. **Brand consistency**: Use the same logo design across all sizes

## After Adding Icons

Once you've added your icon files:

```bash
# From the miles directory
./apply_branding.sh
```

This will copy your icons to the Open Web UI installation.

## Need Help?

- See `branding/README.md` for more details
- Icons are optional - Miles works without custom branding
- You can add icons anytime and re-run `./apply_branding.sh`
