#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relever les identifiants d'un Google Form (formId + entry.* ).

Usage :
    python3 tools/google-form-ids.py 'https://docs.google.com/forms/d/e/FORM_ID/edit'

Affiche un bloc de configuration a coller dans CONFIG.google de
invitation-landing.html. Les identifiants entry.* sont tries dans l'ordre
d'apparition des questions, avec le libelle de chaque question.
"""
import html
import json
import re
import sys
import urllib.request

FORM_RE = re.compile(r"/forms/d/(?:e/)?([A-Za-z0-9_-]{10,})")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def form_id(url):
    m = FORM_RE.search(url)
    if not m:
        sys.exit("Impossible de trouver le formId dans l'URL : " + url)
    return m.group(1)


def questions(page):
    """Retourne [(entry_id, libelle), ...] dans l'ordre du formulaire."""
    # Librairie de questions : chaque bloc porte un id de question et un titre.
    out = []
    for m in re.finditer(
        r'\[\"([^"]+)\",\[\[\"([^"]*)\"\],\"([^\"]*)\"\]\]', page
    ):
        entry, _kind, title = m.group(1), m.group(2), m.group(3)
        label = html.unescape(re.sub(r"<[^>]+>", " ", title)).strip()
        out.append((entry, label))
    if not out:
        # Repli : on liste tous les entry.* avec leur position.
        for i, m in enumerate(re.finditer(r"entry\.(\d+)", page)):
            out.append((m.group(1), "(question %d)" % (i + 1)))
    return out


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else input("URL du formulaire : ").strip()
    fid = form_id(url)
    page = fetch(url)
    qs = questions(page)

    print("# Google Form releve :", fid)
    print("formId: '%s'," % fid)
    print("entries: {")
    for entry, label in qs:
        print("  '%s': '',  /* %s */" % (entry, label[:60]))
    print("},")
    print()
    print(" Correspondance a verifier dans CONFIG.google :")
    mapping = {"name": "Nom", "phone": "Telephone", "cat": "Categorie",
               "places": "Places", "code": "Code"}
    for entry, label in qs:
        guess = next((k for k, v in mapping.items() if v.lower() in label.lower()), "?")
        print("  %-8s <- entry.%s  (%s)" % (guess, entry, label[:50]))
    print()
    print(json.dumps({"formId": fid, "entries": [e for e, _ in qs]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
