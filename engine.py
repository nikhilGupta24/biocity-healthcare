#!/usr/bin/env python3
# ruff: noqa: RUF001, UP017, B905  (Unicode is intentional; keep py3.9-portable: no datetime.UTC / no zip(strict=))
"""
BIOCITY // DIAGNOSTIC INTELLIGENCE ENGINE  (v3.0.0)
=====================================================
A theatrical, self-contained command-line "boot + pipeline" visualiser built
for the Biocity Healthcare v3 client demo.

It streams a large volume of dense, scientific-looking telemetry — hardware
probing, module linking, data ingestion, spectrometer calibration, a live
deep-model training dashboard, federated aggregation across 60+ cities,
genomic variant calling and cryptographic report anchoring — all rendered with
truecolour gradients, rounded panels, sparklines and live-updating meters.

None of the numbers are load-bearing; they are generated for effect. The point
is that it *feels* like a very expensive, very technical, hard-won platform.

Pure Python standard library. No dependencies. No network.

    python3 engine.py                # full show, then HOST the v3 site + open Chrome + live telemetry
    python3 engine.py --fast         # brisk pipeline (~28s) then host
    python3 engine.py --turbo        # near-instant pipeline (rehearsal) then host
    python3 engine.py --port 9000    # choose the local port (default 8090, auto-bumps if busy)
    python3 engine.py --no-open      # host + telemetry but don't auto-launch the browser
    python3 engine.py --no-serve     # pipeline only, no hosting (CI / dry-run)
    python3 engine.py --no-clear     # keep scrollback
    python3 engine.py --mono         # disable colour

After the pipeline it starts a real local web server for the mirrored Biocity
v3 site, opens Google Chrome at http://localhost:<port>/v3/, and then streams a
LIVE mission-control dashboard: real HTTP access-log events plus rolling vitals
(req/s, p50/p95 latency, bytes served, status classes, clients, cpu/mem).

Ctrl-C stops the server and exits cleanly.
"""

import contextlib
import hashlib
import math
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ─────────────────────────────────────────────────────────────────────────────
#  Config / terminal
# ─────────────────────────────────────────────────────────────────────────────
ARGS = set(a for a in sys.argv[1:] if not a.startswith("--port"))
SPEED = 0.04 if "--turbo" in ARGS else (0.35 if "--fast" in ARGS else 1.0)
NO_CLEAR = "--no-clear" in ARGS
NO_SERVE = "--no-serve" in ARGS
NO_OPEN = "--no-open" in ARGS


def _arg_port(default=8090):
    for a in sys.argv[1:]:
        if a.startswith("--port="):
            try:
                return int(a.split("=", 1)[1])
            except ValueError:
                return default
    argv = sys.argv[1:]
    if "--port" in argv:
        i = argv.index("--port")
        if i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                return default
    return default


PORT = _arg_port()
ROOT = os.path.dirname(os.path.abspath(__file__))

_size = shutil.get_terminal_size((100, 30))
COLS = max(74, min(_size.columns, 104))

_env = os.environ
USE_COLOR = sys.stdout.isatty() and _env.get("NO_COLOR") is None and "--mono" not in ARGS
TRUECOLOR = any(x in (_env.get("COLORTERM", "").lower()) for x in ("truecolor", "24bit"))

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def nap(a, b=None):
    time.sleep(max(0.0, (a if b is None else random.uniform(a, b)) * SPEED))


def w(s=""):
    sys.stdout.write(s)


def flush():
    sys.stdout.flush()


def out(s="", end="\n"):
    sys.stdout.write(s + end)
    sys.stdout.flush()


# ─────────────────────────────────────────────────────────────────────────────
#  Colour engine (truecolour with graceful 256-colour fallback)
# ─────────────────────────────────────────────────────────────────────────────
RESET = "\033[0m" if USE_COLOR else ""


