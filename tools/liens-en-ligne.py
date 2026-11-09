#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mettre en ligne la page d'envoi des invitations, protégée par mot de passe.

Usage (après tools/invitations.py) :
    python3 tools/liens-en-ligne.py

Écrit envoi.html à la racine du site : la liste des invités et leurs liens y
sont CHIFFRÉS (AES-GCM, clé dérivée du mot de passe par PBKDF2). Le dépôt
public ne contient donc que du texte illisible ; la page se déchiffre dans le
navigateur une fois le mot de passe saisi.

Le mot de passe est créé au premier lancement dans invites/mot-de-passe.txt
(dossier privé) et réutilisé ensuite.
"""
import base64
import html
import json
import os
import secrets
import sys
import urllib.parse
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from invitations import ALPHABET, DIR, LABELS, ROOT, message, read_rows  # noqa: E402

OUT = ROOT / "envoi.html"
ITER = 200_000


def password():
    f = DIR / "mot-de-passe.txt"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    pw = "DH-" + "".join(secrets.choice(ALPHABET) for _ in range(4)) + "-" + \
         "".join(secrets.choice(ALPHABET) for _ in range(4))
    f.write_text(pw + "\n", encoding="utf-8")
    return pw


def main():
    codes = DIR / "codes.csv"
    if not codes.exists():
        sys.exit("Lancez d'abord tools/invitations.py")
    guests = [r for r in read_rows(codes) if len(r) >= 3]
    rows = "".join(
        f'<li><span>{html.escape(n)}<small>{html.escape(c)} · {k[:4]}-{k[4:]}</small></span>'
        f'<a class="wa" target="_blank" rel="noopener" '
        f'href="https://wa.me/?text={urllib.parse.quote(message(n, k))}">WhatsApp</a></li>'
        for n, c, k in guests)

    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER, default_backend()).derive(password().encode())
    blob = AESGCM(key).encrypt(iv, rows.encode("utf-8"), None)
    data = json.dumps({k: base64.b64encode(v).decode() for k, v in
                       {"salt": salt, "iv": iv, "data": blob}.items()})

    OUT.write_text(f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Envoi des invitations — Daria &amp; Hermann</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0 auto;max-width:640px;padding:20px 16px;background:#fdfaf6;color:#4a2416}}
h1{{font-size:21px;margin:0 0 6px}}p{{line-height:1.5}}
form{{display:flex;gap:8px;margin:18px 0}}input{{flex:1;font:inherit;padding:11px 12px;border:1px solid #d9c3ad;border-radius:10px}}
button{{font:inherit;padding:11px 16px;border:0;border-radius:10px;background:#b85c38;color:#fff}}
.err{{color:#a3431f}}ul{{list-style:none;padding:0;margin:0}}
li{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 4px;border-bottom:1px solid #ecdccb}}
small{{display:block;color:#8a6a58;font-size:12px;margin-top:2px}}
.wa{{flex:none;background:#1f9d55;color:#fff;text-decoration:none;padding:9px 14px;border-radius:99px;font-size:14px}}
.wa:visited,.wa.done{{background:#9bb8a5}}
</style>
</head>
<body>
<h1>Envoi des invitations</h1>
<div id="lock">
  <p>Page réservée aux mariés. Saisissez le mot de passe.</p>
  <form id="f"><input id="pw" type="password" autocomplete="current-password" placeholder="Mot de passe" required><button>Ouvrir</button></form>
  <p class="err" id="err" hidden>Mot de passe incorrect.</p>
</div>
<div id="list" hidden>
  <p>Touchez « WhatsApp », choisissez l’invité dans vos contacts, puis envoyez.
  Le bouton pâlit une fois utilisé. Un lien = une personne : ne pas transférer.</p>
  <ul id="ul"></ul>
</div>
<script>
const P = {data};
const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const DONE = 'envoi-faits';
async function open_(pw) {{
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey({{ name: 'PBKDF2', salt: b64(P.salt), iterations: {ITER}, hash: 'SHA-256' }},
    base, {{ name: 'AES-GCM', length: 256 }}, false, ['decrypt']);
  const txt = new TextDecoder().decode(await crypto.subtle.decrypt({{ name: 'AES-GCM', iv: b64(P.iv) }}, key, b64(P.data)));
  document.getElementById('ul').innerHTML = txt;
  document.getElementById('lock').hidden = true;
  document.getElementById('list').hidden = false;
  let done = [];
  try {{ done = JSON.parse(localStorage.getItem(DONE) || '[]'); }} catch (e) {{}}
  document.querySelectorAll('.wa').forEach((a, i) => {{
    if (done.includes(i)) a.classList.add('done');
    a.addEventListener('click', () => {{
      a.classList.add('done');
      if (!done.includes(i)) done.push(i);
      try {{ localStorage.setItem(DONE, JSON.stringify(done)); }} catch (e) {{}}
    }});
  }});
}}
document.getElementById('f').addEventListener('submit', async e => {{
  e.preventDefault();
  try {{ await open_(document.getElementById('pw').value.trim()); }}
  catch (err) {{ document.getElementById('err').hidden = false; }}
}});
</script>
</body>
</html>
""", encoding="utf-8")
    print(f"{len(guests)} invités chiffrés dans {OUT.name}")
    print(f"Mot de passe : voir {DIR / 'mot-de-passe.txt'}")


if __name__ == "__main__":
    main()
