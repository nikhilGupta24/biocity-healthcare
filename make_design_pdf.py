#!/usr/bin/env python3
"""
Biocity v3 — design-board PDF exporter.

Captures the v3 site as full-page screenshots in four variants
(desktop/mobile x light/dark), frames them like Figma artboards, and
renders a single self-contained PDF via headless Chrome (DevTools Protocol).

    python3 make_design_pdf.py

No third-party dependencies — only the Python standard library + Google Chrome.
Re-run it any time the design changes to refresh the PDF.
"""

import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_PATH = "/v3/index.html"
OUTDIR = os.path.join(ROOT, "design-export")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

VARIANTS = [
    ("desktop", "light", 1440, 900, False),
    ("desktop", "dark", 1440, 900, False),
    ("mobile", "light", 390, 844, True),
    ("mobile", "dark", 390, 844, True),
]
# High-DPI capture. Tall pages exceed Chrome's max image size, so we grab each
# page in vertical segments at full scale and stack them seamlessly in the PDF.
SCALE = {"desktop": 2, "mobile": 3}   # device pixel ratio → desktop ~2880px, mobile ~1170px wide
SAFE_PX = 12000                       # max pixels per segment (stays within Chrome's texture limit)


# ── minimal WebSocket client (CDP is websocket-only) ─────────────────────────
class WS:
    def __init__(self, url):
        assert url.startswith("ws://")
        host_port, _, path = url[5:].partition("/")
        host, _, port = host_port.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=30)
        self.sock.settimeout(60)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        if b"101" not in buf.split(b"\r\n", 1)[0]:
            raise RuntimeError("websocket upgrade failed")
        self._id = 0
        self.events = []

    def _recv_exact(self, n):
        out = b""
        while len(out) < n:
            chunk = self.sock.recv(n - len(out))
            if not chunk:
                raise ConnectionError("socket closed")
            out += chunk
        return out

    def _recv_frame(self):
        data = bytearray()
        while True:
            b1, b2 = self._recv_exact(2)
            fin, opcode = b1 & 0x80, b1 & 0x0F
            ln = b2 & 0x7F
            if ln == 126:
                ln = int.from_bytes(self._recv_exact(2), "big")
            elif ln == 127:
                ln = int.from_bytes(self._recv_exact(8), "big")
            payload = self._recv_exact(ln) if ln else b""
            if opcode == 0x9:  # ping → pong
                self._send(0xA, payload)
                continue
            if opcode == 0x8:  # close
                raise ConnectionError("websocket closed by peer")
            data += payload
            if fin:
                return bytes(data)

    def _send(self, opcode, payload):
        header = bytearray([0x80 | opcode])
        ln = len(payload)
        mask = os.urandom(4)
        if ln < 126:
            header.append(0x80 | ln)
        elif ln < 65536:
            header.append(0x80 | 126)
            header += ln.to_bytes(2, "big")
        else:
            header.append(0x80 | 127)
            header += ln.to_bytes(8, "big")
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def call(self, method, params=None, timeout=60):
        self._id += 1
        mid = self._id
        self._send(0x1, json.dumps({"id": mid, "method": method, "params": params or {}}).encode())
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(self._recv_frame())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg)
        raise TimeoutError(method)

    def wait_event(self, method, timeout=30):
        for m in self.events:
            if m.get("method") == method:
                return m
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(self._recv_frame())
            if msg.get("method") == method:
                return msg
            if "method" in msg:
                self.events.append(msg)
        return None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# ── helpers ──────────────────────────────────────────────────────────────────
