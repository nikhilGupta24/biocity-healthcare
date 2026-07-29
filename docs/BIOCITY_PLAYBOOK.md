# Biocity Project — Agent Playbook

> **Purpose:** Make any AI agent self-sufficient at reproducing the Biocity engagement —
> a modern website, a demo CRM, and a board-ready interactive pitch — plus the methodology,
> design system, and patterns behind them. This is the agent-optimized companion to
> `KNOWLEDGE_BANK.html` (which is the human-facing version).

---

## 0. How an agent should use this file

1. Read this whole file first — it is the source of truth for *method* and *patterns*.
2. Study the **reference implementations** (real code to copy patterns from):
   - `biocity-redesign/index.html` — redesigned website (single file, ~840 lines)
   - `biocity-redesign/PHASE1A_PLAN.html` — interactive pitch deck (single file, ~1,600 lines)
   - `biocity-crm/index.html` + `styles.css` + `app.js` — demo CRM ("Biocity Pulse")
3. Follow the **Replication Checklist** (§13) to produce new artifacts.
4. Always honor the **Quality Bar** (§13) and the **Golden Rule** (§2).

A copy-paste **kickoff prompt** for the human to give their agent is in §15.

---

## 1. Engagement at a glance

**Client:** Biocity Healthcare — NABL-accredited diagnostics; business runs largely over phone calls.
**Brief:** Make the brand look as credible online as it is offline; give the team modern tooling;
don't over-engineer before there is stakeholder buy-in.

**What was delivered:**
- A complete website redesign (public site).
- "Biocity Pulse" — a working demo CRM for a call-driven business.
- An interactive Phase 1A plan that pitches the website revamp to a non-technical CEO.

**Activity timeline:** Audit → Redesign → Build demo CRM → Map stack/hosting/phases/costing →
Create interactive pitch → Iterate on feedback.

---

## 2. The deliverables (and the Golden Rule)

| Artifact | File(s) | Notes |
|---|---|---|
| Website | `biocity-redesign/index.html` | Single file, CSS+JS inline, dark mode, mobile-first |
| CRM "Biocity Pulse" | `biocity-crm/index.html`, `styles.css`, `app.js` | localStorage DB, Chart.js, Kanban |
| Phase 1A Plan | `biocity-redesign/PHASE1A_PLAN.html` | CEO-facing, interactive demos, printable |
| Knowledge bank (human) | `biocity-redesign/KNOWLEDGE_BANK.html` | Styled HTML doc |
| Playbook (agent) | `biocity-redesign/BIOCITY_PLAYBOOK.md` | This file |

**GOLDEN RULE:** Every client-facing artifact is a **single, dependency-free file** (or a tiny folder).
It must open by double-click, work offline, and print to PDF. No build step, no server, no installs.

---

## 3. Methodology — the repeatable five-act method

1. **Audit & empathise.** Use the current product as a real user; list concrete problems
   (clutter, slow, hard to find, no trust). Frame every later change as a fix to one of these.
2. **Prototype the destination, not a deck.** Build a real, clickable artifact early.
3. **Design a system, then apply it.** Define tokens (color, type, spacing, radius, shadow) once
   as CSS variables; everything reads from them (gives consistency + dark mode for free).
4. **Translate for the audience.** Engineers think features; CEOs think outcomes, effort, time.
   Re-label everything; tag by *business goal* and *effort*.
5. **Package the pitch.** Wrap in a narrative: problem → see the fix → the plan → the timeline →
   what we need → why it pays off. Interactive to explore, printable to forward.

**Principle:** *Show, don't tell.* A slider, a device toggle, or a one-tap demo beats a paragraph.

---

## 4. Design system & techniques (copy these)

### 4.1 Token-driven theming + free dark mode
```css
:root{ --bg:#F5F7F8; --ink:#0E1B1A; --accent:#0E9E8C; }
[data-theme="dark"]{ --bg:#0A1110; --ink:#EAF2F0; --accent:#2DD4BF; }
.card{ background:var(--bg); color:var(--ink); }
```
Flip `data-theme` to re-theme the whole page; persist the choice in `localStorage`.

### 4.2 The "siteskin" scoping trick
When embedding a preview of one brand inside a doc with a different brand, wrap the preview in a
class that re-declares tokens locally so it keeps its own identity:
```css
.siteskin{ --accent:#E05A3A; --panel:#FFF; font-family:'Plus Jakarta Sans'; }
```

### 4.3 Typography
One display + one body face. Used: **Fraunces** (website display), **Space Grotesk** (docs headings),
**Inter / Plus Jakarta Sans** (body), **JetBrains Mono** (code).

### 4.4 Micro-interactions
- **Reveal on scroll:** `IntersectionObserver` adds a `.v` class that fades/slides elements in.
- **Scroll-progress bar:** width = `scrollTop / scrollHeight`.
- **Animated counters:** count up on enter-view.
- **Infinite marquee:** duplicate the row, translate linearly for a seamless loop.
- **Hover lift:** `transform: translateY(-4px)` + larger shadow.

