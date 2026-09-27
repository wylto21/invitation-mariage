#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur du sprite floral (SVG) de l'invitation Daria & Hermann.

Reproduit la composition de la carte de référence :
camélias ivoire à étamines dorées, feuillage émeraude brillant,
fougères dorées, perles crème et anneaux dorés.

Le même bloc SVG est injecté dans index.html et invitation-landing.html
(le sprite est inliné : il ne peut pas être externalisé à cause de file://).

Usage :
    python3 tools/floral-sprite.py            # régénère et injecte
    python3 tools/floral-sprite.py --print    # affiche le bloc sur stdout
"""

import math
import pathlib
import re
import sys

# ————————————————————————————————————————————————————————————
# Palette relevée sur la carte de référence
# ————————————————————————————————————————————————————————————
IVORY_HI, IVORY, IVORY_LO, IVORY_SH = "#ffffff", "#f7f3ea", "#e5dfd0", "#cbc4b1"
GOLD_HI, GOLD, GOLD_LO = "#f4e4b4", "#cda75a", "#8c6a26"
LEAF_HI, LEAF, LEAF_LO = "#4d9175", "#1f5544", "#0b2b21"
FERN_HI, FERN, FERN_LO = "#e6d5ae", "#bda172", "#96794a"
PEARL_HI, PEARL, PEARL_LO = "#ffffff", "#f2ede2", "#c3bba8"
EDGE = "#b0aa99"          # liseré doux entre les pétales
STEM = "#2c6b52"          # branche


def n(v):
    """Arrondi propre pour un SVG lisible."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


# ————————————————————————————————————————————————————————————
# Primitives
# ————————————————————————————————————————————————————————————
def petal(r, w):
    """Pétale de camélia : éventail large et arrondi, base au point (0,0),
    pointe vers le haut (axe -Y)."""
    return (
        f"M0 0 "
        f"C{n(-w*0.95)} {n(-r*0.20)} {n(-w*1.02)} {n(-r*0.64)} {n(-w*0.48)} {n(-r*0.93)} "
        f"C{n(-w*0.24)} {n(-r*1.05)} {n(w*0.24)} {n(-r*1.05)} {n(w*0.48)} {n(-r*0.93)} "
        f"C{n(w*1.02)} {n(-r*0.64)} {n(w*0.95)} {n(-r*0.20)} 0 0 Z"
    )


def ring_petals(count, r, w, fill, cx=32.0, cy=32.0, offset=0.0,
                stroke=EDGE, sw=0.6, stroke_op=0.55, scale=1.0, opacity=1.0):
    """Couronne de pétales régulièrement réparties autour du centre."""
    out = []
    d = petal(r * scale, w * scale)
    for i in range(count):
        a = offset + i * 360.0 / count
        out.append(
            f'      <path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{n(sw)}"'
            f' stroke-opacity="{n(stroke_op)}" opacity="{n(opacity)}"'
            f' transform="translate({n(cx)} {n(cy)}) rotate({n(a)})"/>'
        )
    return out


def bez(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def bez_angle(p0, p1, p2, t):
    u = 1 - t
    x = 2 * u * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    y = 2 * u * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    return math.degrees(math.atan2(y, x))


def fronde(p0, p1, p2, count=9, l0=13.0, l1=4.0, w_ratio=0.30, spread=42.0):
    """Fougère : tige en Bézier + folioles elliptiques de part et d'autre.
    `count` élevé et `w_ratio` bas donnent la finesse de la carte."""
    out = []
    for i in range(1, count + 1):
        t = i / (count + 0.6)
        x, y = bez(p0, p1, p2, t)
        ang = bez_angle(p0, p1, p2, t)
        L = l0 + (l1 - l0) * t
        W = L * w_ratio
        for side in (-1, 1):
            rot = math.radians(ang + side * spread)
            cx = x + math.cos(rot) * L * 0.46
            cy = y + math.sin(rot) * L * 0.46
            out.append(
                f'      <ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(L*0.5)}" ry="{n(W*0.5)}"'
                f' fill="url(#g-fern)" transform="rotate({n(ang + side*spread)} {n(cx)} {n(cy)})"/>'
            )
    d = (f"M{n(p0[0])} {n(p0[1])} Q{n(p1[0])} {n(p1[1])} {n(p2[0])} {n(p2[1])}")
    out.insert(0, f'      <path d="{d}" fill="none" stroke="url(#g-fern)"'
                  f' stroke-width="1.1" stroke-linecap="round"/>')
    return out


def use(ref, x, y, w, h=None, rot=None, op=None):
    h = w if h is None else h
    t = f' transform="rotate({n(rot)} {n(x+w/2)} {n(y+h/2)})"' if rot is not None else ""
    o = f' opacity="{n(op)}"' if op is not None else ""
    return f'        <use href="#{ref}" x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"{t}{o}/>'


# ————————————————————————————————————————————————————————————
# Symboles
# ————————————————————————————————————————————————————————————
def build_defs():
    return f"""    <defs>
      <!-- camélia : ivoire éclairé en haut, ombre chaude en base -->
      <linearGradient id="p-out" x1=".28" y1="0" x2=".72" y2="1">
        <stop offset="0" stop-color="{IVORY_HI}"/><stop offset=".5" stop-color="{IVORY}"/><stop offset="1" stop-color="{IVORY_SH}"/>
      </linearGradient>
      <linearGradient id="p-mid" x1=".3" y1="0" x2=".7" y2="1">
        <stop offset="0" stop-color="{IVORY_HI}"/><stop offset=".55" stop-color="#f2eee2"/><stop offset="1" stop-color="#d3ccb9"/>
      </linearGradient>
      <linearGradient id="p-in" x1=".34" y1="0" x2=".66" y2="1">
        <stop offset="0" stop-color="{IVORY_HI}"/><stop offset="1" stop-color="#e9e3d4"/>
      </linearGradient>
      <radialGradient id="p-coeur" cx=".4" cy=".34" r=".72">
        <stop offset="0" stop-color="{GOLD_HI}"/><stop offset=".5" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD_LO}"/>
      </radialGradient>
      <radialGradient id="p-ombre" cx=".5" cy=".5" r=".5">
        <stop offset="0" stop-color="#8a8271" stop-opacity=".5"/><stop offset="1" stop-color="#8a8271" stop-opacity="0"/>
      </radialGradient>
      <!-- feuillage émeraude, nervures éclairées -->
      <linearGradient id="p-leaf" x1=".18" y1="0" x2=".82" y2="1">
        <stop offset="0" stop-color="{LEAF_HI}"/><stop offset=".45" stop-color="{LEAF}"/><stop offset="1" stop-color="{LEAF_LO}"/>
      </linearGradient>
      <linearGradient id="g-gold" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="{GOLD_HI}"/><stop offset=".45" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD_LO}"/>
      </linearGradient>
      <linearGradient id="g-fern" x1=".1" y1="1" x2=".9" y2="0">
        <stop offset="0" stop-color="{FERN_LO}"/><stop offset=".5" stop-color="{FERN}"/><stop offset="1" stop-color="{FERN_HI}"/>
      </linearGradient>
      <radialGradient id="g-perle" cx=".34" cy=".3" r=".78">
        <stop offset="0" stop-color="{PEARL_HI}"/><stop offset=".45" stop-color="{PEARL}"/><stop offset="1" stop-color="{PEARL_LO}"/>
      </radialGradient>
    </defs>"""


def build_perle():
    return f"""    <!-- Perle crème, lumière en haut à gauche -->
    <symbol id="fl-perle" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="url(#g-perle)"/>
      <circle cx="12" cy="12" r="10" fill="none" stroke="#b9b2a1" stroke-width=".7" stroke-opacity=".5"/>
      <ellipse cx="8.6" cy="8.2" rx="3.4" ry="2.6" fill="#ffffff" opacity=".85" transform="rotate(-28 8.6 8.2)"/>
    </symbol>"""


def build_feuille():
    # Nervures secondaires : elles repartent de la nervure centrale à
    # angle droit vers les deux bords du limbe. Le côté gauche du limbe
    # est beaucoup plus près de la nervure que le côté droit, donc
    # chaque nervure est dimensionnée pour s'arrêter au bon bord.
    veins = ""
    for t, ln_g, ln_d in [(0.18, 1.2, 3.4), (0.36, 1.5, 3.6), (0.54, 1.5, 3.3),
                          (0.70, 1.2, 2.6), (0.83, 0.8, 1.8)]:
        bx, by = 17 - 13.4 * t, 30 - 27.5 * t
        for sx, sy, ln, op in ((0.887, -0.462, ln_d, .5), (-0.887, 0.462, ln_g, .42)):
            ex, ey = bx + sx * ln, by + sy * ln
            veins += (f'      <path d="M{n(bx)} {n(by)} Q{n(bx+sx*ln*0.55)} {n(by+sy*ln*0.55-0.4)}'
                      f' {n(ex)} {n(ey)}" fill="none" stroke="#0a2a20"'
                      f' stroke-width=".65" stroke-linecap="round" opacity="{op}"/>\n')
    return f"""    <!-- Feuille émeraude, vernie, nervure centrale marquée.
         Limbe étroit et pointu, comme les feuilles de la carte. -->
    <symbol id="fl-feuille" viewBox="0 0 32 32">
      <path d="M17 30.5 C 11 24 5 13 3 1.5 C 12 5 20.5 12.5 25 22 C 24.5 25.5 21.5 28.5 17 30.5 Z" fill="url(#p-leaf)"/>
      <path d="M17 30.5 C 13.5 21 9 11 4 3 C 11 6 17.5 12.5 22 21 C 21.5 24 19 27 17 30.5 Z" fill="#ffffff" opacity=".07"/>
{veins}      <path d="M17 30 C 13.5 21 9 11 3.6 2.5" fill="none" stroke="#05201a" stroke-width="1.25" opacity=".6" stroke-linecap="round"/>
      <path d="M17 30 C 14 21 9.6 11.5 4.6 3.2" fill="none" stroke="#8fd3b2" stroke-width=".5" opacity=".55" stroke-linecap="round"/>
    </symbol>"""


def build_fougere():
    """Fougère dorée : deux frondes, folioles fines et serrées."""
    body = "\n".join(fronde((3, 45), (13, 25), (33, 3),
                           count=14, l0=13.0, l1=3.4, w_ratio=0.17, spread=40))
    small = "\n".join(fronde((9, 46), (20, 32), (43, 20),
                             count=10, l0=8.0, l1=2.6, w_ratio=0.17, spread=40))
    return f"""    <!-- Fougère dorée (fillette de la carte de référence) -->
    <symbol id="fl-fougere" viewBox="0 0 48 48">
{body}
{small}
    </symbol>"""



def build_rose():
    stamen = ""
    for i in range(8):
        a = math.radians(i * 45 + 12)
        stamen += (f'      <circle cx="{n(32+math.cos(a)*3.9)}" cy="{n(32+math.sin(a)*3.9)}"'
                   f' r="1.15" fill="#a97f24" opacity=".9"/>\n')
    for i in range(4):
        a = math.radians(i * 90 + 45)
        stamen += (f'      <circle cx="{n(32+math.cos(a)*1.7)}" cy="{n(32+math.sin(a)*1.7)}"'
                   f' r="1.05" fill="#8f6a20" opacity=".85"/>\n')
    return f"""    <!-- ===== LE CAMÉLIA — définition unique, réutilisée partout =====
         3 couronnes de pétales larges qui se chevauchent, liseré doux
         entre les pétales, cœur d'étamines dorées. -->
    <symbol id="fl-rose" viewBox="0 0 64 64">
      <ellipse cx="32" cy="33" rx="27" ry="26" fill="url(#p-ombre)" opacity=".55"/>
{chr(10).join(ring_petals(7, 30.0, 13.6, "url(#p-out)", offset=8, stroke_op=.42))}
{chr(10).join(ring_petals(8, 25.0, 12.0, "url(#p-mid)", offset=30, stroke_op=.5))}
      <circle cx="32" cy="32" r="10.5" fill="url(#p-ombre)" opacity=".7"/>
{chr(10).join(ring_petals(6, 17.5, 8.8, "url(#p-in)", offset=12, stroke_op=.45, sw=.5))}
      <circle cx="32" cy="32" r="6.5" fill="url(#p-coeur)"/>
{stamen}      <circle cx="32" cy="32" r="1.5" fill="{GOLD_LO}" opacity=".9"/>
      <circle cx="30.1" cy="30.4" r="1.1" fill="{GOLD_HI}" opacity=".95"/>
    </symbol>"""


def build_simple():
    bouton = f"""    <!-- Bouton fermé, ivoire -->
    <symbol id="fl-bouton" viewBox="0 0 24 32">
      <path d="M12 31 C3 23 1 15 4.5 8.5 C8 2 16 2 19.5 8.5 C23 15 21 23 12 31Z" fill="url(#p-mid)" stroke="{EDGE}" stroke-width=".6" stroke-opacity=".5"/>
      <path d="M12 27 C6.5 20.5 5.5 15 7.5 11 C9.5 7.5 14.5 7.5 16.5 11 C18.5 15 17.5 20.5 12 27Z" fill="url(#p-in)"/>
      <path d="M12 24 C9.5 20.5 9 17 10 14.5" fill="none" stroke="#a9a292" stroke-width=".8" opacity=".6"/>
      <path d="M11 6 C10 9 8 10 6 10.5 C8 12 9 14 9 16" fill="none" stroke="{STEM}" stroke-width="1.3" stroke-linecap="round"/>
    </symbol>"""
    return f"""    <!-- Fleur simple = le camélia -->
    <symbol id="fl-fleur" viewBox="0 0 64 64"><use href="#fl-rose"/></symbol>

    <!-- Camélia double : deux fleurs superposées = plus touffu -->
    <symbol id="fl-fleur2" viewBox="0 0 64 64">
      <use href="#fl-rose" x="0" y="0" width="47" height="47"/>
      <use href="#fl-rose" x="16" y="16" width="44" height="44"/>
    </symbol>

{bouton}"""



def build_ramure():
    """Grand décor de coin, structuré comme la carte de référence :

    - une TOUFFE dense ancrée dans le coin (camélia principal entouré
      d'une couronne serrée de feuilles, fleurs et fougères) ;
    - une QUEUE en diagonale qui s'éloigne du coin et s'amincit
      progressivement vers l'intérieur de la carte.

    Le symbole est mis en miroir par le CSS (`.garland.tr` en
    `scaleX(-1)`, `.garland.bl` en `scaleY(-1)`) : on compose donc
    toujours le même coin haut-gauche.
    """
    touffe, queue = [], []

    # ---- TOUFFE : masse compacte centrée sur le coin -------------------
    CX, CY = 56, 58
    touffe += [
        # fougères dorées : socle de la touffe
        use("fl-fougere", 4, 8, 78, 78, rot=-18),
        use("fl-fougere", 62, -6, 66, 66, rot=12),
        use("fl-fougere", 96, 30, 54, 54, rot=30),
        # camélia principal, cœur de la touffe
        use("fl-fleur", 16, 16, 82, 82),
        # deux fleurs moyennes plaquées contre le principal
        use("fl-fleur2", 74, 4, 54, 54),
        use("fl-fleur", -10, 74, 50, 50),
        use("fl-fleur", 78, 60, 40, 40),
        # petites fleurs serrées : le côté « touffu » de la carte
        use("fl-fleur", 4, 62, 32, 32),
        use("fl-fleur", 48, 62, 30, 30),
        use("fl-fleur", 92, 22, 30, 30),
        use("fl-fleur", 62, 92, 28, 28),
        use("fl-fleur", 6, 100, 30, 30),
        # couronne de feuilles autour du camélia
        use("fl-feuille", 6, 30, 44, 44, rot=52),
        use("fl-feuille", 52, -2, 40, 40, rot=-26),
        use("fl-feuille", 92, 34, 38, 38, rot=28),
        use("fl-feuille", 76, 84, 36, 36, rot=-34),
        use("fl-feuille", 18, 88, 40, 40, rot=36),
        use("fl-feuille", -8, 52, 42, 42, rot=-14),
        use("fl-feuille", 40, 76, 34, 34, rot=20),
        use("fl-feuille", 110, 4, 32, 32, rot=-40),
        use("fl-feuille", 30, 4, 32, 32, rot=8),
        # bourgeons
        use("fl-bouton", 108, 60, 20, 26, rot=-24),
        use("fl-bouton", 58, 108, 20, 26, rot=16),
        use("fl-bouton", 4, 4, 19, 25, rot=30),
        use("fl-bouton", 116, 26, 17, 22, rot=-12),
        # perles incrustées
        use("fl-perle", 106, 52, 13, 13),
        use("fl-perle", 34, 104, 14, 14),
        use("fl-perle", 8, 40, 11, 11),
        use("fl-perle", 88, 92, 10, 10),
        use("fl-perle", 122, 12, 9, 9),
    ]

    # ---- QUEUE : touffe qui s'amincit le long de la diagonale --------
    # Chaque jalon s'écarte de l'axe (dx, dy) et alterne le côté, pour
    # éviter l'alignement en range que donne une position régulière.
    jalons = [
        (0.12, 114, 110, 42,  10,  -6, 0),
        (0.24, 133, 127, 35,  -12,  8, 1),
        (0.36, 149, 141, 29,  11,  -9, 0),
        (0.48, 163, 153, 24,  -9,   6, 1),
        (0.60, 175, 163, 19,   8,  -5, 0),
        (0.72, 184, 171, 15,  -6,   4, 1),
        (0.84, 191, 177, 11,   5,  -3, 0),
        (0.94, 196, 182,  8,  -3,   2, 1),
    ]
    for k, (t_, x, y, s_, dx, dy, cote) in enumerate(jalons):
        c1, c2 = (-1, 1) if cote == 0 else (1, -1)
        # deux feuilles encadrant la tige, de côtés alternés
        queue.append(use("fl-feuille", x + dx * c1, y + dy * c1,
                         s_ * 0.74, s_ * 0.74, rot=-44 + c1 * 26 + k * 4))
        queue.append(use("fl-feuille", x - dx * c2, y - dy * c2,
                         s_ * 0.62, s_ * 0.62, rot=-16 - c2 * 24 - k * 3))
        if k < 4:
            queue.append(use("fl-fougere", x + dx * 0.4, y + dy * 0.4,
                             s_ * 1.00, s_ * 1.00, rot=24 - c1 * 22))
        if k < 5:
            queue.append(use("fl-fleur", x - dx * 0.5, y - dy * 0.5,
                             s_ * 0.62, s_ * 0.62))
        queue.append(use("fl-bouton", x + dx * 1.5, y + dy * 1.5,
                         s_ * 0.30, s_ * 0.38, rot=-26 + c1 * 20))
        if k < 6:
            queue.append(use("fl-perle", x - dx * 1.2, y - dy * 1.2,
                             s_ * 0.24, s_ * 0.24))

    items = touffe + queue
    return f"""    <!-- Ramure fleurie de coin : touffe touffue + queue en diagonale -->
    <symbol id="fl-ramure" viewBox="0 0 200 200">
      <g>
        <path d="M10 12 C52 44 96 92 132 130 C156 156 178 178 198 196"
              fill="none" stroke="{STEM}" stroke-width="2.2" stroke-linecap="round"/>
        <path d="M40 44 C70 70 96 96 118 118" fill="none"
              stroke="{STEM}" stroke-width="1.2" opacity=".6"/>
{chr(10).join(items)}
      </g>
    </symbol>"""


# ————————————————————————————————————————————————————————————
# Plan de pose relevé dans Excalidraw (positions exactes des fleurs)
#
# Le schéma donne un cadre de 1612,93 x 2508,82 et 60 ellipses de
# 160 x 120 (9,9 % de la largeur de carte). Deux bouquets :
#   · A — 27 fleurs, angle 0,       ancré en haut-gauche
#   · B — 33 fleurs, angle 3,157,   ancré en bas-droite (miroir)
# On travaille dans un viewBox de 322 x 502, même ratio que la carte
# (0,643). K convertsit les coordonnées Excalidraw vers ce repère.
# ————————————————————————————————————————————————————————————
_CARD_W, _CARD_H = 1612.926, 2508.817
_K = 322.0 / _CARD_W          # 0.19963
_FW, _FH = 160.0, 120.0       # taille d'une ellipse de pose
_FW_S, _FH_S = _FW * _K, _FH * _K

# (x, y) = coin haut-gauche de l'ellipse, dans le repère Excalidraw.
POSE_A = [
    (10824, 5242), (10944, 5277), (11069, 5278), (11218, 5297), (11307, 5254),
    (10644, 5302), (10786, 5338), (10949, 5386), (11074, 5388), (10649, 5412),
    (11223, 5407), (10791, 5448), (10968, 5455), (10702, 5491), (10879, 5498),
    (10589, 5532), (10815, 5559), (10992, 5566), (10708, 5601), (10884, 5607),
    (10821, 5669), (10997, 5676), (10625, 5710), (10630, 5820), (10716, 5914),
    (10627, 5957), (10632, 6067),
]
POSE_B = [
    (11931, 7522), (11789, 7484), (11988, 6902), (11875, 7333), (11332, 7561),
    (11605, 7367), (11803, 7146), (11630, 7543), (11989, 7294), (11505, 7540),
    (11750, 7579), (11956, 7115), (11763, 7263), (11220, 7491), (11493, 7297),
    (11691, 7076), (11962, 6680), (11927, 7413), (11872, 7223), (11329, 7451),
    (11601, 7258), (11800, 7037), (11627, 7434), (11826, 6851), (11986, 7184),
    (11502, 7430), (11746, 7470), (11945, 6887), (11952, 7005), (11760, 7153),
    (11217, 7381), (11489, 7187), (11688, 6966),
]

# Le bouquet B a ete dessine avec un angle de ~pi : cela oriente les
# fleurs, mais NE les deplace pas — B est deja ancre en bas a droite.
# `turn` ne sert donc qu'a pivoter chaque fleur sur elle-meme.
# Decalages de remplissage (fx, fy en fraction de fleur, rot, taille).
# Le premier dechet est le plus proche de la fleur, le dernier le plus
# etale : c'est ce qui donne l'effet de masse, de touffe.
OFFSETS = [
    (0.42, -0.22, 88, 0.60),
    (-0.40, 0.30, 104, 0.55),
    (0.20, 0.46, 66, 0.50),
    (-0.18, -0.40, 116, 0.46),
    (0.58, 0.14, 78, 0.40),
]


def _pose(pts, turn=False):
    """Convertit une liste de poses Excalidraw en elements SVG.
    Retourne (feuillage, fleurs) : le feuillage est_trace en premier
    pour rester derriere, et comble les interstices du semis."""
    fleurs, feuil = [], []
    for i, (ex, ey) in enumerate(pts):
        x = (ex - 10570.483) * _K
        y = (ey - 5216.146) * _K
        # 1 fleur sur 5 est un bouton : casse la regularite du semis
        ref = "fl-bouton" if i % 5 == 4 else ("fl-fleur2" if i % 7 == 3 else "fl-fleur")
        fleurs.append(use(ref, x, y, _FW_S, _FH_S,
                          rot=(180 if turn and i % 3 else None)))
        # Feuillage derriere, vers l'interieur du bouquet. Quatre passes
        # de remplissage : les fleurs seules laissent trop de vide, la
        # carte de reference est un semis touffu.
        for j, (fx, fy, fr, fs) in enumerate(OFFSETS):
            d = _FW_S * fs
            if i % (j + 2) == 0:
                feuil.append(use("fl-feuille", x + _FW_S * fx, y + _FH_S * fy,
                                 d, d, rot=fr * (1 if turn else -1) + (i % 5) * 11))
        if i % 2 == 1:
            d = _FW_S * 0.70
            feuil.append(use("fl-fougere", x - d * 0.45, y + d * 0.25,
                             d, d, rot=(-28 if turn else 28) + (i % 2) * 18))
        if i % 3 == 0:
            d = _FW_S * 0.52
            feuil.append(use("fl-fougere", x + d * 0.30, y - d * 0.55,
                             d, d, rot=(52 if turn else -52) + (i % 3) * 16))
        if i % 2 == 0:
            feuil.append(use("fl-bouton", x - _FW_S * 0.42, y + _FH_S * 0.46,
                             _FW_S * 0.30, _FH_S * 0.40,
                             rot=(-24 if turn else 24) + (i % 4) * 15))
        if i % 3 == 1:
            feuil.append(use("fl-perle", x + _FW_S * 0.30, y + _FH_S * 0.34,
                             _FW_S * 0.13, _FW_S * 0.13))
    return feuil, fleurs


def build_plan():
    """Grand decor de carte : la pose suit point par point le schema
    Excalidraw (bouquet A en haut-gauche, bouquet B en bas-droite)."""
    feuil_a, fleurs_a = _pose(POSE_A)
    feuil_b, fleurs_b = _pose(POSE_B, turn=True)
    return f"""    <!-- Pose de carte relevee dans Excalidraw : 2 bouquets sur la diagonale -->
    <symbol id="fl-plan" viewBox="0 0 322 502">
      <g>
{chr(10).join(feuil_a + feuil_b + fleurs_a + fleurs_b)}
      </g>
    </symbol>"""


def build_medaillon():
    """Grand medaillon ovale du faire-part : double filet dore, couronne
    de feuillage et de perles, vide au centre pour laisser passer le
    texte en HTML par-dessus. viewBox 240 x 320 (ratio du carre)."""
    cx, cy, rx, ry = 120.0, 160.0, 104.0, 140.0
    L = []
    # couronne : feuillage pose le long de l'ovale, deux passes
    for i in range(26):
        a = math.radians(-90 + i * (360.0 / 26))
        px = cx + rx * math.cos(a) * 0.985
        py = cy + ry * math.sin(a) * 0.985
        s = 15.0 + 5.0 * math.sin(i * 1.7)
        L.append(use("fl-feuille", px - s / 2, py - s / 2, s, s,
                     rot=math.degrees(a) + 90 + (14 if i % 2 else -14)))
    for i in range(20):
        a = math.radians(-84 + i * (348.0 / 19))
        px = cx + rx * math.cos(a) * 0.88
        py = cy + ry * math.sin(a) * 0.88
        s = 9.0 + 3.0 * math.sin(i * 2.3)
        L.append(use("fl-fougere", px - s / 2, py - s / 2, s, s,
                     rot=math.degrees(a) - 90 + (i % 2) * 22))
    # perles espacees regulierement, plus denses en haut et en bas
    for i in range(16):
        a = math.radians(i * 22.5)
        px = cx + rx * 0.93 * math.cos(a)
        py = cy + ry * 0.95 * math.sin(a)
        r = 4.2 if i % 4 else 5.4
        L.append(use("fl-perle", px - r, py - r, r * 2, r * 2))
    # double filet dore + filet interieur tres fin
    L.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" '
             f'fill="none" stroke="url(#g-gold)" stroke-width="2.4"/>')
    L.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx - 7)}" ry="{n(ry - 7)}" '
             f'fill="none" stroke="#cda75a" stroke-width="0.9" opacity=".8"/>')
    L.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx - 12)}" ry="{n(ry - 12)}" '
             f'fill="none" stroke="url(#g-gold)" stroke-width="0.7" opacity=".55"/>')
    # losanges dore aux quatre points cardinaux
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        px = cx + rx * math.cos(r)
        py = cy + ry * math.sin(r)
        L.append(f'<path d="M{n(px)} {n(py - 7)} L{n(px + 7)} {n(py)} '
                 f'L{n(px)} {n(py + 7)} L{n(px - 7)} {n(py)} Z" '
                 f'fill="url(#g-gold)" opacity=".92"/>')
    return (
        "    <!-- Medaillon ovale du faire-part : cadre vide pour le texte -->\n"
        '    <symbol id="fl-medaille" viewBox="0 0 240 320">\n'
        "      <g>\n" + "\n".join(L) + "\n      </g>\n"
        "    </symbol>"
    )



