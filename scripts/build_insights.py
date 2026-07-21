"""Generate the EVOLV Insights archive (index + native editions)."""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GTM = ROOT / "docs/gtm-content"
OUT = ROOT / "website/insights"
OUT.mkdir(parents=True, exist_ok=True)

LINKEDIN_SERIES = (
    "https://www.linkedin.com/in/"
    "sreejith-kanhirangadan-csv-advisor/recent-activity/"
)

# ── Editions manifest ───────────────────────────────────────────
# native=True  -> rendered from the markdown file (md)
# native=False -> card links out to LinkedIn (url)
# Editions 1-9: replace url + fill title/hook when Sree sends them.
EDITIONS = [
    {"num": 12, "date": "Jul 2026", "native": True,
     "md": "newsletter-12-draft.md",
     "title": "Who Validated the Tool That Validates "
              "Everything Else?",
     "hook": "A validation platform is itself GAMP Category 5 "
             "software. So who validated it? We made EVOLV "
             "generate its own validation package - live."},
    {"num": 11, "date": "Jul 2026", "native": True,
     "md": "newsletter-11-draft.md",
     "title": "We Built the Vendor Side of the Framework",
     "hook": "Five questions every pharma buyer should ask "
             "their AI vendor - answered with product "
             "artifacts, not promises."},
    {"num": 10, "date": "Jul 2026", "native": True,
     "md": "newsletter-10-draft.md",
     "title": "Our Test Suite Found 11 Holes in Our Own "
              "Safety Rules. Good.",
     "hook": "We built an eval suite that attacks every EVOLV "
             "agent on every change. Its first run found 11 "
             "real gaps in our own AI safety rules."},
    # ── Earlier editions (LinkedIn) - fill url/title/hook ──
    # {"num": 9, "date": "...", "native": False,
    #  "url": "https://www.linkedin.com/pulse/...",
    #  "title": "...", "hook": "..."},
]

# Cover accent rotation (warm-light brand tones)
ACCENTS = [
    ("#3B5BFF", "#EEF1FF"),   # blue
    ("#65A30D", "#F2F8E7"),   # lime
    ("#D97706", "#FDF3E7"),   # amber
]

TOKENS = """
  :root{--bg:#FAFAF7;--card:#FFFFFF;--ink:#2A2825;--muted:#6B675F;
  --faint:#8A867C;--border:#EAE7E1;--border2:#DDD9D0;--blue:#3B5BFF;
  --lime:#65A30D;--lime-bright:#A3E635;--amber:#D97706;
  --serif:'Fraunces',Georgia,serif;--sans:'Inter',system-ui,sans-serif;
  --mono:'IBM Plex Mono',monospace;}
  *{box-sizing:border-box;margin:0;padding:0;}
  html{scroll-behavior:smooth;}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased;}
  ::selection{background:rgba(163,230,53,0.4);}
  a{color:var(--blue);}
  .wrap{max-width:820px;margin:0 auto;padding:0 24px;}
  nav{position:sticky;top:0;z-index:50;
  background:rgba(250,250,247,0.85);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border);}
  .nav-inner{display:flex;align-items:center;gap:24px;padding:14px 24px;
  max-width:1080px;margin:0 auto;}
  .logo{display:flex;align-items:baseline;gap:10px;text-decoration:none;
  color:var(--ink);}
  .logo-word{font-family:var(--serif);font-size:22px;font-weight:600;
  letter-spacing:.02em;}
  .logo-sub{font-size:10px;font-family:var(--mono);color:var(--faint);
  letter-spacing:.12em;text-transform:uppercase;}
  .nav-links{display:flex;gap:22px;margin-left:auto;align-items:center;}
  .nav-links a{color:var(--muted);text-decoration:none;font-size:14px;
  font-weight:500;}
  .nav-links a:hover{color:var(--ink);}
  .btn{display:inline-flex;align-items:center;gap:8px;padding:11px 22px;
  border-radius:100px;font-size:15px;font-weight:600;text-decoration:none;
  cursor:pointer;border:none;font-family:var(--sans);transition:all .18s;}
  .btn-ink{background:var(--ink);color:#fff;}
  .btn-ink:hover{background:#000;transform:translateY(-1px);
  box-shadow:0 6px 20px rgba(42,40,37,.25);}
  .btn-sm{padding:8px 18px;font-size:14px;}
"""


