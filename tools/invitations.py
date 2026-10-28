#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générer les invitations personnelles (un lien ?i=CODE par invité).

Usage :
    python3 tools/invitations.py [invites/invites.csv]

Entrée — invites/invites.csv, une ligne par invité :
    Nom;Catégorie
    Jean Mbarga;Famille
    Awa Ndiaye;Amis

Sorties (dossier invites/, PRIVÉ, ignoré par git) :
    codes.csv   la mémoire des codes : un invité garde son code d'une
                exécution à l'autre, il ne faut pas le supprimer
    liens.csv   nom, catégorie, code, lien, message WhatsApp
    liens.html  page à ouvrir sur le téléphone : un bouton WhatsApp par invité

Et met à jour le bloc INVITES de invitation-landing.html, qui ne contient
que des empreintes SHA-256 des codes (ni noms ni codes en clair).
"""
import csv
import hashlib
import html
import re
import secrets
import sys
import unicodedata
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "invites"
PAGE = ROOT / "invitation-landing.html"
BASE_URL = "https://wylto21.github.io/invitation-mariage/"
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sans 0/O, 1/I/L
CATS = {"famille": "famille", "amis": "amis", "ami": "amis",
        "collegues": "collegues", "collegue": "collegues"}
LABELS = {"famille": "Famille", "amis": "Amis", "collegues": "Collègues"}


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip().lower()


def read_rows(path):
    text = path.read_text(encoding="utf-8-sig")
    delim = ";" if text.count(";") >= text.count(",") else ","
    rows = list(csv.reader(text.splitlines(), delimiter=delim))
    if rows and norm(rows[0][0]) in ("nom", "name", "invite"):
        rows = rows[1:]
    return [[c.strip() for c in r] for r in rows if r and r[0].strip()]


def new_code(taken):
    while True:
        c = "".join(secrets.choice(ALPHABET) for _ in range(8))
        if c not in taken:
            return c


def fingerprint(code):
    return hashlib.sha256(("dh-invite|" + code).encode()).hexdigest()[:16]


def message(name, code):
    link = BASE_URL + "?i=" + code
    return (f"Bonjour {name}, Daria & Hermann ont la joie de vous inviter à leur mariage "
            f"le vendredi 18 décembre 2026 à Douala. Voici votre invitation personnelle "
            f"(merci de ne pas la transférer, elle ne sert qu'une fois) : {link}")


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DIR / "invites.csv"
    if not src.exists():
        sys.exit(f"Fichier introuvable : {src}\nCréez-le avec une ligne « Nom;Catégorie » par invité.")
    DIR.mkdir(exist_ok=True)

    known = {}
    codes_file = DIR / "codes.csv"
    if codes_file.exists():
        for r in read_rows(codes_file):
            if len(r) >= 3:
                known[norm(r[0])] = r[2]

    out, taken, errors, seen = [], set(known.values()), [], set()
    for i, r in enumerate(read_rows(src), 1):
        name = r[0]
        cat = CATS.get(norm(r[1]) if len(r) > 1 else "")
        if not cat:
            errors.append(f"ligne {i} « {name} » : catégorie inconnue ({r[1] if len(r) > 1 else 'vide'})")
            continue
        key = norm(name)
        if key in seen:
            errors.append(f"ligne {i} « {name} » : nom en double (ajoutez un détail pour les distinguer)")
            continue
        seen.add(key)
        code = known.get(key) or new_code(taken)
        taken.add(code)
        out.append((name, cat, code))
    if errors:
        sys.exit("À corriger dans la liste :\n  " + "\n  ".join(errors))

    with codes_file.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Nom", "Catégorie", "Code"])
        for name, cat, code in out:
            w.writerow([name, LABELS[cat], code])

    with (DIR / "liens.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Nom", "Catégorie", "Code", "Lien", "Message WhatsApp"])
        for name, cat, code in out:
            w.writerow([name, LABELS[cat], code, BASE_URL + "?i=" + code, message(name, code)])

    rows = "\n".join(
        f'<tr><td>{html.escape(n)}<small>{LABELS[c]} · {k[:4]}-{k[4:]}</small></td>'
        f'<td><a class="wa" target="_blank" rel="noopener" '
        f'href="https://wa.me/?text={urllib.parse.quote(message(n, k))}">WhatsApp</a></td></tr>'
        for n, c, k in out)
    (DIR / "liens.html").write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Invitations — Daria & Hermann</title>
<style>body{{font-family:system-ui,sans-serif;margin:0 auto;max-width:640px;padding:16px;background:#fdfaf6;color:#4a2416}}
h1{{font-size:20px}}table{{width:100%;border-collapse:collapse}}td{{padding:10px 6px;border-bottom:1px solid #ecdccb}}
small{{display:block;color:#8a6a58;font-size:12px;margin-top:2px}}td:last-child{{text-align:right}}
.wa{{background:#1f9d55;color:#fff;text-decoration:none;padding:9px 14px;border-radius:99px;font-size:14px}}
.wa:visited{{background:#9bb8a5}}</style></head><body>
<h1>Invitations personnelles ({len(out)})</h1>
<p>Touchez « WhatsApp », choisissez l'invité dans vos contacts, puis envoyez. Le bouton pâlit une fois utilisé.</p>
<table>{rows}</table></body></html>""", encoding="utf-8")

    hashes = ", ".join(f"'{fingerprint(k)}': '{c}'" for _, c, k in out)
    page = PAGE.read_text(encoding="utf-8")
    block = re.compile(r"(/\* INVITES:DEBUT \*/\n)(.*?)(\n\s*/\* INVITES:FIN \*/)", re.S)
    if not block.search(page):
        sys.exit("Bloc INVITES introuvable dans invitation-landing.html")
    page = block.sub(lambda m: m.group(1) + "    hashes: {" + hashes + "}" + m.group(3), page)
    PAGE.write_text(page, encoding="utf-8")

    per = {c: sum(1 for _, cc, _ in out if cc == c) for c in LABELS}
    print(f"{len(out)} invitations — " + ", ".join(f"{LABELS[c]} {n}" for c, n in per.items()))
    print(f"Liens : {DIR / 'liens.html'}  (et liens.csv)")


if __name__ == "__main__":
    main()
