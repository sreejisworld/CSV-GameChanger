from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SRC = (ROOT / "banner-final.html").as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1500},
                    device_scale_factor=2)
    pg.goto(SRC)
    pg.wait_for_timeout(2500)
    for eid, name in (("f1", "banner-b-final.png"),
                      ("f2", "banner-b-final-stats.png"),
                      ("check", "banner-b-clearance.png")):
        pg.locator(f"#{eid}").screenshot(path=str(ROOT / name))
        print("wrote", name)
    b.close()