def build_couronne():
    items = [
        use("fl-feuille", 8, 34, 30, 30, rot=-30),
        use("fl-feuille", 40, 16, 28, 28, rot=18),
        use("fl-feuille", 172, 16, 28, 28, rot=-18),
        use("fl-feuille", 204, 34, 30, 30, rot=30),
        use("fl-fougere", 62, -2, 42, 42, rot=14),
        use("fl-fougere", 140, -2, 42, 42, rot=-14),
        use("fl-fleur", 24, 12, 32, 32),
        use("fl-fleur", 64, -2, 28, 28),
        use("fl-fleur", 148, -2, 28, 28),
        use("fl-fleur", 186, 12, 32, 32),
        use("fl-fleur2", 100, -14, 34, 34),
        use("fl-bouton", 88, 12, 17, 22, rot=-14),
        use("fl-bouton", 130, 12, 17, 22, rot=14),
        use("fl-perle", 120, 30, 9, 9),
    ]
    return f"""    <!-- Couronne de fleurs -->
    <symbol id="fl-couronne" viewBox="0 0 240 70">
      <g>
        <path d="M6 62 C40 22 80 6 120 6 C160 6 200 22 234 62" fill="none" stroke="{STEM}" stroke-width="1.6"/>
{chr(10).join(items)}
      </g>
    </symbol>"""