def inline(t):
    t = html.escape(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    return t


def md_to_html(md):
    lines = md.split("\n")
    n = len(lines)
    out = []
    i = 0
    first_h1_skipped = False
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        # Skip the redundant build-log subtitle (shown in meta line)
        if re.match(r'^\*EVOLV build log', s):
            i += 1
            continue
        if s.startswith('# '):
            if not first_h1_skipped:
                first_h1_skipped = True
                i += 1
                continue
            out.append(f'<h2>{inline(s[2:])}</h2>')
            i += 1
            continue
        if s.startswith('## '):
            out.append(f'<h2>{inline(s[3:])}</h2>')
            i += 1
            continue
        if s.startswith('### '):
            out.append(f'<h3>{inline(s[4:])}</h3>')
            i += 1
            continue
        if s.startswith('---'):
            out.append('<hr>')
            i += 1
            continue
        if s.startswith('>'):
            block = []
            while i < n and lines[i].strip().startswith('>'):
                block.append(lines[i].strip().lstrip('>').strip())
                i += 1
            out.append(f'<blockquote>{inline(" ".join(block))}'
                       f'</blockquote>')
            continue
        if re.match(r'^[-*] ', s):
            items = []
            while i < n and re.match(r'^[-*] ', lines[i].strip()):
                items.append(f'<li>{inline(lines[i].strip()[2:])}</li>')
                i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue
        if re.match(r'^\d+\. ', s):
            items = []
            while i < n and re.match(r'^\d+\. ', lines[i].strip()):
                txt = re.sub(r'^\d+\. ', '', lines[i].strip())
                items.append(f'<li>{inline(txt)}</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
            continue
        para = [s]
        i += 1
        while (i < n and lines[i].strip()
               and not re.match(r'^(#|>|---|[-*] |\d+\. )',
                                lines[i].strip())):
            para.append(lines[i].strip())
            i += 1
        out.append(f'<p>{inline(" ".join(para))}</p>')
    return "\n".join(out)


NAV = """
<nav><div class="nav-inner">
  <a class="logo" href="../index.html">
    <span class="logo-word">EVOLV</span>
    <span class="logo-sub">The Validation Factory</span></a>
  <div class="nav-links">
    <a href="../index.html#how">Platform</a>
    <a href="index.html">Insights</a>
    <a class="btn btn-ink btn-sm" id="demo" href="#">Book a demo</a>
  </div></div></nav>
"""

DEMO_JS = """
<script>
var m='mailto:sreejith@evolifeval.com?subject='+
encodeURIComponent('EVOLV - 15-min demo request');
var d=document.getElementById('demo');if(d)d.href=m;
</script>
"""


def article_page(ed):
    body = md_to_html((GTM / ed["md"]).read_text(encoding="utf-8"))
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{html.escape(ed['title'])} - EVOLV Insights</title>
<meta name="description" content="{html.escape(ed['hook'])}">
<meta name="robots" content="index,follow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{TOKENS}
  .article{{padding:52px 0 40px;}}
  .eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--blue);margin-bottom:14px;}}
  .back{{font-size:14px;color:var(--muted);text-decoration:none;
  font-weight:500;}} .back:hover{{color:var(--ink);}}
  h1{{font-family:var(--serif);font-weight:600;
  font-size:clamp(30px,4.4vw,44px);line-height:1.12;
  letter-spacing:-.01em;margin:6px 0 10px;}}
  .meta{{font-size:14px;color:var(--faint);margin-bottom:8px;}}
  article h2{{font-family:var(--serif);font-weight:600;font-size:25px;
  margin:34px 0 12px;line-height:1.2;}}
  article h3{{font-size:18px;font-weight:600;margin:24px 0 8px;}}
  article p{{margin:0 0 16px;font-size:17px;color:#332F2A;}}
  article ul,article ol{{margin:0 0 16px 22px;}}
  article li{{margin-bottom:7px;font-size:17px;color:#332F2A;}}
  article strong{{color:var(--ink);}}
  article code{{font-family:var(--mono);font-size:.9em;
  background:#F2F0EA;padding:1px 5px;border-radius:4px;}}
  article blockquote{{border-left:3px solid var(--lime);
  background:#F7F9F2;padding:14px 20px;margin:0 0 20px;
  border-radius:0 8px 8px 0;font-size:16.5px;color:#3A3833;}}
  article hr{{border:none;border-top:1px solid var(--border);
  margin:30px 0;}}
  .foot{{margin-top:40px;border-top:1px solid var(--border);
  padding-top:24px;display:flex;gap:14px;flex-wrap:wrap;
  align-items:center;}}
  .li-note{{font-size:13.5px;color:var(--faint);margin-top:18px;}}
  footer{{padding:32px 0;border-top:1px solid var(--border);
  font-size:13.5px;color:var(--muted);text-align:center;margin-top:20px;}}
</style></head><body>
{NAV}
<div class="wrap article">
  <a class="back" href="index.html">&larr; All editions</a>
  <div class="eyebrow" style="margin-top:20px;">EVOLV Insights &middot; Edition {ed['num']}</div>
  <h1>{html.escape(ed['title'])}</h1>
  <div class="meta">{ed['date']} &middot; EVOLV build log</div>
  <article>{body}</article>
  <p class="li-note">Originally shared on LinkedIn.
    <a href="{LINKEDIN_SERIES}" target="_blank" rel="noopener">
    Subscribe there for new editions &rarr;</a></p>
  <div class="foot">
    <a class="btn btn-ink" id="demo" href="#">Book a 15-min demo</a>
    <a class="btn" style="border:1.5px solid var(--border2);
    color:var(--ink);" href="index.html">More editions</a>
  </div>
</div>
<footer>Powered by EVOLV | A WingstarTech Inc. Product &middot; &copy; 2026</footer>
{DEMO_JS}
</body></html>"""


def cover(ed, idx):
    fg, bg = ACCENTS[idx % len(ACCENTS)]
    return f"""<div class="cover" style="background:{bg};">
      <div class="cover-ed" style="color:{fg};">#{ed['num']}</div>
      <div class="cover-lbl">EVOLV &middot; INSIGHTS</div></div>"""


def card(ed, idx):
    href = (f"edition-{ed['num']}.html" if ed["native"]
            else ed.get("url", LINKEDIN_SERIES))
    ext = "" if ed["native"] else ' target="_blank" rel="noopener"'
    tag = ("Read &rarr;" if ed["native"]
           else "Read on LinkedIn &rarr;")
    return f"""<a class="card" href="{href}"{ext}>
      {cover(ed, idx)}
      <div class="card-body">
        <div class="card-meta">Edition {ed['num']} &middot; {ed['date']}</div>
        <div class="card-title">{html.escape(ed['title'])}</div>
        <div class="card-hook">{html.escape(ed['hook'])}</div>
        <div class="card-read">{tag}</div>
      </div></a>"""


def index_page():
    feat = EDITIONS[0]
    rest = EDITIONS[1:]
    cards = "\n".join(card(e, i + 1) for i, e in enumerate(rest))
    feat_href = (f"edition-{feat['num']}.html" if feat["native"]
                 else feat.get("url", LINKEDIN_SERIES))
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Insights - EVOLV | The Validation Factory</title>
<meta name="description" content="Field notes on validating AI in GxP - architecture, governance, and the problems we're solving in Computer System Validation.">
<meta name="robots" content="index,follow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{TOKENS}
  .wrap{{max-width:1080px;}}
  header.hero{{padding:56px 0 26px;}}
  .eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--blue);margin-bottom:14px;}}
  h1{{font-family:var(--serif);font-weight:600;
  font-size:clamp(34px,5vw,52px);line-height:1.08;letter-spacing:-.015em;}}
  .sub{{margin-top:16px;font-size:18px;color:var(--muted);max-width:640px;}}
  .cover{{aspect-ratio:16/9;border-radius:12px;display:flex;
  flex-direction:column;justify-content:center;align-items:center;
  gap:4px;overflow:hidden;}}
  .cover-ed{{font-family:var(--serif);font-size:52px;font-weight:600;
  line-height:1;}}
  .cover-lbl{{font-family:var(--mono);font-size:11px;letter-spacing:.18em;
  color:var(--faint);}}
  .featured{{display:grid;grid-template-columns:1.1fr 1fr;gap:28px;
  align-items:center;background:var(--card);border:1px solid var(--border);
  border-radius:18px;padding:24px;margin:22px 0 40px;text-decoration:none;
  color:var(--ink);transition:all .2s;}}
  .featured:hover{{box-shadow:0 12px 34px rgba(42,40,37,.08);
  transform:translateY(-2px);}}
  .featured .cover{{aspect-ratio:16/10;}}
  .featured .cover-ed{{font-size:72px;}}
  .feat-tag{{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--lime);margin-bottom:8px;}}
  .feat-title{{font-family:var(--serif);font-size:27px;font-weight:600;
  line-height:1.15;margin-bottom:10px;}}
  .feat-hook{{font-size:16px;color:var(--muted);margin-bottom:14px;}}
  .feat-read{{font-size:14px;font-weight:600;color:var(--blue);}}
  .sec-label{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--faint);margin-bottom:18px;}}
  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;}}
  .card{{background:var(--card);border:1px solid var(--border);
  border-radius:16px;overflow:hidden;text-decoration:none;color:var(--ink);
  transition:all .2s;display:flex;flex-direction:column;}}
  .card:hover{{box-shadow:0 12px 30px rgba(42,40,37,.08);
  transform:translateY(-3px);}}
  .card .cover{{border-radius:0;}}
  .card-body{{padding:18px 20px 20px;}}
  .card-meta{{font-family:var(--mono);font-size:11px;color:var(--faint);
  margin-bottom:8px;}}
  .card-title{{font-family:var(--serif);font-size:19px;font-weight:600;
  line-height:1.2;margin-bottom:8px;}}
  .card-hook{{font-size:14px;color:var(--muted);line-height:1.5;
  margin-bottom:12px;}}
  .card-read{{font-size:13px;font-weight:600;color:var(--blue);}}
  .cta-band{{margin:56px 0 0;background:var(--ink);border-radius:18px;
  padding:40px;text-align:center;}}
  .cta-band h2{{font-family:var(--serif);color:#fff;font-size:26px;
  font-weight:600;margin-bottom:8px;}}
  .cta-band p{{color:rgba(245,244,240,.65);margin-bottom:20px;}}
  .cta-band .btn-lime{{background:var(--lime-bright);color:#1A2E05;}}
  footer{{padding:34px 0;border-top:1px solid var(--border);
  font-size:13.5px;color:var(--muted);text-align:center;margin-top:44px;}}
  @media(max-width:820px){{.grid{{grid-template-columns:1fr;}}
  .featured{{grid-template-columns:1fr;}}}}
</style></head><body>
{NAV.replace('../index.html','index.html').replace('href="index.html">Insights','href="index.html" style="color:var(--ink)">Insights').replace('../index.html#how','index.html#how')}
<header class="hero"><div class="wrap">
  <div class="eyebrow">EVOLV Insights</div>
  <h1>Field notes on validating AI in GxP.</h1>
  <p class="sub">Architecture, governance, and the problems we're
  solving in Computer System Validation - written for the QA and
  CSV leads who have to defend this work in an inspection.</p>
</div></header>
<div class="wrap">
  <a class="featured" href="{feat_href}"{"" if feat["native"] else ' target="_blank" rel="noopener"'}>
    {cover(feat, 0)}
    <div>
      <div class="feat-tag">Latest edition &middot; #{feat['num']}</div>
      <div class="feat-title">{html.escape(feat['title'])}</div>
      <div class="feat-hook">{html.escape(feat['hook'])}</div>
      <div class="feat-read">{"Read &rarr;" if feat["native"] else "Read on LinkedIn &rarr;"}</div>
    </div>
  </a>
  <div class="sec-label">All editions</div>
  <div class="grid">{cards}</div>
  <div class="cta-band">
    <h2>See it on your own requirement.</h2>
    <p>Bring one requirement from your backlog. We'll draft it,
    verify it, and hand you the signed PDF - live, in 15 minutes.</p>
    <a class="btn btn-lime" id="demo" href="#">Book a 15-min demo</a>
  </div>
</div>
<footer>Powered by EVOLV | A WingstarTech Inc. Product &middot; &copy; 2026 &middot;
  <a href="mailto:sreejith@evolifeval.com" style="color:var(--muted);">sreejith@evolifeval.com</a>
</footer>
{DEMO_JS}
</body></html>"""


# ── Generate ────────────────────────────────────────────────────
for ed in EDITIONS:
    if ed["native"]:
        (OUT / f"edition-{ed['num']}.html").write_text(
            article_page(ed), encoding="utf-8")
        print(f"wrote edition-{ed['num']}.html")
(OUT / "index.html").write_text(index_page(), encoding="utf-8")
print("wrote insights/index.html")
