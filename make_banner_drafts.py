#!/usr/bin/env python3
"""
Biocity — homepage banner (hero) drafts → one approval PDF.

Loads the real v3 site in headless Chrome, swaps the hero for each candidate
design (so every draft uses the *actual* Biocity tokens, fonts, header and
buttons), crops just the top section (header + banner) at high DPI, then lays
the drafts out one-per-page in a client-friendly PDF.

    python3 make_banner_drafts.py

Output: design-export/Biocity-v3-Banner-Drafts.pdf
Reuses the CDP/WebSocket plumbing from make_design_pdf.py.
"""
import base64
import os
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import make_design_pdf as mdp  # WS client, http_json, free_port, CHROME

ROOT = mdp.ROOT
OUTDIR = os.path.join(ROOT, "design-export")
SITE = "/v3/index.html"
VIEW_W = 1280          # desktop viewport
SCALE = 2              # device-pixel-ratio for crisp zoomable capture

# shared snippets reused across drafts (real sprite icons live in the page) ----
BADGES = (
    '<span class="badge"><svg><use href="#i-shield"/></svg> NABL Accredited</span>'
    '<span class="badge"><svg><use href="#i-home"/></svg> Free Home Collection</span>'
    '<span class="badge"><svg><use href="#i-clock"/></svg> Reports in 24 Hrs</span>'
)
STARS = '<svg><use href="#i-star"/></svg>' * 5