def build_bouquet():
    items = [
        use("fl-fougere", 0, 20, 62, 62, rot=-14),
        use("fl-fougere", 60, 12, 58, 58, rot=16),
        use("fl-feuille", 0, 14, 36, 36, rot=-32),
        use("fl-feuille", 86, 16, 36, 36, rot=30),
        use("fl-feuille", 42, 80, 36, 36, rot=8),
        use("fl-fleur", 20, 16, 52, 52),
        use("fl-fleur", 52, 46, 50, 50),
        use("fl-fleur", 0, 46, 36, 36),
        use("fl-fleur", 78, 38, 34, 34),
        use("fl-bouton", 18, 72, 19, 25, rot=-18),
        use("fl-bouton", 84, 72, 17, 23, rot=20),
        use("fl-perle", 46, 8, 14, 14),
        use("fl-perle", 88, 26, 10, 10),
        use("fl-perle", 8, 88, 11, 11),
    ]
    return f"""    <!-- Bouquet dense -->
    <symbol id="fl-bouquet" viewBox="0 0 120 120">
{chr(10).join(items)}
    </symbol>"""


def build_fete():
    items = [
        use("fl-feuille", 12, 42, 30, 30, rot=-30),
        use("fl-feuille", 50, 20, 28, 28, rot=20),
        use("fl-feuille", 204, 20, 28, 28, rot=-20),
        use("fl-feuille", 242, 42, 30, 30, rot=30),
        use("fl-fougere", 66, -6, 46, 46, rot=16),
        use("fl-fougere", 170, -6, 46, 46, rot=-16),
        use("fl-fleur", 30, 12, 34, 34),
        use("fl-fleur", 72, -2, 30, 30),
        use("fl-fleur", 178, -2, 30, 30),
        use("fl-fleur", 218, 12, 34, 34),
        use("fl-fleur2", 104, -16, 36, 36),
        use("fl-fleur2", 142, -16, 36, 36),
        use("fl-bouton", 58, 32, 17, 22, rot=-16),
        use("fl-bouton", 200, 32, 17, 22, rot=16),
        use("fl-perle", 140, 26, 10, 10),
        use("fl-perle", 96, 30, 8, 8),
        use("fl-perle", 180, 30, 8, 8),
    ]
    return f"""    <!-- Guirlande de fête -->
    <symbol id="fl-fete" viewBox="0 0 280 80">
      <g>
        <path d="M4 70 C48 22 96 4 140 4 C184 4 232 22 276 70" fill="none" stroke="{STEM}" stroke-width="1.6"/>
{chr(10).join(items)}
        <circle cx="140" cy="-12" r="5" fill="url(#g-gold)"/>
      </g>
    </symbol>"""


