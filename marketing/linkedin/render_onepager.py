from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SRC = (ROOT / "assessment-onepager.html").as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 900, "height": 1300},
                    device_scale_factor=2)
    pg.goto(SRC)
    pg.wait_for_timeout(2500)
    pg.pdf(path=str(ROOT / "AI-CSV-Readiness-Assessment.pdf"),
           format="A4", print_background=True,
           margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    pg.locator(".page").screenshot(
        path=str(ROOT / "assessment-preview.png"))
    b.close()
print("wrote PDF + preview")
