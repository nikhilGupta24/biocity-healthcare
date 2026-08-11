#!/usr/bin/env python3
"""
Biocity — homepage banner (hero) drafts, IMAGE-LED set → one approval PDF.

Every draft features a real photo (or a product card). Loads the real v3 site
in headless Chrome, swaps the hero for each candidate, and captures the top
section (header + banner) at high DPI in BOTH desktop and mobile — laid out as
a browser frame (desktop) and a phone frame (mobile), one draft per spread.

    python3 make_banner_drafts_v2.py

Output: design-export/Biocity-v3-Banner-Drafts-Images.pdf
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

# (viewport width, device-pixel-ratio, mobile-emulation)
VIEWS = {
    "desktop": (1280, 2, False),
    "mobile": (390, 3, True),
}

BADGES = (
    '<span class="badge"><svg><use href="#i-shield"/></svg> NABL Accredited</span>'
    '<span class="badge"><svg><use href="#i-home"/></svg> Free Home Collection</span>'
    '<span class="badge"><svg><use href="#i-clock"/></svg> Reports in 24 Hrs</span>'
)
STARS = '<svg><use href="#i-star"/></svg>' * 5


DRAFTS = [
    # ── 1 · split editorial (liked) ──────────────────────────────────────────
    dict(
        name="Split · Editorial",
        desc="Headline & CTA on the left, real photo on the right with a floating "
             "status chip. Clean and premium — one of the two you liked.",
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
@media(max-width:640px){
  .hero-draft.d1{padding:28px 0 34px}
  .d1-grid{grid-template-columns:1fr;gap:26px}
  .d1-h{font-size:2.1rem}.d1-sub{font-size:.98rem}
  .d1-media img{aspect-ratio:4/3}
  .d1-float{left:10px;bottom:10px;padding:9px 11px}
}
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

    # ── 2 · full-bleed image, text overlay (liked) ───────────────────────────
    dict(
        name="Full-width Image · Text on it",
        desc="One edge-to-edge lab photo with a gradient wash and the message laid "
             "over it. Bold, flagship feel — the option you kept.",
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
@media(max-width:640px){
  .hero-draft.d2{min-height:0;padding:40px 0}
  .d2-h{font-size:2.1rem}.d2-sub{font-size:.98rem}
  .d2-ov{background:linear-gradient(180deg,rgba(4,20,14,.5),rgba(4,20,14,.86))}
}
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

    # ── 3 · photo + floating package/price card ──────────────────────────────
    dict(
        name="Package Card · over photo",
        desc="Photo on the right with a floating package + price card — shows a real "
             "product the moment they land. Strong for bookings.",
        css="""
.hero-draft.d3{position:relative;z-index:1;background:var(--bg-soft);
  border-bottom:1px solid var(--border);padding:44px 0 54px}
.d3-grid{display:grid;grid-template-columns:1.02fr .98fr;gap:44px;align-items:center}
.d3 .badge-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.d3-h{font-family:'Fraunces',serif;font-weight:600;font-size:2.9rem;line-height:1.05;
  letter-spacing:-.02em;color:var(--text)}