def build_alliance():
    items = [
        use("fl-feuille", 0, 44, 44, 44, rot=-28),
        use("fl-feuille", 116, 40, 44, 44, rot=28),
        use("fl-feuille", 24, 82, 36, 36, rot=14),
        use("fl-feuille", 100, 80, 36, 36, rot=-14),
        use("fl-fougere", 2, 78, 46, 46, rot=-12),
        use("fl-fougere", 112, 74, 46, 46, rot=12),
        use("fl-fleur", 6, -2, 40, 40),
        use("fl-fleur", 114, -2, 40, 40),
        use("fl-fleur2", 44, -10, 36, 36),
        use("fl-bouton", 80, 2, 19, 25, rot=8),
        use("fl-fleur", 30, 72, 36, 36),
        use("fl-fleur", 94, 72, 36, 36),
        use("fl-bouton", 66, 84, 16, 21, rot=-10),
        use("fl-bouton", 82, 84, 16, 21, rot=10),
        use("fl-perle", 52, 62, 12, 12),
        use("fl-perle", 96, 62, 10, 10),
        use("fl-perle", 20, 30, 9, 9),
        use("fl-perle", 132, 28, 9, 9),
    ]
    return f"""    <!-- ALLIANCES NICHÉES DANS LE FLEURAGE (composition de la carte) -->
    <symbol id="fl-alliance" viewBox="0 0 160 120">
      <g>
{chr(10).join(items)}
        <g class="shine">
          <ellipse cx="66" cy="54" rx="20" ry="23" fill="none" stroke="url(#g-gold)" stroke-width="5.5"/>
          <ellipse cx="94" cy="54" rx="20" ry="23" fill="none" stroke="url(#g-gold)" stroke-width="5.5"/>
          <ellipse cx="66" cy="54" rx="20" ry="23" fill="none" stroke="#fbf1d0" stroke-width="1.2" opacity=".9"/>
          <ellipse cx="94" cy="54" rx="20" ry="23" fill="none" stroke="#fbf1d0" stroke-width="1.2" opacity=".9"/>
        </g>
        <path d="M80 26 C77 21 78.5 17 81 15.5 C82.8 19 83.4 22.4 82 26Z" fill="#fdf6e4" stroke="url(#g-gold)" stroke-width="1"/>
      </g>
    </symbol>"""



