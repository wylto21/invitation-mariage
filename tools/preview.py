#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendu PNG d'un extrait de decoration, pour verifier sans navigateur.

Usage :
    python3 tools/preview.py medallion /tmp/med.png 240 320 '<use .../>'

Le sprite complet (defs + symboles) est resolu, donc les <use href="#fl-...">
fonctionnent dans l'extrait fourni.
"""
import pathlib
import subprocess
import sys
import cairosvg

ROOT = pathlib.Path(__file__).resolve().parent.parent


def sprite():
    out = subprocess.run([sys.executable, str(ROOT / "tools/floral-sprite.py"), "--print"],
                         capture_output=True, text=True, check=True).stdout
    body = out[out.index(">", out.index('<svg class="sprite"')) + 1:]
    return body[:body.rindex("</svg>")]


def render(name, dest, w, h, snippet, bg="#faf4ea", scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}">'
           f'<defs><rect width="{w}" height="{h}" fill="{bg}"/></defs>'
           + sprite() + snippet + "</svg>")
    tmp = pathlib.Path("/tmp") / f"_{name}.svg"
    tmp.write_text(svg, encoding="utf-8")
    cairosvg.svg2png(url=str(tmp), write_to=dest,
                     output_width=int(w * scale), output_height=int(h * scale),
                     background_color=bg)
    return dest


if __name__ == "__main__":
    n, d, w, h, sn = sys.argv[1:6]
    print(render(n, d, int(w), int(h), sn))
