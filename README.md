# Invitation — Daria & Hermann

Site statique (HTML/CSS/JS vanilla, sans dépendance ni build).
Mariage : vendredi 18 décembre 2026, 16h00 — Table des Élites, Akwa, Douala.

## Fichiers
| Fichier | Rôle |
|---|---|
| `index.html` | Page d'intro : enveloppe fleurie → photo → redirection vers le RSVP |
| `invitation-landing.html` | Page principale : hero, compte à rebours, réservations, espace organisateurs |
| `styles.css` | Socle commun : palette, reset, utilitaires, accessibilité |
| `favicon.svg` | Icône du site |
| `photo-couple.jpg` | Photo de couverture (partagée par les balises OG) |

## Configuration
Tout se règle dans le bloc `CONFIG` en haut du script de `invitation-landing.html` :
date du mariage, capacités par catégorie, PIN admin, URL de backend éventuelle.

## Lancer en local
```bash
python3 -m http.server 8000
# puis http://localhost:8000
```

## Accès organisateurs
5 clics sur le logo « H » (ou URL `invitation-landing.html#admin`), puis le PIN.

## État actuel
Les réservations sont stockées dans le `localStorage` du navigateur : les compteurs
ne sont donc **pas synchronisés entre les invités**. Un backend est prévu (champ
`CONFIG.backendUrl`) mais pas encore branché.