def build_filet():
    return f"""    <!-- Filet fleuri (séparateur de titre) -->
    <symbol id="fl-filet" viewBox="0 0 200 28">
      <g>
        <path d="M0 14 H70 M130 14 H200" stroke="url(#g-gold)" stroke-width="1" opacity=".75"/>
        <circle cx="78" cy="14" r="1.8" fill="url(#g-gold)"/>
        <circle cx="122" cy="14" r="1.8" fill="url(#g-gold)"/>
        <use href="#fl-fleur" x="89" y="3" width="22" height="22"/>
        <circle cx="76" cy="6" r="1.2" fill="url(#g-perle)"/>
        <circle cx="124" cy="21" r="1.2" fill="url(#g-perle)"/>
      </g>
    </symbol>"""


def build_anneaux():
    return f"""    <!-- Deux anneaux entrelacés (nus) -->
    <symbol id="fl-anneaux" viewBox="0 0 120 84">
      <g class="shine">
        <ellipse cx="46" cy="52" rx="26" ry="30" fill="none" stroke="url(#g-gold)" stroke-width="5"/>
        <ellipse cx="74" cy="52" rx="26" ry="30" fill="none" stroke="url(#g-gold)" stroke-width="5"/>
        <ellipse cx="46" cy="52" rx="26" ry="30" fill="none" stroke="#f6e7c2" stroke-width="1.1" opacity=".85"/>
        <ellipse cx="74" cy="52" rx="26" ry="30" fill="none" stroke="#f6e7c2" stroke-width="1.1" opacity=".85"/>
      </g>
      <path d="M60 14 C56 8 58 3 62 1 C64 5 65 9 63 13Z" fill="#fdf6e4" stroke="url(#g-gold)" stroke-width="1"/>
    </symbol>"""


