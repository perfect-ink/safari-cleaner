#!/usr/bin/env python3
"""
make_icon.py — Render icon/AppIcon.svg into every size in AppIcon.appiconset.

Usage: python3 make_icon.py

Needs one SVG renderer, tried in this order:
  - rsvg-convert   (brew install librsvg)
  - Playwright     (pip install playwright && playwright install chromium)
"""

import json, os, shutil, subprocess, sys

ROOT    = os.path.dirname(os.path.abspath(__file__))
SVG     = os.path.join(ROOT, "icon/AppIcon.svg")
ICONSET = os.path.join(ROOT, "SafariCleaner/Safari Cleaner/Assets.xcassets/AppIcon.appiconset")
SIZES   = [16, 32, 64, 128, 256, 512, 1024]


def render_rsvg(pixels, out):
    subprocess.run(["rsvg-convert", "-w", str(pixels), "-h", str(pixels), SVG, "-o", out], check=True)


def make_playwright_renderer():
    from playwright.sync_api import sync_playwright
    svg = open(SVG).read()
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page()

    def render(pixels, out):
        page.set_viewport_size({"width": pixels, "height": pixels})
        sized = svg.replace('width="1024" height="1024"', f'width="{pixels}" height="{pixels}"', 1)
        page.set_content(f'<html><body style="margin:0;background:transparent">{sized}</body></html>')
        page.screenshot(path=out, omit_background=True)

    return render, lambda: (browser.close(), pw.stop())


def pick_renderer():
    if shutil.which("rsvg-convert"):
        return render_rsvg, lambda: None
    try:
        return make_playwright_renderer()
    except ImportError:
        sys.exit("No SVG renderer found. Install one: `brew install librsvg` "
                 "or `pip install playwright && playwright install chromium`.")


render, done = pick_renderer()
os.makedirs(ICONSET, exist_ok=True)

images = []
for size in SIZES:
    for scale in ([1, 2] if size <= 512 else [1]):
        filename = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
        render(size * scale, os.path.join(ICONSET, filename))
        images.append({"idiom": "mac", "scale": f"{scale}x", "size": f"{size}x{size}", "filename": filename})
        print(f"  {filename}")
done()

with open(os.path.join(ICONSET, "Contents.json"), "w") as f:
    json.dump({"images": images, "info": {"author": "xcode", "version": 1}}, f, indent=2)

print(f"\nDone. Icon written to {ICONSET}")
print("Rebuild the app in Xcode to pick up the new icon.")