DRAFTS = [
    # ── 1 · refined split ────────────────────────────────────────────────────
    dict(
        name="Split · Editorial",
        desc="Classic two-column hero — headline & CTA on the left, real photo on "
             "the right with a floating status chip. Closest to the current site, "
             "just cleaner and more premium.",
        css="""
.hero-draft.d1{position:relative;z-index:1;background:var(--bg-soft);
  border-bottom:1px solid var(--border);padding:48px 0 58px}
.d1-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:48px;align-items:center}
.d1 .badge-row{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
.d1-h{font-family:'Fraunces',serif;font-weight:600;font-size:3.1rem;line-height:1.06;
  letter-spacing:-.02em;color:var(--text)}
.d1-h em{font-style:italic;color:var(--accent)}
.d1-sub{font-size:1.05rem;color:var(--text-soft);margin:18px 0 26px;max-width:460px}
.d1-cta{display:flex;gap:12px;flex-wrap:wrap}
.d1-proof{display:flex;align-items:center;gap:8px;margin-top:22px;font-size:.9rem;color:var(--text-soft)}
.d1-proof b{color:var(--text)}
.d1-stars svg{width:16px;height:16px;fill:#f59e0b;color:#f59e0b}
.d1-media{position:relative}
.d1-media img{width:100%;border-radius:20px;box-shadow:var(--shadow-lg);object-fit:cover;aspect-ratio:5/4}
.d1-float{position:absolute;left:-14px;bottom:22px;display:flex;gap:10px;align-items:center;
  background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px 14px;box-shadow:var(--shadow-lg)}
.d1-float>svg{width:20px;height:20px;color:var(--accent);flex:none}
.d1-float b{display:block;font-size:.9rem;color:var(--text)}
.d1-float small{font-size:.76rem;color:var(--text-soft)}
""",
        html=f"""
<section class="hero-draft d1"><div class="wrap d1-grid">
  <div>
    <div class="badge-row">{BADGES}</div>
    <h1 class="d1-h">Lab tests at home,<br>results you can <em>trust</em>.</h1>
    <p class="d1-sub">Certified phlebotomists collect your sample at home — free.
       NABL-accredited labs, digital reports in 24 hours.</p>
    <div class="d1-cta">
      <button class="btn btn-primary">Book a Checkup</button>
      <a class="btn btn-ghost"><svg style="width:17px;height:17px"><use href="#i-phone"/></svg> Talk to us</a>
    </div>
    <div class="d1-proof"><span class="d1-stars">{STARS}</span> <b>4.9 / 5</b> from 3,336 verified reviews</div>
  </div>
  <div class="d1-media">
    <img src="../assets/lab/phlebotomy.png" alt="">
    <div class="d1-float"><svg><use href="#i-file"/></svg>
      <div><b>Report ready in 24 hrs</b><small>WhatsApp &amp; email</small></div></div>
  </div>
</div></section>
""",
    ),

    # ── 2 · full-bleed image with text overlay ───────────────────────────────
    dict(
        name="Full-width Image · Text on it",
        desc="A single edge-to-edge lab photo with a dark gradient wash and the "
             "message laid over it. Bold, trust-building, very 'flagship brand'.",
        css="""
.hero-draft.d2{position:relative;z-index:1;min-height:520px;display:flex;align-items:center;
  background:#08130d;overflow:hidden}
.d2-bg{position:absolute;inset:0}
.d2-bg img{width:100%;height:100%;object-fit:cover}
.d2-ov{position:absolute;inset:0;background:linear-gradient(90deg,
  rgba(4,20,14,.94) 0%,rgba(4,20,14,.72) 44%,rgba(4,20,14,.25) 100%)}
.d2-in{position:relative;z-index:2;max-width:620px}
.d2 .badge-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.d2 .badge{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.22);color:#eafff6}
.d2 .badge svg{color:#7ff0c8}
.d2-h{font-family:'Fraunces',serif;font-weight:600;font-size:3.2rem;line-height:1.05;
  color:#fff;letter-spacing:-.02em}
.d2-h em{font-style:italic;color:#5eead4}
.d2-sub{color:rgba(255,255,255,.82);font-size:1.06rem;margin:16px 0 26px;max-width:500px}
.d2-cta{display:flex;gap:12px;flex-wrap:wrap}
.d2 .btn-ghost{border-color:rgba(255,255,255,.4);color:#fff;background:transparent}
""",
        html=f"""
<section class="hero-draft d2">
  <div class="d2-bg"><img src="../assets/lab/lab-interior.jpg" alt=""></div>
  <div class="d2-ov"></div>
  <div class="wrap d2-in">
    <div class="badge-row">{BADGES}</div>
    <h1 class="d2-h">Health checkups at home,<br>done <em>right</em>.</h1>
    <p class="d2-sub">NABL-accredited diagnostics with free home sample collection.
       Digital reports in 24 hours.</p>
    <div class="d2-cta">
      <button class="btn btn-primary">Book a Checkup</button>
      <a class="btn btn-ghost"><svg style="width:17px;height:17px"><use href="#i-phone"/></svg> Talk to us</a>
    </div>
  </div>
</section>
""",
    ),

    # ── 3 · whole horizontal gradient band ───────────────────────────────────
    dict(
        name="Horizontal Band · Centered",
        desc="A whole-width brand-gradient band, centered headline and a strip of "
             "trust numbers. No photo — loads instantly and reads like a statement.",
        css="""
.hero-draft.d3{position:relative;z-index:1;overflow:hidden;padding:60px 0;
  background:linear-gradient(120deg,var(--accent) 0%,var(--accent-dark) 100%)}
.hero-draft.d3::after{content:'';position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.14) 1px,transparent 1px);
  background-size:22px 22px;opacity:.5}
.d3-in{position:relative;z-index:2;text-align:center;max-width:780px;margin:0 auto}
.d3 .badge-row{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:20px}
.d3 .badge{background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.25);color:#fff}
.d3 .badge svg{color:#fff}
.d3-h{font-family:'Fraunces',serif;font-weight:600;font-size:3.3rem;line-height:1.06;
  color:#fff;letter-spacing:-.02em}
.d3-h em{font-style:italic;color:#d1fae5}
.d3-sub{color:rgba(255,255,255,.9);font-size:1.08rem;margin:16px auto 26px;max-width:560px}
.d3-cta{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.d3 .btn-primary{background:#fff;color:var(--accent-dark)}
.d3 .btn-ghost{border-color:rgba(255,255,255,.5);color:#fff;background:transparent}
.d3-stats{display:flex;gap:38px;justify-content:center;margin-top:32px;flex-wrap:wrap}
.d3-stat b{font-family:'Fraunces',serif;font-size:1.7rem;color:#fff;display:block}
.d3-stat span{font-size:.8rem;color:rgba(255,255,255,.8)}
""",
        html=f"""
<section class="hero-draft d3"><div class="wrap d3-in">
  <div class="badge-row">{BADGES}</div>
  <h1 class="d3-h">Full body checkups at home,<br><em>starting ₹999</em>.</h1>
  <p class="d3-sub">NABL-accredited labs. Free home sample collection. Digital reports
     within 24 hours — trusted by 50 lakh+ families.</p>
  <div class="d3-cta">
    <button class="btn btn-primary">Book a Checkup</button>
    <a class="btn btn-ghost">View Packages</a>
  </div>
  <div class="d3-stats">
    <div class="d3-stat"><b>50L+</b><span>Tests done</span></div>
    <div class="d3-stat"><b>60+</b><span>Cities served</span></div>
    <div class="d3-stat"><b>4.9★</b><span>3,336 reviews</span></div>
    <div class="d3-stat"><b>24 hrs</b><span>Report time</span></div>
  </div>
</div></section>
""",
    ),

    # ── 4 · centered minimal with search ─────────────────────────────────────
    dict(
        name="Search-first · Minimal",
        desc="Clean, lots of white space, a big search bar as the hero action plus "
             "quick-pick chips. Modern SaaS feel and very conversion-focused.",
        css="""
.hero-draft.d4{position:relative;z-index:1;background:var(--bg);padding:58px 0 62px;
  text-align:center;border-bottom:1px solid var(--border)}
.d4-ey{display:inline-flex;align-items:center;gap:8px;font-size:.8rem;font-weight:600;
  color:var(--accent);background:var(--accent-soft);border:1px solid var(--border);
  padding:6px 14px;border-radius:100px;margin-bottom:18px}
.d4-h{font-family:'Fraunces',serif;font-weight:600;font-size:3.4rem;line-height:1.05;
  letter-spacing:-.02em;color:var(--text);max-width:760px;margin:0 auto}
.d4-h em{font-style:italic;color:var(--accent)}
.d4-sub{color:var(--text-soft);font-size:1.08rem;margin:16px auto 26px;max-width:540px}
.d4-search{display:flex;gap:8px;max-width:580px;margin:0 auto;background:var(--surface);
  border:1px solid var(--border);border-radius:100px;padding:8px 8px 8px 20px;
  box-shadow:var(--shadow-lg);align-items:center}
.d4-search>svg{width:18px;height:18px;color:var(--text-soft);flex:none}
.d4-search input{flex:1;border:none;outline:none;background:transparent;font-family:inherit;
  font-size:1rem;color:var(--text-soft)}
.d4-chips{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:18px}
.d4-chip{font-size:.82rem;color:var(--text-soft);background:var(--bg-soft);
  border:1px solid var(--border);padding:7px 14px;border-radius:100px}
""",
        html="""
<section class="hero-draft d4"><div class="wrap">
  <div class="d4-ey"><svg style="width:14px;height:14px"><use href="#i-shield"/></svg> NABL Accredited · 60+ Cities</div>
  <h1 class="d4-h">What would you like to <em>check today?</em></h1>
  <p class="d4-sub">Search 450+ lab tests &amp; health packages. Free home collection,
     reports in 24 hours.</p>
  <div class="d4-search">
    <svg><use href="#i-scan"/></svg>
    <input value="Full body checkup, thyroid, vitamin D…" readonly>
    <button class="btn btn-primary">Search</button>
  </div>
  <div class="d4-chips">
    <span class="d4-chip">Full Body Checkup</span><span class="d4-chip">Thyroid Profile</span>
    <span class="d4-chip">Diabetes Care</span><span class="d4-chip">Vitamin D</span>
    <span class="d4-chip">Complete Blood Count</span>
  </div>
</div></section>
""",
    ),

    # ── 5 · offer-led promo ──────────────────────────────────────────────────
    dict(
        name="Offer Banner · Promo",
        desc="A marketing-style banner card that leads with the price. Great for "
             "seasonal campaigns and paid-ad landing — pushes the booking action hard.",
        css="""
.hero-draft.d5{position:relative;z-index:1;background:var(--bg-soft);padding:44px 0 52px}
.d5-card{position:relative;overflow:hidden;border-radius:24px;padding:38px 40px;
  display:grid;grid-template-columns:1.3fr .7fr;gap:28px;align-items:center;
  box-shadow:var(--shadow-lg);
  background:linear-gradient(120deg,var(--accent) 0%,var(--accent-dark) 100%)}
.d5-card::after{content:'';position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.12) 1px,transparent 1px);
  background-size:20px 20px;opacity:.5}
.d5-copy{position:relative;z-index:2}
.d5-tag{display:inline-flex;align-items:center;gap:7px;font-size:.72rem;font-weight:700;
  letter-spacing:1px;text-transform:uppercase;color:var(--accent-dark);background:#fff;
  padding:6px 12px;border-radius:100px;margin-bottom:14px}
.d5-h{font-family:'Fraunces',serif;font-weight:600;font-size:2.7rem;line-height:1.08;color:#fff}
.d5-h em{font-style:italic;color:#d1fae5}
.d5-sub{color:rgba(255,255,255,.9);margin:12px 0 22px;font-size:1.02rem}
.d5-cta{display:flex;gap:12px;flex-wrap:wrap}
.d5 .btn-primary{background:#fff;color:var(--accent-dark)}
.d5 .btn-ghost{border-color:rgba(255,255,255,.5);color:#fff}
.d5-price{position:relative;z-index:2;background:rgba(255,255,255,.14);
  border:1px solid rgba(255,255,255,.28);border-radius:18px;padding:22px;text-align:center;color:#fff}
.d5-price .lbl{font-size:.8rem;color:rgba(255,255,255,.85)}
.d5-price .amt{font-family:'Fraunces',serif;font-size:3rem;font-weight:700;line-height:1}
.d5-price .amt s{font-size:1.1rem;opacity:.7;font-weight:400;margin-left:6px}
.d5-price .note{font-size:.78rem;color:rgba(255,255,255,.85);margin-top:6px}
""",
        html="""
<section class="hero-draft d5"><div class="wrap"><div class="d5-card">
  <div class="d5-copy">
    <span class="d5-tag"><svg style="width:13px;height:13px"><use href="#i-star"/></svg> Limited period offer</span>
    <h1 class="d5-h">Full Body Checkup at home, <em>now ₹999</em>.</h1>
    <p class="d5-sub">80+ parameters · Free home sample collection · NABL-accredited ·
       Reports in 24 hours.</p>
    <div class="d5-cta">
      <button class="btn btn-primary">Book &amp; Save</button>
      <a class="btn btn-ghost"><svg style="width:16px;height:16px"><use href="#i-phone"/></svg> 8860 606 141</a>
    </div>
  </div>
  <div class="d5-price">
    <div class="lbl">Starting at</div>
    <div class="amt">₹999<s>₹2,449</s></div>
    <div class="note">Save 59% · all-inclusive</div>
  </div>
</div></div></section>
""",
    ),
]


