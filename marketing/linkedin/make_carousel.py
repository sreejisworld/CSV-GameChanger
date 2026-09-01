"""
EVOLV — LinkedIn carousel generator.

Renders a slide deck defined in JSON to a multi-page PDF sized
1080x1350 per page — the format LinkedIn accepts as a document post
(the format that earns dwell time and saves).

    python make_carousel.py --deck carousel-ai-triage.json \
                            --out ai-triage.pdf

Slide types:
  cover      {title, sub}
  point      {num, title, text, tag}
  list       {title, items[]}
  statement  {title, text}          <- default

Formatting: *word* renders in mint, \n is a line break.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
TEMPLATE = (ROOT / "carousel.html").as_uri()
OUT_DIR = ROOT / "carousels"


def render(slides: list[dict], out_name: str,
           png_preview: bool = True) -> Path:
    """Render *slides* to a multi-page PDF; return the PDF path."""
    OUT_DIR.mkdir(exist_ok=True)
    pdf_path = OUT_DIR / out_name
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1080, "height": 1350},
            device_scale_factor=2,
        )
        page.goto(TEMPLATE)
        page.wait_for_timeout(2500)          # fonts
        page.evaluate("s => window.renderDeck(s)", slides)
        page.wait_for_timeout(400)           # autofit
        page.pdf(path=str(pdf_path), width="1080px", height="1350px",
                 print_background=True,
                 margin={"top": "0", "bottom": "0",
                         "left": "0", "right": "0"})
        if png_preview:
            for i in range(min(len(slides), 3)):
                page.locator(".slide").nth(i).screenshot(
                    path=str(OUT_DIR / f"{pdf_path.stem}-s{i+1}.png"))
        browser.close()
    return pdf_path


def main() -> None:
    ap = argparse.ArgumentParser(description="EVOLV LinkedIn carousel")
    ap.add_argument("--deck", required=True, help="JSON file of slides")
    ap.add_argument("--out", default="carousel.pdf")
    args = ap.parse_args()

    slides = json.loads(Path(args.deck).read_text(encoding="utf-8"))
    print(f"Rendering {len(slides)} slides...")
    out = render(slides, args.out)
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
