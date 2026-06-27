#!/usr/bin/env python3
"""Build ``docs/diagrams/index.html`` embedding every Mermaid ``.mmd`` source.

Rendering happens client-side in the viewer's browser via the Mermaid CDN, so
CI needs no Chromium/puppeteer — it only writes this static HTML file. Each
diagram's source is JSON-encoded and rendered with ``mermaid.render()``, which
avoids the HTML-parsing pitfalls of putting raw ``<br/>`` / ``&lt;`` into
``<pre>`` blocks.
"""

from __future__ import annotations

import json
from pathlib import Path

DIAGRAMS_DIR = Path("docs/diagrams")
OUTPUT = DIAGRAMS_DIR / "index.html"

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PipelineKit Diagrams</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #0d1117; color: #c9d1d9; }
  header { padding: 1.5rem 2rem; border-bottom: 1px solid #30363d; }
  header h1 { margin: 0; font-size: 1.4rem; }
  header p { margin: .35rem 0 0; color: #8b949e; font-size: .9rem; }
  main { padding: 1rem 2rem 4rem; max-width: 1100px; }
  section { margin: 2rem 0; padding: 1rem 1.25rem; background: #161b22; border: 1px solid #30363d; border-radius: 8px; }
  section h2 { margin: 0 0 1rem; font-size: 1.05rem; color: #58a6ff; font-family: ui-monospace, monospace; }
  .err { color: #ff7b72; white-space: pre-wrap; font-family: ui-monospace, monospace; }
  .mmd svg { max-width: 100%; height: auto; }
</style>
</head>
<body>
<header>
  <h1>PipelineKit Diagrams</h1>
  <p>Rendered client-side via Mermaid (CDN). Sources: docs/diagrams/*.mmd</p>
</header>
<main id="container"></main>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });
const diagrams = __DATA__;
const container = document.getElementById('container');
for (const d of diagrams) {
  const section = document.createElement('section');
  const h = document.createElement('h2');
  h.textContent = d.title;
  section.appendChild(h);
  const target = document.createElement('div');
  target.className = 'mmd';
  section.appendChild(target);
  container.appendChild(section);
  try {
    const { svg } = await mermaid.render('mmd_' + d.id, d.code);
    target.innerHTML = svg;
  } catch (e) {
    const pre = document.createElement('pre');
    pre.className = 'err';
    pre.textContent = 'Render error: ' + (e && e.message ? e.message : String(e));
    target.appendChild(pre);
  }
}
</script>
</body>
</html>
"""


def main() -> None:
    files = sorted(DIAGRAMS_DIR.glob("*.mmd"))
    items = [
        {
            "id": f.stem.replace("-", "_"),
            "title": f.stem,
            "code": f.read_text(encoding="utf-8"),
        }
        for f in files
    ]
    html = _TEMPLATE.replace("__DATA__", json.dumps(items, indent=2))
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(items)} diagram(s).")


if __name__ == "__main__":
    main()
