"""
EVOLV — LinkedIn post-image generator.

Renders 1080x1350 (4:5) post images from the shared template so every
post looks like it belongs to the same account.

Single image:
    python make_post.py --text "We wrote the test script *after* we ran it." \
                        --out we-wrote-the-test.png

Stat image:
    python make_post.py --type stat --stat "60-80%" \
        --text "of FDA drug GMP warning letters cite data integrity." \
        --out data-integrity-stat.png

Contrast image:
    python make_post.py --type contrast \
        --before "~You need a new framework for AI.~" \
        --after  "You need to *apply the one you have*." \
        --out framework.png

Batch (recommended — one file per posting week):
    python make_post.py --batch posts.json

Formatting inside any text field:
    *word*   -> mint accent
    ~word~   -> struck through (for the 'before' half)
    \n       -> line break
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
TEMPLATE = (ROOT / "post-template.html").as_uri()
OUT_DIR = ROOT / "posts"


def render(configs: list[dict]) -> list[Path]:
    """Render each config to a PNG and return the written paths."""
    OUT_DIR.mkdir(exist_ok=True)
    written: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1080, "height": 1350},
            device_scale_factor=2,          # retina-crisp
        )
        page.goto(TEMPLATE)
        page.wait_for_timeout(2500)          # let Google Fonts settle
        for cfg in configs:
            out = OUT_DIR / cfg.get("out", "post.png")
            page.evaluate("cfg => window.renderPost(cfg)", cfg)
            page.wait_for_timeout(220)       # let auto-fit finish
            page.locator("#card").screenshot(path=str(out))
            print(f"  wrote {out.name}")
            written.append(out)
        browser.close()
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="EVOLV LinkedIn post images")
    ap.add_argument("--batch", help="JSON file with a list of configs")
    ap.add_argument("--type", default="statement",
                    choices=["statement", "stat", "contrast"])
    ap.add_argument("--text", default="")
    ap.add_argument("--stat", default="")
    ap.add_argument("--before", default="")
    ap.add_argument("--after", default="")
    ap.add_argument("--kicker", default="THE VALIDATION EDGE")
    ap.add_argument("--handle",
                    default="Sreejith Kanhirangadan\nevolifeval.com")
    ap.add_argument("--out", default="post.png")
    args = ap.parse_args()

    if args.batch:
        configs = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    else:
        configs = [{
            "type": args.type, "text": args.text, "stat": args.stat,
            "before": args.before, "after": args.after,
            "kicker": args.kicker, "handle": args.handle, "out": args.out,
        }]

    print(f"Rendering {len(configs)} image(s)...")
    render(configs)
    print(f"Done -> {OUT_DIR}")


if __name__ == "__main__":
    main()
