# Biocity Healthcare — Website

A fast, fully self-contained marketing website for Biocity Healthcare (NABL-accredited diagnostics, home sample collection, full-body health checkups).

Every page is a single HTML file with **all CSS and JavaScript inlined** — no build step, no dependencies, no external asset files. Open any file directly in a browser and it just works (light/dark mode, animations, mobile-responsive, print-friendly).

## Structure

```
.
├── index.html                         # Home page
├── pages/
│   ├── city-noida.html                # City landing page (template)
│   ├── condition-diabetes.html        # Condition/ailment landing page (template)
│   ├── blog.html                      # Blog hub + Trusted Resources (genuine external links)
│   └── blog-vitamin-d-deficiency.html # Sample blog article
├── docs/                              # Internal planning docs (not part of the live site)
│   ├── BIOCITY_PLAYBOOK.md
│   ├── KNOWLEDGE_BANK.html
│   └── PHASE1A_PLAN.html
├── .nojekyll                          # Tell GitHub Pages to serve files as-is (no Jekyll)
└── README.md
```

All links are relative, so the site is portable — the whole folder can be moved or served from any static host.

## Run locally

Just open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploy to GitHub Pages

1. Create a new GitHub repository (e.g. `biocity-healthcare`) and push this folder to it:
   ```bash
   git init
   git add .
   git commit -m "Biocity Healthcare website"
   git branch -M main
   git remote add origin git@github.com:<your-username>/biocity-healthcare.git
   git push -u origin main
   ```
2. In the repo: **Settings → Pages → Build and deployment**.
3. Set **Source: Deploy from a branch**, **Branch: `main`**, **Folder: `/ (root)`**, then **Save**.
4. After a minute the site is live at:
   `https://<your-username>.github.io/biocity-healthcare/`

The included `.nojekyll` file ensures GitHub serves the HTML exactly as written.