### 4.5 "Show, don't tell" widgets
- **Before/After slider:** two stacked layers + draggable handle clipping width.
- **Device toggle:** one mockup, two CSS widths (desktop ↔ phone) reflowed via a `.mobile` class — no second file.
- **Element demo modal:** each "change" card opens a realistic animated mini-preview.
- **Animated concept tiles:** tiny CSS animations that visualize abstract ideas (e.g. an AI answer citing the brand).

### 4.6 The single-file constraint
Inline all CSS/JS. **Avoid `<iframe src="other.html">`** in anything shared as one file — build a
self-contained mockup instead. After building, grep for external `src`/iframe references and confirm zero remain.
> Hard-won lesson: a live-preview iframe required a second file; we replaced it with an inline mockup.

---

## 5. Website redesign — principles

Philosophy: replace noise with clarity; make every screen push toward a booking.

| Before | After |
|---|---|
| Banners/popups competing | Calm, spacious layout, one action per screen |
| Hard on mobile | Mobile-first, thumb-sized targets |
| Prices/tests buried | Comparable package cards + "most popular" |
| Trust hidden | Trust section front & center + proof stats |
| Invisible on Google/AI | SEO + GEO foundations (§9) |

**Sections used:** sticky nav (theme toggle + mobile menu), hero (floating trust cards + scroll progress),
animated numbers, "How it works", package cards, "Why us"/trust, health-awareness, infinite reviews marquee, BMI calculator.

**Takeaway:** For healthcare/services, **trust + ease-of-contact** beat clever visuals. Everything funnels to call / WhatsApp / book.

---

## 6. CRM "Biocity Pulse" — patterns

Organized around a call-driven business: **capture lead → log call → book visit → track report.**

**Modules:** Dashboard (KPIs + charts), Leads (drag-drop Kanban), Calls, Bookings, Phlebotomists,
Reports, Customers (with LTV), Analytics (revenue by city, channel mix, growth), Packages.

**Demo pattern that makes it shine:**
- `seed()` generates realistic data; `load()`/`save()` persist to `localStorage` (survives refresh).
- A **Reset** button restores the seed before a live pitch.
- **Chart.js** for revenue/funnel/growth visuals reading the same data.
- Reuses the token + dark-mode design system.

**Why no backend yet:** a browser-storage demo proves the workflow and wins buy-in *before* spending on
servers/auth/DB. Build the real backend after approval (§8, §10).

---

## 7. The Phase 1A pitch — narrative arc

Most refined artifact because it gets presented. Job: make a non-technical leader feel the value in minutes.

**Arc (9 sections):** How to read → See it in action (live desktop/mobile mockup) → At a glance (3 goals) →
The next frontier (GEO) → Content that captures demand → The full checklist (24 changes, each w/ live demo) →
The roadmap (3–4 weeks) → What we need from you → Why it matters.

**Translation techniques:**
- **Effort, not cost:** tag items 🟢 Low / 🟡 Medium / 🔴 High; keep price out of the room.
- **Goal filters:** slice changes by business outcome (Look & Feel / Win the Booking / Get Found).
- **Plain-English pairs:** every card = one-line "Now" vs "After".
- **Independent aesthetic:** the deck has its own indigo/Space-Grotesk identity so it reads as strategy, not the website.

---

## 8. Tech stack & hosting (for production)

| Layer | Recommended | Alternatives |
|---|---|---|
| Website front | Next.js or Astro (React) | Plain HTML for brochure |
| CRM front | React + component lib | Vue / Svelte |
| Backend/API | Node.js (NestJS) or Python (FastAPI) | Django |
| Database | PostgreSQL | MySQL |
| Cache/queues | Redis | — |
| File storage | AWS S3 / GCP Storage / Cloudflare R2 | — |
| Payments | Razorpay | Stripe / PayU |
| Messaging | WhatsApp Business API, MSG91/Twilio (SMS), SendGrid/SES (email) | — |
| Call tracking | Exotel / Knowlarity | — |

**Hosting answer:** website on a **static host** (Vercel/Netlify/Cloudflare Pages — cheap, fast, secure);
CRM/API on **managed cloud** (AWS/GCP/DigitalOcean). In-house only if compliance truly requires it.

---

## 9. SEO & GEO playbook

**SEO** = rank on Google. **GEO (Generative Engine Optimization)** = be *cited* by ChatGPT/Gemini/Perplexity/AI Overviews.
Most competitors aren't doing GEO yet — it's an ownable edge.

**What helps get cited by AI:** clear factual content; direct question→answer format; structured headings + clean HTML;
schema markup (JSON-LD: business type, rating, prices, area served); authoritative/expert-reviewed content; brand mentions across trusted sites.

> Practise what you preach: the plan ships `MedicalBusiness` + `FAQPage` JSON-LD in its `<head>`.

**Content strategy that scales — targeted landing pages on 3 axes + a blog:**

