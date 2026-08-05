# Biocity v3 — local demo pack

One command hosts the site, opens Chrome, and streams live telemetry. Fully
offline, no dependencies (stock Python 3.9+, standard library only).

## Run it

```bash
cd biocity-healthcare
python3 engine.py
```

`engine.py`:

1. Streams a theatrical diagnostic pipeline (hardware probe, module link, data
   ingest, spectrometer calibration, a live model-training dashboard with a loss
   sparkline + per-GPU meters, federated aggregation, genomic variant calling,
   cryptographic report anchoring) — truecolour, progress bars, rolling logs.
2. **Hosts this repo** on a real local web server.
3. **Opens Google Chrome** at `http://localhost:<port>/v3/`.
4. Switches the terminal to a **live mission-control dashboard of real server
   traffic** — every request Chrome makes (method, status, path, bytes, latency,
   client) plus rolling vitals: req/s + sparkline, p50/p95 latency, bytes served,
   2xx/3xx/4xx/5xx, unique clients, cpu/mem.

Click around the site in Chrome and watch the requests appear in the terminal.

### Flags

```bash
python3 engine.py --fast      # brisk pipeline, then host
python3 engine.py --turbo     # near-instant pipeline (rehearsal), then host
python3 engine.py --port 9000 # pick the port (default 8090, auto-bumps if busy)
python3 engine.py --no-open   # host + telemetry, don't auto-launch the browser
python3 engine.py --no-serve  # pipeline only, no hosting
python3 engine.py --no-clear  # keep scrollback
python3 engine.py --mono      # colour off
```

`Ctrl-C` stops the server and exits cleanly (prints total requests served).

`serve.sh` is a bare-bones fallback host (`./serve.sh [port]`) if you only want
the site without the engine.

**Demo tip:** full-screen, dark terminal, large font, in a truecolour terminal
(iTerm2 / VS Code / Ghostty). Terminal.app auto-falls-back to 256 colours.

> ⚠️ The *pipeline* numbers (training, genomics, …) are synthetic — for visual
> effect only, not for clinical use. The **stage 09 traffic telemetry is real** —
> it is the genuine access log of the local server.