# ————————————————————————————————————————————————————————————
# Assemblage & injection
# ————————————————————————————————————————————————————————————
HEAD = "  <!-- ===== SPRITE FLORAL"
PAGES = ("index.html", "invitation-landing.html", "carte.html")

HEADER = """  <!-- ===== SPRITE FLORAL — CAMÉLIAS IVOIRE (carte de référence) =====
       Camélias à 3 couronnes de pétales larges, cœur d'étamines dorées,
       feuilles émeraude vernies, fougères dorées, perles crème.
       Ce bloc est dupliqué à l'identique dans les 2 pages : il est
       régénéré par tools/floral-sprite.py — ne pas éditer à la main. -->
  <svg class="sprite" aria-hidden="true" focusable="false">"""


def sprite_block():
    parts = [
        HEADER,
        build_defs(),
        build_perle(),
        build_feuille(),
        build_fougere(),
        build_rose(),
        build_simple(),
        build_ramure(),
        build_couronne(),
        build_plan(),
        build_medaillon(),
        build_filet(),
        build_bouquet(),
        build_fete(),
        build_alliance(),
        build_anneaux(),
    ]
    return "\n\n".join(parts) + "\n  </svg>"


def splice(path, block):
    lines = path.read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith(HEAD))
    end = next(i for i, l in enumerate(lines[start:], start) if l.strip() == "</svg>")
    out = lines[:start] + block.split("\n") + lines[end + 1:]
    path.write_text("\n".join(out), encoding="utf-8")
    return end - start + 1


def main():
    block = sprite_block()
    if "--print" in sys.argv:
        print(block)
        return
    root = pathlib.Path(__file__).resolve().parent.parent
    for name in PAGES:
        replaced = splice(root / name, block)
        print(f"{name} : bloc floral régénéré ({replaced} lignes remplacées)")


if __name__ == "__main__":
    main()