| Axis | Example | Captures |
|---|---|---|
| 🏙️ City | "Full Body Checkup in Noida" | local / "near me" |
| 🩺 Ailment | "Diabetes Screening" | symptom/condition searches |
| 👨‍👩‍👧 Age/life-stage | "Health Checkup for Women 40+" | demographic searches |
| 📰 Blog hub | "Signs of Vitamin D deficiency" | informational + AI citations |

Combined ≈ **60+ cities × 14+ conditions × 4+ life-stages = ~3,000+ targeted pages.**

---

## 10. Phasing, timeline & costing

**Phases:** 1A = website revamp + SEO/GEO foundations · 1B = targeted pages at scale + blog ·
2 = CRM productionised (auth, DB) · 3 = integrations (payments, WhatsApp, SMS, call tracking, storage).

**Phase 1A timeline (~3–4 weeks):** W1 Design & sign-off · W2 Build pages · W3 Content/SEO/GEO · W4 Review & go live.

**Talking budget (humble):** lead with value not price; anchor to outcomes & phases (quote per milestone);
ask the range ("what budget are we working within for 1A so I can shape scope?"); offer a small, clear first step.
*Keep specific figures out of shared docs — quote on your team's rates + agreed scope.*

---

## 11. What to collect from the client

- **Brand & visuals:** logo (vector ideally), colors/fonts, real photos (lab/team/home visits), videos.
- **Reference & inspiration:** 2–3 sites they like, competitor sites, specific likes/dislikes.
- **Content & proof:** package details & prices, certifications/awards, real reviews, contact details.
- **Access:** **source code repository**, domain & DNS, Google Business Profile & analytics, social handles.
- **Lists for targeted pages:** priority cities; ailments/conditions; age & life stages; any other category
  (corporate/B2B, seasonal, by gender).

> If they can't supply everything, start with what they have and fill gaps as you go — momentum beats a perfect kickoff.

---

## 12. Prompts & communication patterns

**Prompting an AI partner:** set a persona + a bar ("best UI/UX designer; make it a banger");
give constraints not just goals (single file, dark mode, mobile, don't mention cost); name the audience
(non-technical CEO; Gen-Z + older); iterate in small concrete edits; ask for options when trade-offs exist.

**Talking to non-technical stakeholders:** translate every feature into an outcome; use effort tiers (🟢🟡🔴) not jargon;
show a working thing; keep it less verbose (one-line Now/After); end with a small, obvious ask.

---

## 13. Replication checklist

1. Audit the current product; list concrete user problems (+ screenshots).
2. Define the design system: palette + 1 display + 1 body font; tokens as CSS variables w/ dark-mode override.
3. Prototype the new front-end as one self-contained HTML file (reveal-on-scroll, counters, conversion sections).
4. Build a demo of any tooling (CRM/dashboard) on `localStorage` + Chart.js; add a "reset demo" button.
5. Research the production stack (front/back/DB/integrations/hosting); write the phase plan + timeline.
6. Write the SEO/GEO strategy (schema, Q&A content, city × ailment × age matrix).
7. Build the pitch as an interactive HTML file: narrative arc, plain-English change cards tagged by goal + effort,
   live element demos, a roadmap, a client ask-list.
8. Scope the deck's aesthetic independently from the product (own colors/fonts).
9. Enforce the single-file rule: inline CSS/JS, mock anything needing a second file, grep for external refs.
10. Iterate with the stakeholder in small, specific edits until subtle, clear, convincing.
11. Ship a knowledge bank (human HTML) + this playbook (agent MD) so the team inherits the know-how.

**QUALITY BAR:** opens by double-click · works offline · great in light *and* dark · responsive on a phone ·
printable to PDF · zero external dependencies.

---

## 14. Glossary

- **SEO** — ranking in Google results.
- **GEO** — Generative Engine Optimization: being cited/recommended by AI assistants.
- **Schema / JSON-LD** — structured data stating explicit business facts to engines.
- **Design token** — a named variable (color, spacing) the whole UI references.
- **Siteskin** — scoping class that re-themes an embedded preview to its own brand.
- **LTV** — Lifetime Value: total revenue from a customer over time.

---

## 15. Kickoff prompt (paste this to the agent)

```
You are a senior UI/UX designer + full-stack engineer. Read BIOCITY_PLAYBOOK.md in full,
then study the reference files it lists (biocity-redesign/index.html,
biocity-redesign/PHASE1A_PLAN.html, and biocity-crm/*). These define my method, design system,
and quality bar.

Now apply the SAME methodology, design system, and patterns to: <DESCRIBE THE NEW CLIENT/PRODUCT>.

Rules:
- Follow the five-act method (§3) and the Replication Checklist (§13).
- Honor the Golden Rule (§2): every client-facing artifact is a single, dependency-free file
  that opens by double-click, works offline, supports light/dark, is mobile-responsive, and prints to PDF.
- Translate features into outcomes for a non-technical stakeholder; tag changes by goal + effort.
- Use "show, don't tell" interactive demos. Keep copy subtle and concise.
- Before finishing, verify the Quality Bar (§13) and grep for any external src/iframe references.

Start by proposing a plan, then build.
```
