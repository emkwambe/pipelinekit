#!/usr/bin/env python3
"""Build ``docs/diagrams/index.html`` from the diagram sources.

Two source kinds live side by side in ``docs/diagrams/``:

- ``*.mmd`` — Mermaid diagrams (flowcharts, sequence, ER). Rendered client-side
  via the Mermaid CDN with ``mermaid.render()``.
- ``*.md``  — Markdown table documents (e.g. the CLI map, error taxonomy,
  blueprint catalog). Rendered client-side via the ``marked`` CDN.

Rendering happens in the viewer's browser, so CI needs no Chromium/puppeteer —
it only writes this static HTML file. ``README.md`` is excluded.
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
  section h2.diagram-title { margin: 0 0 1rem; font-size: 1.05rem; color: #58a6ff; font-family: ui-monospace, monospace; }
  .err { color: #ff7b72; white-space: pre-wrap; font-family: ui-monospace, monospace; }
  .mmd svg { max-width: 100%; height: auto; }
  .md h1 { font-size: 1.15rem; color: #e6edf3; }
  .md h2 { font-size: 1.0rem; color: #adbac7; }
  .md table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .9rem; }
  .md th, .md td { border: 1px solid #30363d; padding: .45rem .6rem; text-align: left; vertical-align: top; }
  .md th { background: #21262d; color: #e6edf3; }
  .md tr:nth-child(even) td { background: #0f141a; }
  .md code { background: #21262d; padding: .1rem .35rem; border-radius: 4px; font-size: .85em; }
</style>
</head>
<body>
<header>
  <h1>PipelineKit Diagrams</h1>
  <p>Rendered client-side via Mermaid + marked (CDN). Sources: docs/diagrams/*.mmd and *.md</p>
</header>
<main id="container"></main>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
import { marked } from 'https://cdn.jsdelivr.net/npm/marked@12/+esm';
mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });
const diagrams = __DATA__;
const container = document.getElementById('container');
for (const d of diagrams) {
  const section = document.createElement('section');
  const h = document.createElement('h2');
  h.className = 'diagram-title';
  h.textContent = d.title;
  section.appendChild(h);
  const target = document.createElement('div');
  section.appendChild(target);
  container.appendChild(section);
  if (d.kind === 'markdown') {
    target.className = 'md';
    target.innerHTML = marked.parse(d.code);
  } else {
    target.className = 'mmd';
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
}
</script>
</body>
</html>
"""


def _kind(path: Path) -> str:
    return "mermaid" if path.suffix == ".mmd" else "markdown"


def main() -> None:
    sources = [
        p
        for p in DIAGRAMS_DIR.iterdir()
        if p.suffix in (".mmd", ".md") and p.name.lower() != "readme.md"
    ]
    sources.sort(key=lambda p: p.name)
    items = [
        {
            "id": p.stem.replace("-", "_"),
            "title": p.stem,
            "kind": _kind(p),
            "code": p.read_text(encoding="utf-8"),
        }
        for p in sources
    ]
    html = _TEMPLATE.replace("__DATA__", json.dumps(items, indent=2))
    OUTPUT.write_text(html, encoding="utf-8")
    kinds = ", ".join(f"{i['title']} [{i['kind']}]" for i in items)
    print(f"Wrote {OUTPUT} with {len(items)} item(s):\n  {kinds}")


if __name__ == "__main__":
    main()
