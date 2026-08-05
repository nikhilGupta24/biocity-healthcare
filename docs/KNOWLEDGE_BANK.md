# Biocity Healthcare Website — Knowledge Bank

> **Living document — keep it current.** This is the single source of truth for the
> Biocity Healthcare marketing website (the site deployed to GitHub Pages). It is written
> for **peers and AI agents** to get up to speed fast on the technical design, architecture,
> and caveats. If you change the site, **update this file in the same commit** (see
> [§14 Maintenance Protocol](#14-maintenance-protocol)).

- **Last updated:** 2026-07-30
- **Maintainer:** Nikhil Gupta (GitHub `nikhilGupta24`)
- **Supersedes** (for website specifics): the older `docs/BIOCITY_PLAYBOOK.md` and
  `docs/KNOWLEDGE_BANK.html`, which describe an earlier single-file prototype and are now
  **out of date** (the site has since grown to 24 interior pages + shared assets).

---

## 1. TL;DR

A fast, dependency-free, static marketing website for **Biocity Healthcare** — an
NABL-accredited home diagnostics company (full-body checkups, home sample collection,
60+ cities). Dark-first, medical-green theme, cinematic animations, mobile-responsive,
light/dark toggle, print-friendly. No build step, no framework — plain HTML/CSS/JS.

- **Home** (`index.html`): one big self-contained file (inline CSS/JS/SVG sprite).
- **24 interior pages** (`pages/*.html`): share `assets/site.css` + `assets/site.js`.
- **Deployed** via GitHub Pages from the `nikhilGupta24/biocity-healthcare` repo (`main`).

---

## 2. Repos, folders & where things live

There are **two folders**, kept in sync:

| Folder | Role | Notes |
|---|---|---|
| `biocity-redesign/` | **Working source** (edit here) | Also holds planning docs; not a git repo of its own within the deploy sense |
| `biocity-healthcare/` | **Deploy repo** (git) | Pushed to GitHub Pages; peers get access here |

> **Rule of thumb:** *Edit in `biocity-redesign/`, then sync the changed files into
> `biocity-healthcare/` and commit there.* See [§13 Deploy workflow](#13-deploy-workflow).

**Deploy repo git remote** (SSH, uses a host alias so the right key is used):

```
origin  git@github-nikhilgupta24:nikhilGupta24/biocity-healthcare.git   (main)
```

**Hosting:** GitHub Pages, served from repo root of `main`. `.nojekyll` is present so files
are served as-is. Canonical/OG URLs point to `https://biocityhealthcare.com` (the intended
production domain); there is **no `CNAME` file committed** — the custom domain, if used, is
set in the GitHub Pages UI. Until then the site also lives at the `github.io` Pages URL.

### Folder layout (deploy repo)

```
biocity-healthcare/
├── index.html                 # Home (self-contained: inline CSS/JS/SVG sprite)
├── pages/                      # 24 interior pages (share ../assets/site.css + site.js)
│   ├── about-us.html
│   ├── certifications.html     # NABL + 8 ISO + DMC, real certificate scans + lightbox
│   ├── awards.html  media-coverage.html  social-activities.html
│   ├── full-body-checkup.html  preventive-health-checkup.html  offers.html
│   ├── test-cbc.html  test-lipid-profile.html  test-thyroid.html
│   ├── test-blood-sugar.html  test-vitamin-d.html  test-haemoglobin.html  test-kidney-kft.html
│   ├── bmi-calculator.html  contact.html
│   ├── city-noida.html         # city landing (retrofitted early page)
│   ├── condition-diabetes.html # condition landing (retrofitted early page)
│   ├── blog.html  blog-vitamin-d-deficiency.html   # (retrofitted early pages)
│   └── privacy.html  terms.html  refund.html        # legal
├── assets/
│   ├── site.css                # shared design system for interior pages (~520 lines)
│   ├── site.js                 # shared JS + injected SVG icon sprite (~110 lines)
│   ├── certs/  (9)              # real certificate scans (NABL, ISO x7, GLP, DMC)
│   ├── lab/ (7)  team/ (14)  welfare/ (6)  awards/ (18)  social/ (9)   # photos
├── docs/                       # older planning docs (STALE for site specifics)
├── .nojekyll
└── README.md                   # also stale in parts (says "all inlined / few pages")
```

---

## 3. Run / preview locally

Any static server works (all links are relative):

```bash
cd biocity-redesign          # or biocity-healthcare
python3 -m http.server 8080
# Desktop:  http://localhost:8080/index.html
# A page:   http://localhost:8080/pages/certifications.html
```

**Screenshot/QA caveat:** headless Chrome (`--headless=new`) has a **hard minimum viewport
width of ~500px**. Screenshots requested at 414/430px are actually rendered at 500px and
cropped, which produces **false right-edge clipping**. Verify true mobile at **500px** width,
not below. (This bit us before — don't chase phantom clipping.)

---

## 4. Architecture — two rendering strategies (IMPORTANT)

The site deliberately uses **two** strategies. Know which file you're in:

1. **Home (`index.html`) = fully self-contained.**
   - Inline `<style>`, inline `<script>`, inline SVG `<symbol>` sprite.
   - Its **own** mobile menu (`.mmenu`, `toggleMenu()`/`closeMenu()`).
   - Nav links use `pages/…` prefixes.

2. **Interior pages (`pages/*.html`) = shared assets.**
   - `<link rel="stylesheet" href="../assets/site.css">` + `<script src="../assets/site.js">`.
   - SVG icon sprite is **injected by `site.js`** at runtime (not inline in the page).
   - Mobile menu is the **drawer** (`.drawer`, `openDrawer()`/`closeDrawer()`).
   - Nav links use **bare** file names (e.g. `about-us.html`).

> ⚠️ **The #1 gotcha:** the **design tokens and many component styles exist in BOTH**
> `index.html`'s inline `<style>` **and** `assets/site.css`. If you change a shared visual
> (colors, buttons, nav, deck, cards), you often must change it **in both places** or the
> home page and interior pages will drift. Same for JS behaviors that both define.

The **4 earliest pages** (`city-noida`, `condition-diabetes`, `blog`, `blog-vitamin-d-deficiency`)
were **retrofitted**: they use the shared mega-menu + drawer and `site.css`/`site.js`, but may
still carry some inline styles and use a **different footer layout** (no "Company" column), so
site-wide find/replace on footers won't match them (that's expected).

---

## 5. Design system

**Theme:** `data-theme="dark"` default on `<html>`; `toggleTheme()` flips to `light` and
persists in `localStorage('theme')`. Both themes fully tokenized.

**Fonts:** `Fraunces` (display/headings, serif) + `DM Sans` (body/UI). Loaded from Google Fonts.

**Core tokens** (defined per theme; identical names in `site.css` and `index.html` inline):
- Backgrounds: `--bg --bg2 --surface --surface2`
- Glass/borders: `--gl --glH --glB --glBH`
- Text: `--text --text2 --text3 --textI`
- Accent (medical green): `--accent (#10B981 dark / #059669 light) --accentH --accentD --accentS --accentG`
- Secondary: `--accent2 (#0EA5E9)`; Shadows: `--sh --shL`; Mesh gradient: `--mesh`

**Atmosphere layers** (fixed, `z-index:0`, pointer-events:none):
- `.bg-mesh` — radial mesh gradient.
- `.bg-cross` — **graph-paper grid** (two grid scales), radially masked. Reinforces the
  "pulse/medical" motif.
- `.orb .orb-1/2/3` — ambient gradient orbs.
- `.cg` — cursor-follow glow (desktop only).
- `#prog` — top scroll-progress bar.

**Signature motifs:**
- **Pulse dot / heartbeat "ping"** — `.dot`, `.td`, `.eyebrow .td`, `.tag`, `.pulse` (used on
  section tags, badges, icon boxes) via `@keyframes blink` / `tdPing`.
- **Animated atom logo** — inline SVG (`.logo-atom`): static tilted orbit ellipses with
  electrons gliding via CSS `offset-path`; a bubbling lab flask. Small/faint watermark in the
  home hero + the nav brand mark. (History: earlier "orbits flying off" bug was fixed by making
  orbits static and animating only electrons.)
- **ECG line** — animated SVG heartbeat in the home hero (`.hero-ecg`).
- **Reveal-on-scroll** — `.sr` (+ variants `sr-s/-l/-r/-blur`, delays `sr-d1..d5`) toggled to
  `.v` by an `IntersectionObserver`.

---

## 6. Shared components & conventions

| Component | Where | Notes |
|---|---|---|
| **Mega-menu nav** | all pages | `.nav-links` → `.nl-item` → `.mega .mega-g.c2` → `.mega-a`. Tabs: Checkups · Lab Tests · Company · Blog |
| **Mobile drawer** | interior pages | `.drawer` + `openDrawer()/closeDrawer()`; groups mirror the mega-menu |
| **Mobile menu (home only)** | `index.html` | `.mmenu` + `toggleMenu()/closeMenu()` |
| **Footer** | all | `.foot`; interior "template" footer has Checkups/Company/Contact columns |
| **Breadcrumbs** | interior | visible `.bread` **and** matching `BreadcrumbList` JSON-LD |
| **Icon sprite** | — | Inline in `index.html`; **injected by `site.js`** on interior pages. IDs like `#i-shield #i-heart #i-droplet #i-activity #i-award #i-stethoscope #i-scan #i-gauge #i-moon #i-usercheck #i-target #i-check #i-arrow #i-phone #i-chevron #i-star #i-wa #i-fb #i-ig #i-in …` |
| **Coverflow deck** | interior | `initDeck()` in `site.js` runs on every `.deck-wrap` (photo cards `.dcard`, `.deck-dots`, prev/next). Responsive `translateX/Z` recomputed on resize. **Front-card click calls `openModal()`.** |
| **Lightbox** | interior | `site.js` binds to `.gal figure img` **and** any `.lbx` element; uses `data-full` or `src`; keyboard + swipe. |
| **Booking modal** | all | `#modal`, `openModal([pkg])`, `closeModal()`, `submitForm(e)` (shows confirm, resets). |
| **WhatsApp FAB** | all | `.wa` → `wa.me/918860606141` |
| **Mobile action bar** | all | `.mbar#mbar` (Call Now / Book) — shows on scroll (>600px). Mobile only. |
| **Landing atom mark** | all | `.phero-atom` — a **highlighted** animated atom (green tile + glow) in the first landing section of every page. On interior shared-asset pages it is **injected by `site.js`** into the first hero (`.phero-in`/`.hero-c`/`.hero .w`/`.blog-hero`); on `index.html` + the 4 self-contained pages it is **inline markup + inline CSS**. Reuses the `.la-orbit/.la-e/.la-nuc` atom styles. |

**Contact constants:** phone `+91 8860 606 141` (`+918860606141`), email
`care@biocityhealthcare.com`, address `Plot No 434, 2nd Floor, Jagriti Enclave, Vikas Marg,
Delhi 110092`. Founder/CEO **Shubham Jain**.

---

## 7. Home page (`index.html`) — section by section

Top → bottom:

1. **Lab Finder console** (`.finder`, top of page — the primary hero; added 2026-07-30).
   Inspired by 1mg's labs landing.
   - `.finder-bg` — **4 aligned, symmetric, STATIC** background photos (`.ff1..4`, mirrored
     left/right, equal size). They are **lab/medical photos only** (`assets/lab/*`) — no float,
     no parallax (removed on request: "images should not be off-topic and should not be
     moving"). The section has a **solid `--bg`** so the site-wide graph-paper grid does **not**
     show through this first section (removed on request: "grid lines… feel cluttered").
   - **Highlighted BioCity atom** (`.phero-atom`) sits above the badge — see §6.
   - `.hi-rail` — **foreground highlight rail**: 4 captioned photo cards (NABL Lab · Free Home
     Collection · Safe Cold-Chain · 39L+ Families).
   - **Live search** `#cFind` — filters `.tile`s as you type (clones matches into `#cSearch`);
     Enter/"Search" navigates to the first match, else scrolls to `#recommender`.
   - **Category console** — tabs `.ctab` (Popular · By Age & Gender · Health Concerns · Full
     Body · Individual Tests) switch `.cpanel`s of `.tile` links to real pages/sections.
   - The page's single **`<h1>`** lives here (the old hero title was demoted to `<h2>`).
2. **Hero** (`.hero#hero-main`) — original landing: animated atom watermark, ECG, headline,
   and a **3D coverflow package deck** (`#deck`) whose rotation includes a **festive offer**
   card (`#deckOffer`).
3. **Recommender** (`#recommender`) — "Find My Test" age/gender/concern selector.
4. **Packages** (`#packages`), **comparison** (mobile = tabbed per-package view), **process
   flow**, **Silent Killers** (flashlight reveal on desktop, canvas **scratch-card** on mobile),
   **numbers/counters**, **reviews marquee**, **Connect** bento, **Health Radar**, **FAQ**, **CTA**.
5. **Sticky callback bar** (`.cbar#cbar`, 1mg-style; added 2026-07-30) — see §8.
6. **Festive promo modal** (`#promo`) — appears ~1.6s after every load (see §9).

**Home JS entry points:** `openModal` `closeModal` `toggleMenu` `closeMenu` `toggleTheme`
`submitForm` `gotoOffer` `onModPkgChange` + IIFEs for finder, cbar, festival engine, deck,
counters, silent killers, reveal observer.

---

## 8. Sticky callback bar (`.cbar`) — 1mg-style lead capture

- Slides up from the bottom after **scroll > 780px**; dismissible (`#cbarX`); re-appears if you
  scroll back up unless dismissed.
- `#cbarForm` captures a **10-digit phone number** (validates digits), then swaps to a
  "we'll call you in 5 minutes ✓" confirmation and auto-closes.
- **Desktop/tablet only (≥820px).** On phones the existing `.mbar` (Call / Book) stays, to avoid
  stacking two bottom bars. (If mobile number-capture is wanted, swap `.mbar` for a compact
  `.cbar` variant.)

---

## 9. Festival/offer engine

Pure JS (bottom of `index.html`). Detects the **nearest upcoming festival/day** from a data
list, then:
- Fills the **promo modal** (`#promo`, name/offer/code) and shows it ~1.6s after load —
  **on every load** (no `sessionStorage` gate, by design).
- Syncs the **festive card inside the hero coverflow deck** (`#deckOffer…`).
- Runs a live **countdown**.

> To temporarily suppress the promo for clean screenshots, a common trick is to wrap the
> `setTimeout(...'promo'...)` in `if(!/nopromo/.test(location.hash))` and load `#nopromo` —
> **remember to revert** it (it's a debug-only change, never commit it).

---

## 10. Certifications system

- Page: `pages/certifications.html`. Featured **NABL / ISO 15189:2022** hero cert + a grid of
  **all 9 real certificates** (lightbox-enabled `.ccard` → `.lbx`), plus a "why it matters"
  section and `Organization`/`BreadcrumbList` JSON-LD.
- Real scans live in `assets/certs/` (downloaded from the live site `/our-certifications/`):
  - `nabl-iso15189.jpg` — **NABL** Accreditation, ISO 15189:2022, Medical Testing, **Cert MC-6991**, valid **28/11/2024–27/11/2028**
  - `iso-9001-quality.jpg` — ISO 9001:2015 (Quality; Cert 101050620, QVC UK)
  - `iso-14001-environment.jpg` · `iso-45001-safety.jpg` · `iso-27001-infosec.jpg`
    (Cert IMC-ISMS-BHC-7684) · `iso-17025-labs.jpg` (QVA-BHLC-21-243093)
    · `iso-20000-services.jpg` (QCAS-BIH-22-0515096) · `glp-practice.jpg` (QVA-BYLH-22-2811641)
    · `delhi-medical-council.jpg` (DMC doctor registration)
- A compact accreditations strip on `about-us.html` links here ("See all 9 certificates →").

---

## 11. Information architecture (menus)

Canonical menu (mega-menu + drawer + `.mmenu` + footer), applied to **every** page:

- **Checkups:** Preventive Health Checkup · Full Body Checkup · Offers & Packages · **BMI Calculator**
- **Lab Tests:** **Complete Blood Count** · Lipid Profile · Thyroid · Blood Sugar · Vitamin D · Haemoglobin · Kidney (KFT)
- **Company:** About Us · **Certifications** · Awards · Media Coverage · Social Activities · Contact Us
- **Blog** (top-level)

**IA decisions (rationale):** BMI moved Company→Checkups (it's a health tool); CBC moved
Checkups→Lab Tests (it's a lab test); Certifications added to Company (trust/credibility).

> Because the nav markup is **duplicated inline in every page** (not a shared include), a
> site-wide nav change is done by replacing the **byte-identical** nav/drawer/footer blocks in
> all interior pages (a throwaway `python` string-replace script over `pages/*.html` is the
> proven approach — the blocks were verified identical across all 23 interior pages), and then
> editing `index.html` separately (it has `pages/` prefixes + its own `.mmenu`).

---

## 12. SEO / GEO

- Per-page `<title>`, `<meta name="description">`, `theme-color`, robots, **canonical**
  (`https://biocityhealthcare.com/...`), Open Graph + Twitter cards.
- **JSON-LD**: home has `MedicalBusiness` + `FAQPage`; interior pages have `Organization` and
  **`BreadcrumbList`** (matching the visible `.bread`). GA4 placeholder `G-XXXXXXXXXX` in home
  (replace before launch).

---

## 13. Deploy workflow

```bash
# 1) Edit in the working folder
#    biocity-redesign/index.html  or  biocity-redesign/pages/*.html  or assets/*

# 2) Sync changed files into the deploy repo
cp biocity-redesign/index.html            biocity-healthcare/index.html
cp biocity-redesign/pages/*.html          biocity-healthcare/pages/
cp biocity-redesign/assets/site.css       biocity-healthcare/assets/site.css
cp biocity-redesign/assets/site.js        biocity-healthcare/assets/site.js
# (new image dirs, e.g. assets/certs/, must be copied too)

# 3) Commit & push from the deploy repo
cd biocity-healthcare
git add -A
git commit -m "…"
git push origin main            # GitHub Pages redeploys in ~1–2 min
```

**Access control for peers (recommended):** add them as a repo **Collaborator** and enable
**branch protection on `main`** (require PR + 1 approval) so nothing hits the live Pages site
without review. Never share private SSH keys/tokens — each person uses their own; for machines
use a repo **deploy key** or a fine-grained PAT.

---

## 14. Maintenance protocol (keep THIS file current)

When you make a change to the site, **in the same commit**:
1. Update the relevant section above (and the folder layout if files were added/removed).
2. Bump **Last updated** at the top.
3. Add a line to the **Changelog** (§16).
4. If you changed a **shared visual/behavior**, confirm you applied it to **both**
   `index.html` (inline) **and** `assets/site.css`/`site.js` (see §4).
5. Keep the file in **both** `biocity-redesign/` and `biocity-healthcare/docs/` in sync.

> Ask the maintainer if you'd like this automated via a Cursor **rule** (auto-remind agents to
> update the KB when touching `biocity-*/**`) or a **hook**.

---

## 15. Common recipes

- **Add an interior page:** copy `pages/about-us.html` as a template (it has the canonical
  nav/drawer/footer, breadcrumb + JSON-LD, `../assets/site.*` links). Update `<title>`,
  meta, canonical, breadcrumb, JSON-LD, and content. Add it to the mega-menu/drawer/footer
  across all pages + `index.html` if it should be discoverable.
- **Add a lab-test page:** clone an existing `test-*.html`; update name, price, params,
  breadcrumb, JSON-LD; add to Lab Tests mega + drawer + footer.
- **Change prices/wording site-wide:** they're inline per page — grep for the value across
  `pages/*.html` + `index.html`.
- **Add a certificate:** drop the scan in `assets/certs/`, add a `.ccard` to
  `certifications.html`; if flagship, also update the about-us strip.
- **Change the nav everywhere:** see §11 (byte-identical block replacement + separate home edit).

---

## 16. Changelog

- **2026-07-30** — **Highlighted landing atom** (`.phero-atom`) added to the first section of
  every page (home finder, all interior pages via `site.js`, and the 4 self-contained pages via
  inline edits). Home Lab Finder: **removed the graph-paper grid** from the first section (solid
  `--bg`), and made the background photos **static + lab-only** (removed float/parallax).
- **2026-07-30** — Home **Lab Finder console** (live search + category tabs/tiles), foreground
  **highlight photo rail**, **aligned** symmetric background photos (replacing scattered drift),
  and **1mg-style sticky callback bar** (`.cbar`, desktop/tablet). Old hero heading demoted to
  `h2` so the finder is the single `h1`.
- **2026-07-30** — **Certifications page** with 9 real certificate scans + lightbox; **menu IA
  rationalized** (Certifications→Company, BMI→Checkups, CBC→Lab Tests) across all pages.
- **(earlier)** — Interior page expansion (about-us, checkups, 7 lab tests, awards/media/social,
  offers/contact/BMI, legal), shared `assets/site.css`/`site.js`, mega-menu + drawer,
  breadcrumbs + JSON-LD, 3D coverflow deck + festive panel, animated atom logo, graph-paper
  background, Silent Killers reveal/scratch, full mobile-performance pass. Deployed to GitHub
  Pages (`nikhilGupta24/biocity-healthcare`).

---

## 17. Caveats & gotchas (read before editing)

1. **Two CSS/JS homes** — shared visuals often must change in **both** `index.html` (inline)
   and `assets/site.css`/`site.js`. Easy to forget → home vs interior drift. (§4)
2. **Headless min-width 500px** — narrow screenshots show **false clipping**; test at 500px. (§3)
3. **Nav is duplicated per page** (no include) — site-wide nav edits need the block-replace
   approach; the 4 retrofitted pages have a different footer. (§4, §11)
4. **Promo shows on every load** by design (no session gate). The `#nopromo` hash trick is
   debug-only — never commit it. (§9)
5. **`.cbar` is desktop/tablet only** (≥820px); mobile keeps `.mbar`. (§8)
6. **We do NOT use 1mg's images/tiles** — those are Tata 1mg proprietary assets (copyright/
   trademark risk). The Lab Finder uses **Biocity's own** photos. Keep it that way.
7. **Coverflow front-card click opens the booking modal** (`initDeck`). If you build an
   image-only deck, don't also make cards `.lbx` or you'll get two overlapping actions — that's
   why `certifications.html` uses a lightbox **grid**, not the coverflow deck.
8. **Canonical/OG point to `biocityhealthcare.com`**, but no `CNAME` is committed — set the
   custom domain in the Pages UI (or the canonical won't match the live github.io URL).
9. **GA4 is a placeholder** (`G-XXXXXXXXXX`) — replace before launch.
10. **`docs/BIOCITY_PLAYBOOK.md` + `docs/KNOWLEDGE_BANK.html` + `README.md` are stale** for the
    current site; trust **this file** for site specifics.
11. **The landing atom (`.phero-atom`) lives in 4 places** — `index.html` (inline),
    `assets/site.css` + `assets/site.js` (interior pages), and the **4 self-contained pages'
    inline `<style>`** (`city-noida`, `condition-diabetes`, `blog`, `blog-vitamin-d-deficiency`),
    because those pages do **not** load the shared assets. Change all 4 if you restyle it.
