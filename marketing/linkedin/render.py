"""Render the LinkedIn banner variants to PNG at 1584x396."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SRC = (ROOT / "banner.html").as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1400},
                    device_scale_factor=2)
    pg.goto(SRC)
    pg.wait_for_timeout(2500)          # let Google Fonts settle
    for vid in ("a", "b", "c"):
        out = ROOT / f"banner-{vid}.png"
        pg.locator(f"#{vid}").screenshot(path=str(out))
        print("wrote", out.name)
    b.close()