INJECT = r"""
(function(){
  var root=document.documentElement;
  root.setAttribute('data-theme','light');
  var kill=document.createElement('style');
  kill.textContent='*{animation:none!important;transition:none!important;'
    +'scroll-behavior:auto!important}.reveal{opacity:1!important;transform:none!important}';
  document.head.appendChild(kill);
  document.querySelectorAll('.reveal').forEach(function(e){e.classList.add('visible');});
  var st=document.createElement('style'); st.textContent=%CSS%; document.head.appendChild(st);
  var hero=document.querySelector('.hero'); if(hero){ hero.outerHTML=%HTML%; }
  var el=document.querySelector('.hero-draft');
  var r=el.getBoundingClientRect();
  return Math.ceil(r.bottom + window.scrollY);
})()
"""


def capture_draft(dbg, site_url, idx, draft):
    import json
    tgt = mdp.http_json(f"{dbg}/json/new?about:blank", method="PUT")
    ws = mdp.WS(tgt["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        ws.call("Emulation.setDeviceMetricsOverride",
                {"width": VIEW_W, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        ws.call("Page.navigate", {"url": site_url})
        ws.wait_event("Page.loadEventFired", timeout=30)
        time.sleep(1.0)
        expr = (INJECT
                .replace("%CSS%", json.dumps(draft["css"]))
                .replace("%HTML%", json.dumps(draft["html"])))
        res = ws.call("Runtime.evaluate",
                      {"expression": expr, "returnByValue": True}, timeout=60)
        height = int(res.get("result", {}).get("value") or 760)
        ws.call("Emulation.setDeviceMetricsOverride",
                {"width": VIEW_W, "height": height, "deviceScaleFactor": 1, "mobile": False})
        time.sleep(0.4)
        shot = ws.call("Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": True, "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": VIEW_W, "height": height, "scale": SCALE},
        }, timeout=120)
        name = f"draft-{idx}.png"
        with open(os.path.join(OUTDIR, name), "wb") as f:
            f.write(base64.b64decode(shot["data"]))
        print(f"  captured {idx}. {draft['name']}  ({VIEW_W*SCALE}px × {height*SCALE}px)")
        return name
    finally:
        try:
            mdp.http_json(f"{dbg}/json/close/{tgt['id']}")
        except Exception:
            pass
        ws.close()


def build_presentation(shots):
    date = datetime.now().strftime("%d %b %Y")
    pages = ""
    for i, (draft, src) in enumerate(zip(DRAFTS, shots), 1):
        pages += f"""
    <section class="page">
      <div class="dhead">
        <span class="dnum">Draft {i} of {len(DRAFTS)}</span>
        <h2 class="dname">{draft['name']}</h2>
        <p class="ddesc">{draft['desc']}</p>
      </div>
      <div class="win">
        <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
          <span class="url">biocityhealthcare.com</span></div>
        <img src="{src}" alt="{draft['name']}">
      </div>
    </section>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
@page{{size:A4;margin:0}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:-apple-system,'Segoe UI',sans-serif;color:#10251b}}
.cover{{height:297mm;display:flex;flex-direction:column;justify-content:center;padding:0 26mm;
  background:linear-gradient(150deg,#0b3d33,#0e1512 70%);color:#eafff7}}
.cover .k{{font:600 12px/1 ui-monospace,monospace;letter-spacing:3px;text-transform:uppercase;
  color:#5eead4;margin-bottom:20px}}
.cover h1{{font-size:50px;font-weight:800;letter-spacing:-1.5px;line-height:1.06;margin-bottom:16px}}
.cover h1 span{{color:#34d399}}
.cover p{{font-size:16px;color:#9fc7bd;max-width:470px;line-height:1.6}}
.cover .meta{{margin-top:40px;display:flex;gap:10px;flex-wrap:wrap}}
.cover .meta b{{font:600 12px/1 ui-monospace,monospace;letter-spacing:1px;background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.16);padding:9px 14px;border-radius:100px;color:#d7fff2}}
.page{{break-before:page;height:297mm;padding:15mm 15mm;display:flex;flex-direction:column;
  background:#eef1f0}}
.dhead{{margin-bottom:12px}}
.dnum{{font:700 11px/1 ui-monospace,monospace;letter-spacing:2px;text-transform:uppercase;color:#059669}}
.dname{{font-size:24px;font-weight:800;letter-spacing:-.5px;margin:8px 0 6px}}
.ddesc{{font-size:12.5px;color:#5b6d64;line-height:1.55;max-width:165mm}}
.win{{margin-top:6px;border:1px solid #e3e8e6;border-radius:12px;overflow:hidden;background:#fff;
  box-shadow:0 18px 50px rgba(14,21,18,.14)}}
.bar{{height:36px;display:flex;align-items:center;gap:7px;padding:0 16px;background:#f6f8f7;
  border-bottom:1px solid #e3e8e6}}
.dot{{width:11px;height:11px;border-radius:50%}}
.dot.r{{background:#ff5f57}}.dot.y{{background:#febc2e}}.dot.g{{background:#28c840}}
.url{{margin-left:14px;font:500 12px/1 ui-monospace,monospace;color:#6b7a76;background:#fff;
  border:1px solid #e3e8e6;padding:6px 16px;border-radius:100px}}
.win img{{width:100%;display:block}}
</style></head><body>
<div class="cover">
  <div class="k">Biocity Healthcare · v3</div>
  <h1>Homepage banner<br><span>design drafts</span></h1>
  <p>{len(DRAFTS)} directions for the top of the home page — same brand, header and
     colours, different hero treatment. Pick one (or mix ideas) and we'll build it out.</p>
  <div class="meta"><b>{len(DRAFTS)} drafts</b><b>Desktop · Light</b><b>{date}</b></div>
</div>
{pages}
</body></html>"""


def render_pdf(dbg, pres_path):
    tgt = mdp.http_json(f"{dbg}/json/new?about:blank", method="PUT")
    ws = mdp.WS(tgt["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        ws.call("Emulation.setDeviceMetricsOverride",
                {"width": 1240, "height": 1754, "deviceScaleFactor": 1, "mobile": False})
        ws.call("Page.navigate", {"url": "file://" + pres_path})
        ws.wait_event("Page.loadEventFired", timeout=30)
        time.sleep(1.5)
        res = ws.call("Page.printToPDF", {
            "printBackground": True, "preferCSSPageSize": True,
            "marginTop": 0, "marginBottom": 0, "marginLeft": 0, "marginRight": 0,
        }, timeout=120)
        out = os.path.join(OUTDIR, "Biocity-v3-Banner-Drafts.pdf")
        with open(out, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        return out
    finally:
        try:
            mdp.http_json(f"{dbg}/json/close/{tgt['id']}")
        except Exception:
            pass
        ws.close()


def main():
    if not os.path.exists(mdp.CHROME):
        sys.exit("Google Chrome not found at the expected path.")
    os.makedirs(OUTDIR, exist_ok=True)

    web_port = mdp.free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", web_port),
                                partial(SimpleHTTPRequestHandler, directory=ROOT))
    httpd.RequestHandlerClass.log_message = lambda *a, **k: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    site_url = f"http://127.0.0.1:{web_port}{SITE}"
    print(f"serving site at {site_url}")

    dbg_port = mdp.free_port()
    profile = tempfile.mkdtemp(prefix="biocity-banner-")
    proc = subprocess.Popen(
        [mdp.CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--no-first-run", "--no-default-browser-check", "--disable-extensions",
         "--force-color-profile=srgb", "--font-render-hinting=none",
         f"--remote-debugging-port={dbg_port}", f"--user-data-dir={profile}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    dbg = f"http://127.0.0.1:{dbg_port}"
    for _ in range(100):
        try:
            mdp.http_json(f"{dbg}/json/version")
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        sys.exit("Chrome DevTools endpoint did not come up.")

    try:
        print("capturing banner drafts…")
        shots = [capture_draft(dbg, site_url, i, d) for i, d in enumerate(DRAFTS, 1)]
        print("composing approval PDF…")
        pres_path = os.path.join(OUTDIR, "_banner-drafts.html")
        with open(pres_path, "w") as f:
            f.write(build_presentation(shots))
        pdf = render_pdf(dbg, pres_path)
        print(f"\n✓ PDF ready: {pdf}")
    finally:
        proc.terminate()
        httpd.shutdown()


if __name__ == "__main__":
    main()