def http_json(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


REVEAL_JS = """
new Promise(async (resolve) => {
  const root = document.documentElement;
  root.setAttribute('data-theme', '%THEME%');
  try { localStorage.setItem('biocity-theme', '%THEME%'); } catch (e) {}
  const st = document.createElement('style');
  st.textContent = '*{animation:none!important;transition:none!important;scroll-behavior:auto!important}'
    + '.reveal{opacity:1!important;transform:none!important}';
  document.head.appendChild(st);
  document.querySelectorAll('.reveal').forEach(e => e.classList.add('visible'));
  const h = () => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  let y = 0;
  while (y < h()) { window.scrollTo(0, y); y += 500; await new Promise(r => setTimeout(r, 12)); }
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 400));
  resolve(h());
});
"""


def capture(dbg, site_url, kind, theme, w, h, mobile):
    tgt = http_json(f"{dbg}/json/new?about:blank", method="PUT")
    ws = WS(tgt["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        scale = SCALE[kind]
        ws.call("Emulation.setDeviceMetricsOverride",
                {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile})
        ws.call("Page.navigate", {"url": site_url})
        ws.wait_event("Page.loadEventFired", timeout=30)
        time.sleep(1.2)
        res = ws.call("Runtime.evaluate", {
            "expression": REVEAL_JS.replace("%THEME%", theme),
            "awaitPromise": True, "returnByValue": True,
        }, timeout=60)
        page_h = int(res.get("result", {}).get("value") or h)
        # lay out the full page, then capture it in high-DPI vertical segments
        ws.call("Emulation.setDeviceMetricsOverride",
                {"width": w, "height": page_h, "deviceScaleFactor": 1, "mobile": mobile})
        time.sleep(0.3)
        seg_css = max(200, int(SAFE_PX / scale))          # css-px height per segment
        segments, y, idx = [], 0, 0
        while y < page_h:
            sh = min(seg_css, page_h - y)
            shot = ws.call("Page.captureScreenshot", {
                "format": "png", "captureBeyondViewport": True, "fromSurface": True,
                "clip": {"x": 0, "y": y, "width": w, "height": sh, "scale": scale},
            }, timeout=120)
            name = f"{kind}-{theme}-{idx}.png"
            with open(os.path.join(OUTDIR, name), "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            segments.append(name)
            y += sh
            idx += 1
        print(f"  captured {kind} · {theme}  ({w * scale}px wide · {page_h * scale}px tall · "
              f"{len(segments)} segment{'s' if len(segments) > 1 else ''})")
        return segments
    finally:
        try:
            http_json(f"{dbg}/json/close/{tgt['id']}")
        except Exception:
            pass
        ws.close()


# ── Figma-style presentation ─────────────────────────────────────────────────
def build_presentation(shots):
    date = datetime.now().strftime("%d %b %Y")

    def imgs(srcs, label):
        return "".join(f'<img src="{s}" alt="{label}">' for s in srcs)

    def desktop_frame(srcs, label):
        return f"""
        <section class="board">
          <div class="cap"><span class="tag">{label}</span></div>
          <div class="win">
            <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
              <span class="url">biocityhealthcare.com</span></div>
            <div class="stack">{imgs(srcs, label)}</div>
          </div>
        </section>"""

    def mobile_frame(srcs, label):
        return f"""
        <section class="board">
          <div class="cap"><span class="tag">{label}</span></div>
          <div class="phone"><span class="notch"></span><div class="stack">{imgs(srcs, label)}</div></div>
        </section>"""

    body = (
        desktop_frame(shots["desktop-light"], "Desktop · Light")
        + desktop_frame(shots["desktop-dark"], "Desktop · Dark")
        + mobile_frame(shots["mobile-light"], "Mobile · Light")
        + mobile_frame(shots["mobile-dark"], "Mobile · Dark")
    )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
@page{{size:A4;margin:0}}
:root{{--ink:#0e1512;--mut:#6b7a76;--line:#e3e8e6;--accent:#10B981}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:-apple-system,'Segoe UI',sans-serif;background:#eef1f0;color:var(--ink)}}
.cover{{height:297mm;display:flex;flex-direction:column;justify-content:center;padding:0 26mm;
  background:linear-gradient(150deg,#0b3d33,#0e1512 70%);color:#eafff7;break-after:page}}
.cover .k{{font:600 12px/1 ui-monospace,monospace;letter-spacing:3px;text-transform:uppercase;color:#5eead4;margin-bottom:20px}}
.cover h1{{font-size:52px;font-weight:800;letter-spacing:-1.5px;line-height:1.05;margin-bottom:16px}}
.cover h1 span{{color:#34d399}}
.cover p{{font-size:16px;color:#9fc7bd;max-width:460px;line-height:1.6}}
.cover .meta{{margin-top:40px;display:flex;gap:10px;flex-wrap:wrap}}
.cover .meta b{{font:600 12px/1 ui-monospace,monospace;letter-spacing:1px;background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.16);padding:9px 14px;border-radius:100px;color:#d7fff2}}
.board{{break-before:page;padding:14mm 14mm 0;background:#eef1f0}}
.board img{{break-inside:avoid-page}}
.cap{{margin-bottom:14px}}
.tag{{font:700 11px/1 ui-monospace,monospace;letter-spacing:2px;text-transform:uppercase;color:var(--mut);
  background:#fff;border:1px solid var(--line);padding:8px 14px;border-radius:100px}}
.win{{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;
  box-shadow:0 18px 50px rgba(14,21,18,.14)}}
.bar{{height:38px;display:flex;align-items:center;gap:7px;padding:0 14px;background:#f6f8f7;border-bottom:1px solid var(--line)}}
.dot{{width:11px;height:11px;border-radius:50%}}
.dot.r{{background:#ff5f57}}.dot.y{{background:#febc2e}}.dot.g{{background:#28c840}}
.url{{margin-left:12px;font:500 12px/1 ui-monospace,monospace;color:var(--mut);
  background:#fff;border:1px solid var(--line);padding:6px 16px;border-radius:100px}}
.stack{{font-size:0;line-height:0}}
.stack img{{width:100%;display:block}}
.phone{{width:300px;margin:0 auto;border:11px solid #12100f;border-radius:42px;overflow:hidden;
  background:#12100f;box-shadow:0 22px 60px rgba(14,21,18,.22);position:relative}}
.phone .notch{{position:absolute;top:0;left:50%;transform:translateX(-50%);width:120px;height:22px;
  background:#12100f;border-radius:0 0 16px 16px;z-index:2}}
.phone .stack{{border-radius:30px;overflow:hidden}}
</style></head><body>
<div class="cover">
  <div class="k">Biocity Healthcare · v3</div>
  <h1>Website Design<br><span>Preview Board</span></h1>
  <p>The v3 diagnostics website, shown in desktop and mobile layouts across light and dark themes.</p>
  <div class="meta"><b>4 Artboards</b><b>Light + Dark</b><b>Web + Mobile</b><b>{date}</b></div>
</div>
{body}
</body></html>"""
    path = os.path.join(OUTDIR, "presentation.html")
    with open(path, "w") as f:
        f.write(html)
    return path


def render_pdf(dbg, pres_path):
    tgt = http_json(f"{dbg}/json/new?about:blank", method="PUT")
    ws = WS(tgt["webSocketDebuggerUrl"])
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
        out = os.path.join(OUTDIR, "Biocity-v3-Design.pdf")
        with open(out, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        return out
    finally:
        try:
            http_json(f"{dbg}/json/close/{tgt['id']}")
        except Exception:
            pass
        ws.close()


def main():
    if not os.path.exists(CHROME):
        sys.exit("Google Chrome not found at the expected path.")
    os.makedirs(OUTDIR, exist_ok=True)

    # 1) serve the site so ../assets/* resolve
    web_port = free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", web_port),
                                partial(SimpleHTTPRequestHandler, directory=ROOT))
    httpd.RequestHandlerClass.log_message = lambda *a, **k: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    site_url = f"http://127.0.0.1:{web_port}{SITE_PATH}"
    print(f"serving site at {site_url}")

    # 2) launch headless Chrome with the DevTools endpoint open
    dbg_port = free_port()
    profile = tempfile.mkdtemp(prefix="biocity-pdf-")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--no-first-run", "--no-default-browser-check", "--disable-extensions",
         "--force-color-profile=srgb", "--font-render-hinting=none",
         f"--remote-debugging-port={dbg_port}", f"--user-data-dir={profile}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    dbg = f"http://127.0.0.1:{dbg_port}"
    for _ in range(100):
        try:
            http_json(f"{dbg}/json/version")
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        sys.exit("Chrome DevTools endpoint did not come up.")

    try:
        print("capturing artboards…")
        shots = {}
        for kind, theme, w, h, mobile in VARIANTS:
            shots[f"{kind}-{theme}"] = capture(dbg, site_url, kind, theme, w, h, mobile)
        print("composing Figma-style board…")
        pres = build_presentation(shots)
        print("rendering PDF…")
        pdf = render_pdf(dbg, pres)
        print(f"\n✓ PDF ready: {pdf}")
    finally:
        proc.terminate()
        httpd.shutdown()


if __name__ == "__main__":
    main()