def _nearest256(r, g, b):
    def cube(v):
        return 0 if v < 48 else (1 if v < 115 else (v - 35) // 40)

    ri, gi, bi = cube(r), cube(g), cube(b)
    return 16 + 36 * ri + 6 * gi + bi


def fg(rgb):
    if not USE_COLOR:
        return ""
    r, g, b = rgb
    if TRUECOLOR:
        return f"\033[38;2;{r};{g};{b}m"
    return f"\033[38;5;{_nearest256(r, g, b)}m"


def C(s, rgb, bold=False):
    if not USE_COLOR:
        return str(s)
    b = "\033[1m" if bold else ""
    return f"{b}{fg(rgb)}{s}{RESET}"


def lerp(c1, c2, t):
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def gradient(s, c1, c2, bold=False, tilt=0.0, row=0):
    if not USE_COLOR:
        return str(s)
    n = max(len(s) - 1, 1)
    b = "\033[1m" if bold else ""
    parts = []
    for i, ch in enumerate(s):
        t = i / n
        if tilt:
            t = min(1.0, t * (1 - tilt) + row * tilt)
        parts.append(fg(lerp(c1, c2, t)) + ch)
    return b + "".join(parts) + RESET


def vlen(s):
    return len(ANSI_RE.sub("", s))


def clip(s, n):
    """Truncate to n *visible* chars, preserving ANSI escapes. Prevents wrap."""
    if vlen(s) <= n:
        return s
    buf, count, i = [], 0, 0
    while i < len(s) and count < n:
        m = ANSI_RE.match(s, i)
        if m:
            buf.append(m.group())
            i = m.end()
            continue
        buf.append(s[i])
        i += 1
        count += 1
    return "".join(buf) + (RESET if USE_COLOR else "")


# ─────────────────────────────────────────────────────────────────────────────
#  Palette
# ─────────────────────────────────────────────────────────────────────────────
GREEN = (16, 185, 129)
GREEN_HI = (52, 211, 153)
MINT = (110, 231, 183)
CYAN = (14, 165, 233)
SKY = (56, 189, 248)
INK = (226, 232, 240)
MUTE = (148, 163, 184)
DIM = (94, 110, 130)
FAINT = (64, 78, 96)
WARN = (251, 191, 36)
GOLD = (250, 204, 21)
BAD = (248, 113, 113)
VIOLET = (167, 139, 250)


# ─────────────────────────────────────────────────────────────────────────────
#  Primitives
# ─────────────────────────────────────────────────────────────────────────────
SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
SPARK = "▁▂▃▄▅▆▇█"


def ts():
    return C(datetime.now(timezone.utc).strftime("%H:%M:%S.") + f"{random.randint(0, 999):03d}Z", FAINT)


def rand_hex(n=64):
    return hashlib.sha256(os.urandom(16) + str(time.time_ns()).encode()).hexdigest()[:n]


def hrule(color1=GREEN, color2=CYAN, ch="─"):
    out(gradient(ch * COLS, color1, color2))


def section(num, name, tag=""):
    out()
    if USE_COLOR and TRUECOLOR:
        badge = f"\033[48;2;16;185;129m\033[38;2;6;20;14m\033[1m {num:02d} {RESET}"
    else:
        badge = C(f"[{num:02d}]", GREEN, bold=True)
    title = C(name.upper(), INK, bold=True)
    tagp = "  " + C(tag, MUTE) if tag else ""
    out(f"{badge} {title}{tagp}")
    out(gradient("─" * COLS, GREEN, CYAN))


ICON = {
    "OK": ("✔", GREEN_HI),
    "INFO": ("•", CYAN),
    "WARN": ("▲", WARN),
    "PERF": ("⚡", VIOLET),
    "NET": ("◇", SKY),
    "GPU": ("▨", GOLD),
    "BIO": ("❖", MINT),
    "SEC": ("⛨", SKY),
    "MATH": ("∑", VIOLET),
    "DATA": ("⛁", CYAN),
}


def log(level, msg, tag=None):
    icon, col = ICON.get(level, ("·", MUTE))
    lv = C(f"{level:<4}", col, bold=True)
    ic = C(icon, col)
    tagp = " " + C(f"[{tag}]", FAINT) if tag else ""
    out(f"{ts()} {ic} {lv}{tagp}  {msg}")
    nap(0.015, 0.05)


def typel(prefix, text, color=INK, cps=90):
    w(prefix)
    flush()
    if SPEED <= 0.1 or not USE_COLOR:
        out(C(text, color))
        return
    for ch in text:
        w(C(ch, color))
        flush()
        time.sleep((1.0 / cps) * SPEED)
    out()


def minibar(frac, width, c1, c2, empty="·"):
    frac = 0.0 if frac < 0 else (1.0 if frac > 1 else frac)
    filled = round(frac * width)
    cells = []
    for i in range(width):
        if i < filled:
            cells.append(C("█", lerp(c1, c2, i / max(width - 1, 1))))
        else:
            cells.append(C(empty, FAINT))
    return "".join(cells)


def spark(vals, c1=GREEN_HI, c2=CYAN):
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    n = max(len(vals) - 1, 1)
    o = []
    for i, v in enumerate(vals):
        idx = int((v - lo) / rng * (len(SPARK) - 1))
        o.append(C(SPARK[idx], lerp(c1, c2, i / n)))
    return "".join(o)


def spinner(label, duration, ok="ready", tag=None):
    frames = min(60, max(8, int(duration / 0.075 / (SPEED or 1))))
    start = time.time()
    for i in range(frames):
        w(f"\r  {C(SPIN[i % len(SPIN)], CYAN)} {C(label, INK)}\033[K")
        flush()
        nap(duration / frames)
    el = time.time() - start
    tagp = " " + C(f"[{tag}]", FAINT) if tag else ""
    out(f"\r  {C('✔', GREEN_HI)} {C(label, MUTE)}{tagp}  {C('· ' + ok, GREEN_HI)} {C(f'({el:04.2f}s)', FAINT)}\033[K")


def progress(label, total, unit="rec", rate=(180, 900), width=34, c1=GREEN, c2=CYAN):
    done, tick, start = 0, 0, time.time()
    while done < total:
        done = min(total, done + random.randint(int(total * 0.018), int(total * 0.085) + 1))
        frac = done / total
        r = random.uniform(*rate) * (1 + 0.12 * math.sin(tick))
        eta = (total - done) / max(r, 1)
        w(
            f"\r  {C(label, INK)} {minibar(frac, width, c1, c2)} "
            f"{C(f'{frac * 100:5.1f}%', INK, bold=True)} "
            f"{C(f'{done:>9,}/{total:,} {unit}', MUTE)} "
            f"{C(f'{r:6.0f} {unit}/s', VIOLET)} {C(f'eta {eta:04.1f}s', FAINT)}\033[K"
        )
        flush()
        tick += 1
        nap(0.03, 0.08)
    el = time.time() - start
    out(
        f"\r  {C(label, MUTE)} {minibar(1, width, c1, c2)} "
        f"{C('100.0%', GREEN_HI, bold=True)} {C(f'{total:,} {unit}', MUTE)} "
        f"{C('✔', GREEN_HI)} {C(f'{el:04.2f}s · {total / max(el, 0.01):,.0f} {unit}/s', FAINT)}\033[K"
    )


def panel_lines(rows, title="", color=GREEN, width=None):
    width = width or COLS
    inner = width - 2
    tl, tr, bl, br, h, v = "╭", "╮", "╰", "╯", "─", "│"
    if title:
        t = f" {title} "
        fill = inner - 1 - vlen(t)
        top = C(tl + h, color) + C(t, INK, bold=True) + C(h * max(0, fill) + tr, color)
    else:
        top = C(tl + h * inner + tr, color)
    lines = [top]
    for r in rows:
        pad = inner - 2 - vlen(r)
        lines.append(C(v, color) + " " + r + " " * max(0, pad) + " " + C(v, color))
    lines.append(C(bl + h * inner + br, color))
    return lines


def panel(rows, title="", color=GREEN, width=None):
    for ln in panel_lines(rows, title, color, width):
        out(ln)


class Live:
    """A block of N lines redrawn in place."""

    def __init__(self, n):
        self.n = n
        self.first = True

    def render(self, lines):
        buf = "" if self.first else f"\033[{self.n}A"
        for ln in lines:
            buf += "\r" + clip(ln, COLS) + "\033[K\n"
        self.first = False
        w(buf)
        flush()


# ─────────────────────────────────────────────────────────────────────────────
#  Domain flavour
# ─────────────────────────────────────────────────────────────────────────────
CITIES = [
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Chennai",
    "Kolkata",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
    "Noida",
    "Gurugram",
    "Chandigarh",
    "Kochi",
    "Indore",
    "Nagpur",
    "Surat",
    "Bhopal",
    "Patna",
    "Coimbatore",
]
MODULES = [
    ("libhemo-core", "3.11.2", "SIMD/AVX-512"),
    ("spectra-rt", "2.7.0", "FPGA-offload"),
    ("torch-inference", "2.4.1+cu124", "CUDA graphs"),
    ("cudnn", "9.3.0", "fp8 kernels"),
    ("nccl", "2.22.3", "ring-allreduce"),
    ("biocity-nabl-calib", "6991.4", "ISO-15189"),
    ("genome-align", "1.9.14", "BWA-MEM2"),
    ("variant-caller", "4.5.0", "GATK-compat"),
    ("secure-agg", "0.8.1", "he-CKKS"),
    ("report-anchor", "2.1.0", "ed25519+PQC"),
]
ASSAYS = ["CBC-24", "Lipid-9", "LFT-12", "KFT-8", "Thyroid-T3T4TSH", "HbA1c", "Vitamin-D-25OH", "Ferritin"]
GENES = ["MTHFR", "TP53", "BRCA1", "HBB", "G6PD", "APOE", "TCF7L2", "FTO", "VDR", "TSHR"]

# ANSI-Shadow wordmark, assembled per-letter for perfect alignment.
GLYPHS = {
    "B": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██████╔╝", "╚═════╝ "],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
    "T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    "Y": ["██╗   ██╗", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚██╔╝  ", "   ██║   ", "   ╚═╝   "],
}