.d3-h em{font-style:normal;color:var(--accent)}
.d3-h i{font-style:normal;color:#0e9aa7}
.d3-tag{display:block;font-family:'Fraunces',serif;font-style:italic;font-weight:500;
  font-size:1.35rem;color:var(--text-soft);margin-top:6px}
.d3-sub{font-size:1.02rem;color:var(--text-soft);margin:16px 0 24px;max-width:430px}
.d3-cta{display:flex;gap:12px;flex-wrap:wrap}
.d3-photo{position:relative;border-radius:22px;overflow:hidden;box-shadow:var(--shadow-lg);aspect-ratio:4/3}
.d3-photo>img{width:100%;height:100%;object-fit:cover}
.d3-pkg{position:absolute;left:16px;bottom:16px;width:250px;background:var(--surface);
  border:1px solid var(--border);border-radius:16px;box-shadow:var(--shadow-lg);padding:15px}
.d3-pkg h4{font-size:.92rem;color:var(--text);display:flex;align-items:center;gap:8px;margin:0}
.d3-pkg h4 svg{width:16px;height:16px;color:var(--accent);flex:none}
.d3-pkg .rows{margin:10px 0}
.d3-pkg .row{display:flex;align-items:center;gap:8px;font-size:.79rem;color:var(--text-soft);padding:3px 0}
.d3-pkg .row svg{width:14px;height:14px;color:var(--accent);flex:none}
.d3-pkg .pr{display:flex;align-items:baseline;gap:8px;margin-top:2px}
.d3-pkg .pr b{font-family:'Fraunces',serif;font-size:1.5rem;color:var(--text)}
.d3-pkg .pr s{font-size:.82rem;color:var(--text-soft)}
.d3-pkg .bk{margin-top:10px;text-align:center;background:var(--accent);color:#fff;
  border-radius:10px;padding:9px;font-size:.83rem;font-weight:600}
@media(max-width:640px){
  .hero-draft.d3{padding:28px 0 34px}
  .d3-grid{grid-template-columns:1fr;gap:26px}
  .d3-h{font-size:2rem}.d3-tag{font-size:1.15rem}
  .d3-photo{aspect-ratio:4/3}
  .d3-pkg{width:210px;left:12px;bottom:12px;padding:13px}
}
""",
        html=f"""
<section class="hero-draft d3"><div class="wrap d3-grid">
  <div>
    <div class="badge-row">{BADGES}</div>
    <h1 class="d3-h">Health checks that <em>come</em> <i>to you</i>.
      <span class="d3-tag">Not the other way around.</span></h1>
    <p class="d3-sub">Full body checkups from your couch. 80+ parameters,
       NABL-certified accuracy, reports within 24 hours.</p>
    <div class="d3-cta">
      <button class="btn btn-primary">Find My Test</button>
      <a class="btn btn-ghost"><svg style="width:16px;height:16px"><use href="#i-phone"/></svg> Call us free</a>
    </div>
  </div>
  <div class="d3-photo">
    <img src="../assets/lab/phlebotomy.png" alt="">
    <div class="d3-pkg">
      <h4><svg><use href="#i-scan"/></svg> Advanced · 100+ params</h4>
      <div class="rows">
        <div class="row"><svg><use href="#i-check"/></svg> Everything in Comprehensive</div>
        <div class="row"><svg><use href="#i-check"/></svg> Cancer Markers · 5 tests</div>
        <div class="row"><svg><use href="#i-check"/></svg> Hormone Panel · 6 tests</div>
      </div>
      <div class="pr"><b>₹2,999</b><s>₹6,800</s></div>
      <div class="bk">Book Advanced</div>
    </div>
  </div>
</div></section>
""",
    ),

    # ── 4 · bento photo grid ─────────────────────────────────────────────────
    dict(
        name="Bento · Photo grid",
        desc="A modern tile grid mixing two real photos with a stat tile and a rating "
             "tile. Feels fresh, visual and trustworthy.",
        css="""
.hero-draft.d4{position:relative;z-index:1;background:var(--bg);padding:44px 0 52px;
  border-bottom:1px solid var(--border)}
.d4-grid{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}
.d4 .badge-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.d4-h{font-family:'Fraunces',serif;font-weight:600;font-size:3rem;line-height:1.06;
  letter-spacing:-.02em;color:var(--text)}
.d4-h em{font-style:italic;color:var(--accent)}
.d4-sub{font-size:1.02rem;color:var(--text-soft);margin:16px 0 24px;max-width:430px}
.d4-cta{display:flex;gap:12px;flex-wrap:wrap}
.d4-bento{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:14px;height:392px}
.d4-bento>div{border-radius:18px;overflow:hidden;position:relative;box-shadow:var(--shadow)}
.d4-ph img{width:100%;height:100%;object-fit:cover}
.d4-stat{background:linear-gradient(135deg,var(--accent),var(--accent-dark));color:#fff;
  display:flex;flex-direction:column;justify-content:center;padding:18px}
.d4-stat b{font-family:'Fraunces',serif;font-size:2rem;line-height:1}
.d4-stat span{font-size:.82rem;color:rgba(255,255,255,.85);margin-top:6px}
.d4-rate{background:var(--surface);border:1px solid var(--border);display:flex;
  flex-direction:column;justify-content:center;padding:18px}
.d4-rate .st{display:flex;gap:2px}
.d4-rate .st svg{width:15px;height:15px;fill:#f59e0b;color:#f59e0b}
.d4-rate b{font-size:1.1rem;color:var(--text);margin-top:8px}
.d4-rate span{font-size:.77rem;color:var(--text-soft)}
@media(max-width:640px){
  .hero-draft.d4{padding:28px 0 34px}
  .d4-grid{grid-template-columns:1fr;gap:24px}
  .d4-h{font-size:2.1rem}
  .d4-bento{height:300px;gap:12px}
}
""",
        html=f"""
<section class="hero-draft d4"><div class="wrap d4-grid">
  <div>
    <div class="badge-row">{BADGES}</div>
    <h1 class="d4-h">Diagnostics that feel <em>effortless</em>.</h1>
    <p class="d4-sub">From home collection to a digital report — one simple flow.
       80+ parameters, NABL-certified, delivered in 24 hours.</p>
    <div class="d4-cta">
      <button class="btn btn-primary">Book a Checkup</button>
      <a class="btn btn-ghost"><svg style="width:16px;height:16px"><use href="#i-phone"/></svg> Talk to us</a>
    </div>
  </div>
  <div class="d4-bento">
    <div class="d4-ph"><img src="../assets/lab/phlebotomy.png" alt=""></div>
    <div class="d4-ph"><img src="../assets/lab/lab-interior.jpg" alt=""></div>
    <div class="d4-stat"><b>24 hr</b><span>Digital reports on WhatsApp &amp; email</span></div>
    <div class="d4-rate"><div class="st">{STARS}</div><b>4.9 / 5</b><span>3,336 verified reviews</span></div>
  </div>
</div></section>
""",
    ),

    # ── 5 · diagonal split with photo ────────────────────────────────────────
    dict(
        name="Diagonal Split · Photo",
        desc="Copy on the left, photo sweeping in from the right on a diagonal edge, "
             "with a floating report chip. Dynamic and modern.",
        css="""
.hero-draft.d6{position:relative;z-index:1;background:var(--bg-soft);overflow:hidden;
  min-height:520px;display:flex;align-items:center}
.d6-copy{position:relative;z-index:2;width:54%;padding:44px 0}
.d6 .badge-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.d6-h{font-family:'Fraunces',serif;font-weight:600;font-size:3.1rem;line-height:1.05;
  letter-spacing:-.02em;color:var(--text)}
.d6-h em{font-style:italic;color:var(--accent)}
.d6-sub{font-size:1.02rem;color:var(--text-soft);margin:16px 0 24px;max-width:420px}
.d6-cta{display:flex;gap:12px;flex-wrap:wrap}
.d6-media{position:absolute;top:0;right:0;bottom:0;width:52%;
  clip-path:polygon(16% 0,100% 0,100% 100%,0 100%)}
.d6-media img{width:100%;height:100%;object-fit:cover}
.d6-chip{position:absolute;right:30px;bottom:28px;z-index:3;display:flex;align-items:center;gap:10px;
  background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px 14px;box-shadow:var(--shadow-lg)}
.d6-chip>svg{width:20px;height:20px;color:var(--accent);flex:none}
.d6-chip b{display:block;font-size:.87rem;color:var(--text)}
.d6-chip small{font-size:.74rem;color:var(--text-soft)}
@media(max-width:640px){
  .hero-draft.d6{display:block;min-height:0}
  .d6-copy{width:100%;padding:30px 0 22px}
  .d6-h{font-size:2.1rem}
  .d6-media{position:relative;width:100%;height:250px;clip-path:none}
  .d6-chip{right:16px;bottom:16px}
}
""",
        html=f"""
<section class="hero-draft d6">
  <div class="wrap">
    <div class="d6-copy">
      <div class="badge-row">{BADGES}</div>
      <h1 class="d6-h">Lab tests at home,<br>results you can <em>trust</em>.</h1>
      <p class="d6-sub">Certified phlebotomists collect your sample at home — free.
         NABL-accredited labs, reports in 24 hours.</p>
      <div class="d6-cta">
        <button class="btn btn-primary">Book a Checkup</button>
        <a class="btn btn-ghost"><svg style="width:16px;height:16px"><use href="#i-phone"/></svg> Talk to us</a>
      </div>
    </div>
  </div>
  <div class="d6-media"><img src="../assets/lab/phlebotomy.png" alt=""></div>
  <div class="d6-chip"><svg><use href="#i-file"/></svg>
    <div><b>Report in 24 hrs</b><small>WhatsApp &amp; email</small></div></div>
</section>
""",
    ),

    # ── 6 · package-card carousel, illustrated (with arrows) ─────────────────
    dict(
        name="Package Carousel · Illustrated",
        desc="Your reference — a stacked package-card carousel with arrow controls "
             "(auto-plays and users can scroll too), plus trust chips beneath.",
        css="""
.hero-draft.d7{position:relative;z-index:1;background:var(--bg-soft);
  border-bottom:1px solid var(--border);padding:42px 0 46px;overflow:hidden}
.d7-grid{display:grid;grid-template-columns:1.02fr .98fr;gap:40px;align-items:center;
  position:relative;z-index:2}
.d7-iso{display:inline-flex;align-items:center;gap:8px;font-size:.78rem;font-weight:600;
  color:var(--text-soft);background:var(--surface);border:1px solid var(--border);
  padding:7px 14px;border-radius:100px;margin-bottom:20px}
.d7-iso .d{width:7px;height:7px;border-radius:50%;background:var(--accent)}
.d7-h{font-family:'Fraunces',serif;font-weight:600;font-size:3.2rem;line-height:1.03;
  letter-spacing:-.02em;color:var(--text)}
.d7-h em{font-style:normal;color:var(--accent)}
.d7-tag{display:block;font-family:'Fraunces',serif;font-style:italic;font-weight:500;
  font-size:1.5rem;color:var(--text-soft);margin-top:8px}
.d7-sub{font-size:1.02rem;color:var(--text-soft);margin:18px 0 26px;max-width:450px}
.d7-cta{display:flex;gap:12px;flex-wrap:wrap}
.d7-proof{display:flex;align-items:center;gap:20px;margin-top:24px;font-size:.85rem;color:var(--text-soft)}
.d7-proof .st{display:inline-flex;gap:1px;vertical-align:middle}
.d7-proof .st svg{width:14px;height:14px;fill:#f59e0b;color:#f59e0b}
.d7-proof b{color:var(--text)}
.d7-cards{position:relative;height:400px}
.d7-cards::before{content:'';position:absolute;left:-2%;top:6%;width:72%;height:80%;border-radius:50%;
  background:radial-gradient(circle,rgba(5,150,105,.07),transparent 70%)}
.d7-ghost{position:absolute;background:var(--surface);border:1px solid var(--border);
  border-radius:20px;box-shadow:var(--shadow)}
.d7-ghost.g2{top:10px;right:2px;width:78%;height:84%;transform:rotate(2.5deg);opacity:.55}
.d7-ghost.g1{top:16px;right:10px;width:80%;height:86%;opacity:.85}
.d7-card{position:absolute;top:0;right:24px;width:82%;background:var(--surface);
  border:1px solid var(--border);border-top:3px solid var(--accent);border-radius:20px;
  box-shadow:var(--shadow-lg);padding:20px}
.d7-card .hd{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.d7-card .ic{width:34px;height:34px;border-radius:9px;background:var(--accent-soft);
  display:flex;align-items:center;justify-content:center;flex:none}
.d7-card .ic svg{width:18px;height:18px;color:var(--accent)}
.d7-card .hd b{font-size:1rem;color:var(--text);display:block}
.d7-card .hd small{font-size:.76rem;color:var(--text-soft)}
.d7-row{display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:9px 12px;border:1px solid var(--border);border-radius:10px;margin-bottom:8px}
.d7-row .l{display:flex;align-items:center;gap:8px;font-size:.82rem;color:var(--text)}
.d7-row .l svg{width:15px;height:15px;color:var(--accent);flex:none}
.d7-row .pill{font-size:.67rem;color:var(--accent);background:var(--accent-soft);
  border-radius:100px;padding:3px 9px;font-weight:600;flex:none}
.d7-foot{display:flex;align-items:center;justify-content:space-between;margin:14px 2px 0}
.d7-foot .pr b{font-family:'Fraunces',serif;font-size:1.55rem;color:var(--text)}
.d7-foot .pr s{font-size:.84rem;color:var(--text-soft);margin-left:6px}
.d7-foot .save{font-size:.68rem;font-weight:700;letter-spacing:.5px;color:var(--accent);
  border:1px solid var(--accent);border-radius:100px;padding:5px 10px}
.d7-book{margin-top:14px;text-align:center;background:var(--accent);color:#fff;
  border-radius:12px;padding:12px;font-size:.9rem;font-weight:600}
.d7-dots{position:absolute;bottom:0;left:50%;transform:translateX(-50%);display:flex;gap:6px}
.d7-dots i{width:7px;height:7px;border-radius:50%;background:var(--border)}
.d7-dots i.on{width:20px;border-radius:100px;background:var(--accent)}
.d7-nav{position:absolute;top:42%;width:34px;height:34px;border-radius:50%;background:var(--surface);
  border:1px solid var(--border);box-shadow:var(--shadow-lg);display:flex;align-items:center;
  justify-content:center;z-index:5;cursor:pointer}
.d7-nav svg{width:16px;height:16px;color:var(--text)}
.d7-nav.l{left:-8px}.d7-nav.l svg{transform:rotate(90deg)}
.d7-nav.r{right:-8px}.d7-nav.r svg{transform:rotate(-90deg)}
@media(max-width:640px){
  .hero-draft.d7{padding:28px 0 30px}
  .d7-grid{grid-template-columns:1fr;gap:28px}
  .d7-h{font-size:2.1rem}.d7-tag{font-size:1.2rem}
  .d7-cards{height:370px;margin-top:4px}
  .d7-card{right:auto;left:50%;transform:translateX(-50%);width:300px}
  .d7-ghost.g1{left:50%;transform:translateX(-46%);right:auto}
  .d7-ghost.g2{left:50%;transform:translateX(-52%) rotate(2.5deg);right:auto}
  .d7-nav.l{left:2px}.d7-nav.r{right:2px}
  .d7-proof{flex-wrap:wrap;gap:10px}
  .d7-trust{flex-wrap:wrap;gap:12px}
}
.d7-trust{display:flex;gap:24px;justify-content:center;margin-top:28px;position:relative;z-index:2}
.d7-chip{display:flex;align-items:center;gap:10px;background:var(--surface);
  border:1px solid var(--border);border-radius:14px;padding:10px 16px;box-shadow:var(--shadow)}
.d7-chip .ic{width:30px;height:30px;border-radius:8px;background:var(--accent-soft);
  display:flex;align-items:center;justify-content:center;flex:none}
.d7-chip .ic svg{width:16px;height:16px;color:var(--accent)}
.d7-chip b{display:block;font-size:.85rem;color:var(--text)}
.d7-chip small{font-size:.73rem;color:var(--text-soft)}
""",
        html=f"""
<section class="hero-draft d7"><div class="wrap">
  <div class="d7-grid">
    <div>
      <div class="d7-iso"><span class="d"></span> NABL Accredited · ISO 15189:2022 Certified</div>
      <h1 class="d7-h">Health checks that <em>come to you.</em>
        <span class="d7-tag">Not the other way around.</span></h1>
      <p class="d7-sub">Full body health checkups from your couch. 80+ parameters,
         NABL-certified accuracy, reports within 24 hours. Trusted by 50 lakh+ families
         across 60+ cities.</p>
      <div class="d7-cta">
        <button class="btn btn-primary">Find My Test</button>
        <a class="btn btn-ghost"><svg style="width:16px;height:16px"><use href="#i-phone"/></svg> Call Us Free</a>
      </div>
      <div class="d7-proof">
        <span><span class="st">{STARS}</span> <b>4.9 / 5</b> · 3,300+ reviews</span>
        <span><b>100%</b> Hygienic &amp; Safe</span>
      </div>
    </div>
    <div class="d7-cards">
      <div class="d7-ghost g2"></div>
      <div class="d7-ghost g1"></div>
      <div class="d7-card">
        <div class="hd"><span class="ic"><svg><use href="#i-scan"/></svg></span>
          <span><b>Advanced</b><small>100+ parameters · Executive</small></span></div>
        <div class="d7-row"><span class="l"><svg><use href="#i-check"/></svg> Everything in Comprehensive</span><span class="pill">80+</span></div>
        <div class="d7-row"><span class="l"><svg><use href="#i-check"/></svg> Cancer Markers</span><span class="pill">5 tests</span></div>
        <div class="d7-row"><span class="l"><svg><use href="#i-check"/></svg> Hormone Panel</span><span class="pill">6 tests</span></div>
        <div class="d7-row"><span class="l"><svg><use href="#i-check"/></svg> Arthritis Screening</span><span class="pill">4 tests</span></div>
        <div class="d7-foot"><span class="pr"><b>₹2,999</b><s>₹6,800</s></span><span class="save">SAVE 55%</span></div>
        <div class="d7-book">Book Advanced</div>
      </div>
      <button class="d7-nav l"><svg><use href="#i-chevron"/></svg></button>
      <button class="d7-nav r"><svg><use href="#i-chevron"/></svg></button>
      <div class="d7-dots"><i class="on"></i><i></i><i></i><i></i></div>
    </div>
  </div>
  <div class="d7-trust">
    <div class="d7-chip"><span class="ic"><svg><use href="#i-shield"/></svg></span>
      <div><b>NABL Certified</b><small>Int'l standard accuracy</small></div></div>
    <div class="d7-chip"><span class="ic"><svg><use href="#i-clock"/></svg></span>
      <div><b>24hr Reports</b><small>Email + WhatsApp</small></div></div>
  </div>
</div></section>
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


def capture(dbg, site_url, idx, draft, kind):
    import json
    w, dsf, mobile = VIEWS[kind]
    tgt = mdp.http_json(f"{dbg}/json/new?about:blank", method="PUT")
    ws = mdp.WS(tgt["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        ws.call("Emulation.setDeviceMetricsOverride",
                {"width": w, "height": 900, "deviceScaleFactor": 1, "mobile": mobile})
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
                {"width": w, "height": height, "deviceScaleFactor": 1, "mobile": mobile})
        time.sleep(0.5)
        shot = ws.call("Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": True, "fromSurface": True,
            "clip": {"x": 0, "y": 0, "width": w, "height": height, "scale": dsf},
        }, timeout=120)
        suffix = "" if kind == "desktop" else "-m"
        name = f"imgdraft-{idx}{suffix}.png"
        with open(os.path.join(OUTDIR, name), "wb") as f:
            f.write(base64.b64decode(shot["data"]))
        print(f"  captured {idx}. {draft['name']} · {kind}  ({w*dsf}px × {height*dsf}px)")
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
    for i, (draft, pair) in enumerate(zip(DRAFTS, shots), 1):
        desk, mob = pair
        pages += f"""
    <section class="page">
      <div class="dhead">
        <span class="dnum">Draft {i} of {len(DRAFTS)} · Desktop</span>
        <h2 class="dname">{draft['name']}</h2>
        <p class="ddesc">{draft['desc']}</p>
      </div>
      <div class="win">
        <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
          <span class="url">biocityhealthcare.com</span></div>
        <img src="{desk}" alt="{draft['name']} desktop">
      </div>
    </section>
    <section class="page mob">
      <div class="dhead">
        <span class="dnum">Draft {i} of {len(DRAFTS)} · Mobile</span>
        <h2 class="dname">{draft['name']}</h2>
      </div>
      <div class="phone"><img src="{mob}" alt="{draft['name']} mobile"></div>
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
.page{{break-before:page;min-height:297mm;padding:15mm 15mm;display:flex;flex-direction:column;
  background:#eef1f0}}
.page.mob{{align-items:center}}
.dhead{{margin-bottom:12px;width:100%}}
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
.phone{{width:300px;margin:8px auto 0;border:11px solid #12100f;border-radius:42px;overflow:hidden;
  background:#12100f;box-shadow:0 22px 60px rgba(14,21,18,.22);position:relative}}
.phone img{{width:100%;display:block}}
</style></head><body>
<div class="cover">
  <div class="k">Biocity Healthcare · v3</div>
  <h1>Homepage banner<br><span>image-led drafts</span></h1>
  <p>{len(DRAFTS)} hero directions — every one features a real photo or product card,
     shown in both desktop and mobile. Same brand, header and colours. Pick one and we build it.</p>
  <div class="meta"><b>{len(DRAFTS)} drafts</b><b>Desktop + Mobile</b><b>{date}</b></div>
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
        out = os.path.join(OUTDIR, "Biocity-v3-Banner-Drafts-Images.pdf")
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
    profile = tempfile.mkdtemp(prefix="biocity-banner2-")
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
        print("capturing image-led banner drafts (desktop + mobile)…")
        shots = []
        for i, d in enumerate(DRAFTS, 1):
            desk = capture(dbg, site_url, i, d, "desktop")
            mob = capture(dbg, site_url, i, d, "mobile")
            shots.append((desk, mob))
        print("composing approval PDF…")
        pres_path = os.path.join(OUTDIR, "_banner-drafts-images.html")
        with open(pres_path, "w") as f:
            f.write(build_presentation(shots))
        pdf = render_pdf(dbg, pres_path)
        print(f"\n✓ PDF ready: {pdf}")
    finally:
        proc.terminate()
        httpd.shutdown()


if __name__ == "__main__":
    main()
