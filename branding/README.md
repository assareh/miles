# Miles Branding Assets

This directory contains branding assets for the Miles Open Web UI interface.

## Required Files

### Favicons (branding/favicons/)
You need to provide these image files for the Miles brand:

- `miles.svg` - Main logo in SVG format
- `favicon.png` - 32x32 favicon
- `favicon-96x96.png` - 96x96 favicon
- `apple-touch-icon.png` - 180x180 Apple touch icon
- `web-app-manifest-192x192.png` - 192x192 PWA icon
- `web-app-manifest-512x512.png` - 512x512 PWA icon
- `splash.png` - Splash screen logo (light mode)
- `splash-dark.png` - Splash screen logo (dark mode)

### Carousel Images (branding/carousel_images/)
Optional: Custom images for the onboarding splash screen carousel

- `image1.jpg` - First carousel image
- `image2.jpg` - Second carousel image
- `image3.jpg` - Third carousel image
- `image4.jpg` - Fourth carousel image

### Custom CSS (branding/)
- `custom.css` - Already provided with Miles theme

## How to Add Your Icon

1. Create or obtain your Miles logo/icon
2. Generate the required sizes using an image editing tool or online service
3. Save them to the `branding/favicons/` directory with the names listed above
4. Run `./apply_branding.sh` to apply the branding

## Notes

- PNG files should have transparent backgrounds where appropriate
- SVG files are preferred for logos as they scale better
- Carousel images are optional - defaults will be used if not provided