def wordmark(text="BIOCITY"):
    rows = ["", "", "", "", "", ""]
    for ch in text:
        g = GLYPHS.get(ch)
        if not g:
            continue
        for i in range(6):
            rows[i] += g[i] + " "
    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  Stages
# ─────────────────────────────────────────────────────────────────────────────
def stage_banner():
    if not NO_CLEAR:
        w("\033[2J\033[H")
    rows = wordmark("BIOCITY")
    wm_w = max(len(r) for r in rows)
    out()
    if wm_w <= COLS:
        pad = " " * ((COLS - wm_w) // 2)
        for i, r in enumerate(rows):
            out(pad + gradient(r, GREEN_HI, CYAN, bold=True, tilt=0.10, row=i / 5))
    else:
        out(gradient("  B I O C I T Y", GREEN_HI, CYAN, bold=True))
    sub = "D I A G N O S T I C   I N T E L L I G E N C E   E N G I N E"
    out()
    out(_center(gradient(sub, MINT, SKY, bold=True)))
    meta = f"v3.0.0  ·  build 20260806.a1f9c3  ·  session {rand_hex(8)}  ·  region ap-south-1"
    out(_center(C(meta, MUTE)))
    out()
    hrule()
    typel("  ", "initialising secure enclave", MUTE, cps=140)
    nap(0.25)


def _center(s):
    pad = max(0, (COLS - vlen(s)) // 2)
    return " " * pad + s


def stage_hardware():
    section(1, "Hardware & Runtime Fabric", "topology via hwloc-2.11")
    spinner("enumerating NUMA domains, PCIe lanes and NVLink mesh", 1.1, ok="1 node · 4 accelerators")
    rows = [
        f"{C('CPU', SKY, bold=True)}   {C('AMD EPYC 9654', INK)}  {C('96C / 192T', MUTE)}   base 2.40GHz  boost {C('3.70GHz', GREEN_HI)}   L3 {C('384 MB', GREEN_HI)}",
        f"{C('RAM', SKY, bold=True)}   {C('1.5 TiB', INK)} DDR5-4800 ECC   12-channel   bandwidth {C('460.8 GB/s', GREEN_HI)}",
        f"{C('NIC', SKY, bold=True)}   {C('InfiniBand NDR', INK)} 400 Gb/s   ·   {C('NVLink 4.0', INK)} 900 GB/s   ·   RDMA {C('on', GREEN_HI)}",
    ]
    for i in range(4):
        bar = minibar(random.uniform(0.0, 0.05), 10, GREEN, GREEN_HI)
        rows.append(
            f"{C(f'GPU{i}', GOLD, bold=True)}  {C('NVIDIA H100 SXM5', INK)}  80GB HBM3  {C('3.35 TB/s', MUTE)}  ecc {C('on', GREEN_HI)}  util {bar} {C('idle', FAINT)}"
        )
    panel(rows, title="compute inventory", color=GREEN)
    log(
        "SEC",
        f"TPM 2.0 remote attestation {C('PASS', GREEN_HI, bold=True)}  ·  secure-boot chain verified  ·  PCR7 {C(rand_hex(16), FAINT)}",
    )
    spinner("autotuning cuBLASLt / cuDNN kernels for this SKU", 1.3, ok="1,284 kernels JIT-compiled")


def stage_modules():
    section(2, "Dynamic Module Link", "signed shared objects")
    for name, ver, feat in MODULES:
        spinner(f"dlopen {C(name, INK, bold=True)} {C(ver, MUTE)}", random.uniform(0.28, 0.55), ok=f"linked · {feat}")
    log(
        "SEC",
        f"ABI matrix resolved {C('10/10', GREEN_HI, bold=True)}  ·  0 conflicts  ·  ed25519 signatures {C('OK', GREEN_HI)}",
    )


def stage_ingest():
    section(3, "Cohort Ingestion & Sharding", "PHI-safe · HIPAA Safe-Harbor")
    log("DATA", f"mount {C('s3://biocity-phi/cohort-2026Q3', INK)}  {C('(AES-256, envelope-KMS)', MUTE)}")
    log("SEC", f"de-identification {C('k-anonymity (k=25)', INK)} + l-diversity enforced")
    progress("ingest ", 3_336_412, unit="rec", rate=(90_000, 260_000), c1=GREEN, c2=GREEN_HI)
    progress("decode ", 512_004, unit="assay", rate=(20_000, 70_000), c1=GREEN_HI, c2=CYAN)
    progress("shard  ", 4096, unit="shard", rate=(200, 900), c1=CYAN, c2=SKY)
    log(
        "PERF",
        f"columnar re-encode {C('Parquet + ZSTD-19', INK)}  ratio {C('7.4:1', GREEN_HI)}  {C('1.98 TiB → 274 GiB', MUTE)}",
    )
    log(
        "OK",
        f"feature store materialised  {C('612 features × 3.33M rows', MUTE)}  ·  null-rate {C('0.014%', GREEN_HI)}",
    )


def stage_calibrate():
    section(4, "Spectrometer & Assay Calibration", "NABL / ISO-15189 · cert MC-6991")
    rows = []
    for a in ASSAYS:
        cv = random.uniform(0.4, 2.4)
        drift = random.uniform(-0.8, 0.8)
        ok = cv < 2.6
        badge = C("PASS", GREEN_HI, bold=True) if ok else C("REVIEW", WARN, bold=True)
        rows.append(
            f"{C(a, INK):<28} CV {minibar(cv / 3, 8, GREEN, WARN)} {C(f'{cv:4.2f}%', INK)}   "
            f"drift {C(f'{drift:+4.2f}σ', MUTE)}   LJ {badge}"
        )
    panel(rows, title="Levey-Jennings QC · Westgard multi-rule", color=CYAN)
    log(
        "MATH",
        f"channel deconvolution {C('Voigt fit', INK)}  R² {C('0.99978', GREEN_HI)}  residual {C('3.1e-05', MUTE)}",
    )
    spinner("freezing calibration coefficients + reference lots", 1.0, ok="12/12 assays in-control")


def stage_architecture():
    section(5, "Model Graph :: SpectraFormer-XL", "1.74B params · 48 layers · bf16+fp8")
    diag = [
        f"{C('input', MUTE)} {C('▸', DIM)} {C('[ Spectra-Embed ]', SKY)} d=2048 {C('▸', DIM)} {C('[ Conv1D ×3 ]', CYAN)} {C('▸', DIM)} {C('[ Transformer ×48 ]', GREEN_HI, bold=True)}",
        f"        {C('▸', DIM)} {C('[ Cross-Attn Pool ]', CYAN)} {C('▸', DIM)} {C('[ MoE-FFN 8e ]', SKY)} {C('▸', DIM)} {C('[ Calibrated Head ]', GREEN_HI)} {C('▸', DIM)} {C('12 assays', INK, bold=True)}",
    ]
    panel(diag, title="forward graph", color=VIOLET)
    log(
        "PERF",
        f"precision {C('bf16 + fp8 (E4M3)', INK)}  ·  ZeRO-3  ·  grad-ckpt  ·  flash-attn-3  ·  {C('4× H100', GOLD)}",
    )
    stage_train()


def stage_train():
    epochs = 2 if SPEED <= 0.2 else 3
    steps = 26
    loss, acc, lr = random.uniform(4.4, 4.9), random.uniform(0.42, 0.51), 3.0e-4
    hist = []
    live = Live(7)
    out()  # leave a blank line above the dashboard
    for ep in range(1, epochs + 1):
        for st in range(1, steps + 1):
            loss = max(0.021, loss - random.uniform(0.03, 0.16) + random.uniform(-0.01, 0.02))
            acc = min(0.9994, acc + random.uniform(0.004, 0.02))
            lr *= 0.995
            hist.append(loss)
            hist[:] = hist[-46:]
            gpus = [random.randint(90, 100) for _ in range(4)]
            gnorm = random.uniform(0.4, 1.9)
            tflops = random.uniform(41, 49) * 4
            tok = random.randint(180_000, 340_000)
            fr = st / steps
            lines = [
                C("  ┏━ optimisation dashboard ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", FAINT),
                f"  {C('epoch', MUTE)} {C(f'{ep}/{epochs}', INK, bold=True)}   "
                f"{C('step', MUTE)} {C(f'{st:02d}/{steps}', INK, bold=True)}   "
                f"{minibar(fr, 26, GREEN, CYAN)} {C(f'{fr * 100:4.0f}%', INK)}",
                f"  {C('loss', MUTE)}  {spark(hist)} {C(f'{loss:6.4f}', GOLD, bold=True)}   "
                f"{C('acc', MUTE)} {C(f'{acc * 100:5.2f}%', GREEN_HI, bold=True)}   "
                f"{C('lr', MUTE)} {C(f'{lr:.2e}', MUTE)}   {C('|g|', MUTE)} {C(f'{gnorm:4.2f}', MUTE)}",
                f"  {C('gpu', MUTE)}  "
                + "   ".join(
                    f"{C(f'{i}', GOLD)}{minibar(gpus[i] / 100, 8, GREEN, GOLD)}{C(f'{gpus[i]:>3}%', INK)}"
                    for i in range(4)
                ),
                f"  {C('perf', MUTE)} {C(f'{tflops:5.0f} TFLOPs', VIOLET, bold=True)}   "
                f"{C(f'{tok:,} tok/s', CYAN)}   {C('mem', MUTE)} {C(f'{random.uniform(71, 78):.1f}/80 GB', MUTE)}",
                f"  {C('sync', MUTE)} NCCL ring-allreduce {C('✔', GREEN_HI)}   "
                f"{C('ckpt', MUTE)} {C(rand_hex(12), FAINT)}",
                C("  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", FAINT),
            ]
            live.render(lines)
            nap(0.05, 0.12)
    log(
        "MATH",
        f"AUROC {C('0.9971', GREEN_HI, bold=True)}  ·  AUPRC {C('0.9863', GREEN_HI)}  ·  F1 {C('0.981', GREEN_HI)}  ·  ECE {C('0.007', GREEN_HI)} {C('(temp-scaled)', MUTE)}",
    )
    log(
        "MATH",
        f"posterior check {C('MCMC 4×2000', INK)}  R̂ {C('1.001', GREEN_HI)}  ESS {C('7,914', GREEN_HI)}  divergences {C('0', GREEN_HI)}",
    )
    log("OK", f"early-stop not triggered · best-val restored {C(rand_hex(10), FAINT)}")


def stage_federated():
    section(6, "Federated Aggregation", "secure-agg CKKS-HE · DP ε=0.87")
    picks = random.sample(CITIES, 8)
    state = [{"city": c, "on": False, "lat": 0.0, "grad": 0.0} for c in picks]
    live = Live(len(state) + 1)

    def frame():
        rows = [C("  city            status     rtt                         Δgrad", FAINT)]
        for s in state:
            city = s["city"]
            if s["on"]:
                lat = s["lat"]
                grd = s["grad"]
                col = GREEN_HI if lat < 20 else (WARN if lat < 32 else BAD)
                citycol = C(f"{city:<14}", INK)
                dot = C("●", col)
                status = C("online ", col)
                bar = minibar(min(1.0, lat / 45), 16, GREEN, WARN)
                latstr = C(f"{lat:5.1f}ms", col)
                grdstr = C(f"{grd:4.1f} MiB", MUTE)
                rows.append(f"  {citycol} {dot} {status}  {bar} {latstr}   {grdstr}")
            else:
                citycol = C(f"{city:<14}", MUTE)
                rows.append(f"  {citycol} {C('○', FAINT)} {C('…handshake', FAINT)}")
        return rows

    live.render(frame())
    order = list(range(len(state)))
    random.shuffle(order)
    for idx in order:
        state[idx]["on"] = True
        state[idx]["lat"] = random.uniform(3.2, 41.0)
        state[idx]["grad"] = random.uniform(2.0, 19.0)
        live.render(frame())
        nap(0.12, 0.28)
    spinner("ring-allreduce gradient sync across 62 nodes (secure-agg)", 1.4, ok="convergence Δ < 1e-4")
    log(
        "OK",
        f"global model v3 committed  ·  {C('62/62', GREEN_HI, bold=True)} nodes acked  ·  staleness {C('0', GREEN_HI)}",
    )


def stage_genomics():
    section(7, "Genomic Alignment & Variant Calling", "GRCh38.p14 · GATK-compatible")
    progress("align  ", 148_204_331, unit="read", rate=(1_800_000, 5_200_000), c1=GREEN, c2=MINT)
    log(
        "BIO",
        f"mapped {C('99.62%', GREEN_HI)}  ·  dup {C('4.1%', MUTE)}  ·  mean-depth {C('38.7×', INK)}  ·  insert-size {C('312bp', MUTE)}",
    )
    spinner("HaplotypeCaller → GVCF joint genotyping", 1.5, ok="4,812,336 sites")
    rows = []
    for g in random.sample(GENES, 5):
        q = random.randint(38, 60)
        af = random.uniform(0.001, 0.48)
        rows.append(
            f"{C(g, INK, bold=True):<24} {C('chr' + str(random.randint(1, 22)), MUTE)}:{random.randint(10**6, 10**8):,}"
            f"   phred {C('Q' + str(q), GREEN_HI)}   AF {C(f'{af:.3f}', MUTE)}   ClinVar {C('benign', GREEN_HI)}"
        )
    panel(rows, title="pharmacogenomic panel · CPIC-scored", color=MINT)


def stage_anchor():
    section(8, "Report Synthesis & Cryptographic Anchoring", "append-only ledger · PQC")
    progress("render ", 3336, unit="report", rate=(120, 520), c1=CYAN, c2=SKY)
    for _ in range(3):
        log("SEC", f"merkle-leaf {C(rand_hex(48), FAINT)}  signed {C('ed25519', GREEN_HI)}", tag="anchor")
    root = rand_hex(64)
    log("SEC", f"merkle-root {C(root[:32], SKY, bold=True)}{C(root[32:], FAINT)}")
    spinner("anchoring root to ledger (Dilithium-3, quantum-resistant)", 1.2, ok="block #4,182,907 sealed")
    log("OK", "reports immutable · verifiable · QR + WhatsApp delivery queued")


def stage_summary(t0):
    out()
    hrule(GREEN, CYAN, "━")
    out(_center(gradient("  P I P E L I N E   C O M P L E T E  ", GREEN_HI, CYAN, bold=True)))
    hrule(GREEN, CYAN, "━")
    el = time.time() - t0
    metrics = [
        ("records processed", "3,336,412", 1.00, CYAN),
        ("assays in-control", "12 / 12", 1.00, GREEN_HI),
        ("model parameters", "1.74 B", 0.87, VIOLET),
        ("validation AUROC", "0.9971", 0.997, GREEN_HI),
        ("expected calib. error", "0.007", 0.06, GREEN_HI),
        ("federated nodes", "62 / 62", 1.00, GREEN_HI),
        ("variants called", "4,812,336", 0.78, CYAN),
        ("reports anchored", "3,336", 1.00, GREEN_HI),
        ("differential-privacy ε", "0.87", 0.30, WARN),
        ("peak throughput", "5.2M reads/s", 0.92, VIOLET),
    ]
    rows = []
    for name, val, frac, col in metrics:
        label = C(name, MUTE)
        pad = 24 - vlen(label)
        rows.append(
            f"{label}{' ' * max(1, pad)}{minibar(frac, 22, col, lerp(col, INK, 0.4))}  {C(val, INK, bold=True)}"
        )
    panel(rows, title="run summary", color=GREEN)
    art = "biocity-model-v3-" + rand_hex(20)
    log("OK", f"artifact  {C(art, INK)}")
    log(
        "OK",
        f"status    {C('CONVERGED', GREEN_HI, bold=True)}  ·  promoted → {C('registry://prod/biocity/v3', SKY)}  ·  {C(f'{el:0.1f}s wall-clock', MUTE)}",
    )
    out()
    out(
        "  "
        + C("●", GREEN_HI)
        + " "
        + C("Biocity Diagnostic Intelligence Engine v3 — ready for production traffic.", INK, bold=True)
    )
    out("  " + C("  demo build · figures synthetic · not for clinical use", FAINT))
    out()


# ─────────────────────────────────────────────────────────────────────────────
#  Stage 9 — live hosting + real edge telemetry
# ─────────────────────────────────────────────────────────────────────────────
def _human(n):
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}GB"


def _trunc(s, n):
    return s if len(s) <= n else (s[: max(1, n - 1)] + "…")


def _bind_server(handler, port):
    for p in [port, *range(port + 1, port + 40)]:
        try:
            return ThreadingHTTPServer(("127.0.0.1", p), handler), p
        except OSError:
            continue
    return None, port


def _open_chrome(url):
    if sys.platform == "darwin":
        for cmd, name in ((["open", "-a", "Google Chrome", url], "Google Chrome"), (["open", url], "default browser")):
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return name
            except Exception:
                continue
    try:
        webbrowser.open(url)
        return "default browser"
    except Exception:
        return None


def stage_serve():
    section(9, "Live Deployment & Edge Telemetry", "local edge node · real traffic")

    events = deque()
    lock = threading.Lock()

    class Tele(SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a, **k):
            pass

        def send_response(self, code, message=None):
            self._code = code
            super().send_response(code, message)

        def send_header(self, keyword, value):
            if keyword.lower() == "content-length":
                with contextlib.suppress(ValueError):
                    self._size = int(value)
            super().send_header(keyword, value)

        def handle_one_request(self):
            self._t0 = time.time()
            self._code = 0
            self._size = 0
            self.command = None  # so a keep-alive empty read isn't logged as a phantom
            try:
                super().handle_one_request()
            finally:
                if getattr(self, "command", None):
                    ev = {
                        "ip": self.client_address[0],
                        "method": self.command,
                        "path": self.path or "/",
                        "code": self._code or 200,
                        "size": self._size,
                        "ms": (time.time() - self._t0) * 1000.0,
                        "t": time.time(),
                    }
                    with lock:
                        events.append(ev)

    server, port = _bind_server(partial(Tele, directory=ROOT), PORT)
    if server is None:
        log("WARN", f"could not bind a local port near {PORT} — skipping live host")
        return
    url = f"http://localhost:{port}/v3/"
    threading.Thread(target=server.serve_forever, name="httpd", daemon=True).start()
    log(
        "NET",
        f"edge node online  ·  bound {C('127.0.0.1:' + str(port), INK, bold=True)}  ·  document-root {C(ROOT, MUTE)}",
    )
    log("OK", f"Biocity v3 is live  →  {C(url, SKY, bold=True)}")
    if NO_OPEN:
        log("INFO", "browser auto-open disabled (--no-open)")
    else:
        who = _open_chrome(url)
        if who:
            log("NET", f"opening {C(who, INK)}  ·  {C(url, SKY)}")
        else:
            log("WARN", "no browser could be launched — open the URL manually")

    total = 0
    bytes_total = 0
    codes = {2: 0, 3: 0, 4: 0, 5: 0}
    ips = set()
    lat = deque(maxlen=400)
    evq = deque(maxlen=6000)
    rps_hist = deque([0], maxlen=40)
    feed = deque(maxlen=13)
    start = time.time()
    last_sec = int(start)
    sec_count = 0
    tty = sys.stdout.isatty()

    def pctl(sv, q):
        if not sv:
            return 0.0
        return sv[min(len(sv) - 1, int(q * len(sv)))]

    def feed_line(e, bud):
        m, code, ms = e["method"], e["code"], e["ms"]
        size, ip, path = e["size"], e["ip"], e["path"]
        mc = {"GET": CYAN, "HEAD": DIM, "POST": VIOLET, "OPTIONS": MUTE}.get(m, MUTE)
        cc = GREEN_HI if code < 300 else (SKY if code < 400 else (WARN if code < 500 else BAD))
        msc = GREEN_HI if ms < 25 else (WARN if ms < 150 else BAD)
        path_w = max(14, bud - 51)
        ptxt = _trunc(path, path_w)
        tstr = time.strftime("%H:%M:%S", time.localtime(e["t"]))
        return (
            f"{C(tstr, FAINT)} {C(f'{m:<4}', mc, bold=True)} {C(f'{code:>3}', cc, bold=True)} "
            f"{C(f'{ptxt:<{path_w}}', INK)} {C(f'{_human(size):>7}', MUTE)} "
            f"{C(f'{ms:6.1f}ms', msc)} {C(f'{ip:<15}', FAINT)}"
        )

    log("INFO", C("streaming live access log — interact with the page in Chrome to see traffic", MUTE))
    out()
    live = Live(20) if tty else None

    # Explicit signal handling: overrides the SIG_IGN the shell hands to
    # background jobs, so Ctrl-C (and TERM) always stop the server cleanly.
    stop = threading.Event()
    old_int = signal.getsignal(signal.SIGINT)
    old_term = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    with contextlib.suppress(Exception):
        signal.signal(signal.SIGTERM, lambda *_: stop.set())

    try:
        while not stop.is_set():
            now = time.time()
            with lock:
                batch = list(events)
                events.clear()
            for e in batch:
                total += 1
                bytes_total += e["size"]
                cls = e["code"] // 100
                cls = 2 if cls < 2 else (5 if cls > 5 else cls)
                codes[cls] = codes.get(cls, 0) + 1
                ips.add(e["ip"])
                lat.append(e["ms"])
                evq.append((e["t"], e["size"]))
                sec_count += 1
                fl = feed_line(e, COLS - 4)
                feed.append(fl)
                if not tty:
                    out(fl)
            if int(now) != last_sec:
                for _ in range(int(now) - last_sec):
                    rps_hist.append(sec_count)
                    sec_count = 0
                last_sec = int(now)
            if tty:
                w3 = [x for x in evq if x[0] > now - 3]
                rps = len(w3) / 3.0
                bps = sum(s for _, s in w3) / 3.0
                sv = sorted(lat)
                p50, p95 = pctl(sv, 0.50), pctl(sv, 0.95)
                pmax = sv[-1] if sv else 0.0
                up = now - start
                sp = spark(list(rps_hist), GREEN_HI, CYAN)
                cpu = min(0.99, 0.05 + rps * 0.014 + random.uniform(0, 0.03))
                mem = 0.33 + 0.10 * (0.5 + 0.5 * math.sin(now / 6.0))
                vit = [
                    f"{C('◆', GREEN_HI)} {C('SERVING', GREEN_HI, bold=True)}   "
                    f"{C('uptime', MUTE)} {C(f'{up:6.1f}s', INK)}   "
                    f"{C('requests', MUTE)} {C(f'{total:>6,}', INK, bold=True)}   "
                    f"{C('req/s', MUTE)} {C(f'{rps:5.1f}', VIOLET, bold=True)} {sp}",
                    f"{C('latency', MUTE)} p50 {C(f'{p50:5.1f}ms', GREEN_HI)}  "
                    f"p95 {C(f'{p95:6.1f}ms', WARN)}  max {C(f'{pmax:6.1f}ms', MUTE)}   "
                    f"{C('served', MUTE)} {C(_human(bytes_total), GREEN_HI)} "
                    f"{C(f'({_human(bps)}/s)', FAINT)}",
                    f"{C('2xx', MUTE)} {C(str(codes.get(2, 0)), GREEN_HI)}  "
                    f"{C('3xx', MUTE)} {C(str(codes.get(3, 0)), SKY)}  "
                    f"{C('4xx', MUTE)} {C(str(codes.get(4, 0)), WARN)}  "
                    f"{C('5xx', MUTE)} {C(str(codes.get(5, 0)), BAD)}   "
                    f"{C('clients', MUTE)} {C(str(len(ips)), INK)}   "
                    f"{C('workers', MUTE)} {C(str(threading.active_count()), INK)}   "
                    f"{C('cpu', MUTE)} {minibar(cpu, 8, GREEN, WARN)}  "
                    f"{C('mem', MUTE)} {minibar(mem, 8, GREEN, SKY)}",
                ]
                block = panel_lines(vit, title="server vitals · live", color=GREEN)
                fl = list(feed) or [C("waiting for the browser to reach the edge node…", FAINT)]
                while len(fl) < 13:
                    fl.append("")
                block += panel_lines(fl[-13:], title="access log · live  ·  Ctrl-C to stop", color=CYAN)
                live.render(block)
            stop.wait(0.12)
    except KeyboardInterrupt:
        pass
    finally:
        with contextlib.suppress(Exception):
            signal.signal(signal.SIGINT, old_int)
        with contextlib.suppress(Exception):
            signal.signal(signal.SIGTERM, old_term)
        with contextlib.suppress(Exception):
            server.shutdown()
    with lock:
        rest = list(events)
        events.clear()
    for e in rest:
        total += 1
        bytes_total += e["size"]
    out()
    log(
        "OK",
        f"edge node drained · {C(f'{total:,}', INK, bold=True)} requests served · {C(_human(bytes_total), GREEN_HI)} egress · uptime {C(f'{time.time() - start:.1f}s', MUTE)}",
    )
    out("  " + C("● server stopped — thanks for watching.", GREEN_HI, bold=True))
    out()


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    if USE_COLOR:
        w("\033[?25l")  # hide cursor
    try:
        stage_banner()
        stage_hardware()
        stage_modules()
        stage_ingest()
        stage_calibrate()
        stage_architecture()
        stage_federated()
        stage_genomics()
        stage_anchor()
        stage_summary(t0)
        if not NO_SERVE:
            stage_serve()
    except KeyboardInterrupt:
        out("\n" + C("✗ interrupted — tearing down CUDA context, flushing buffers…", BAD))
        nap(0.2)
        out(C("  clean shutdown complete.", MUTE))
        sys.exit(130)
    finally:
        if USE_COLOR:
            w("\033[?25h")  # restore cursor
            flush()


if __name__ == "__main__":
    main()
