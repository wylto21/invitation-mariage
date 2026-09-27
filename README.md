# Invitation — Daria & Hermann

Site statique (HTML/CSS/JS vanilla, sans dépendance ni build).
Mariage : vendredi 18 décembre 2026, 16h00 — Table des Élites, Akwa, Douala.

## Fichiers
| Fichier | Rôle |
|---|---|
| `index.html` | Page d'intro : enveloppe fleurie (alliances au centre) → photo → RSVP |
| `invitation-landing.html` | Page principale : hero, compte à rebours, réservations, espace organisateurs |
| `styles.css` | Socle commun : palette, reset, utilitaires, décors floraux, accessibilité |
| `favicon.svg` | Icône du site |
| `photo-couple.jpg` | Photo de couverture (partagée par les balises OG) |

## Direction artistique — « Nuit Douala »
Une soirée, pas un après-midi. Le fond est une nuit profonde (oxblood → indigo),
**l'or est traité comme une source de lumière** et les fleurs sont des **silhouettes**
découpées dans la pénombre — pas des illustrations. Aucun crème, aucun script cursif :
la typographie est Cormorant Garamond (élégant, contemporaine) + Cinzel (capitales) + Jost.

| Rôle | Couleur |
|---|---|
| Fond absolu | `#14090d` |
| Oxblood / vin | `#4a0f1c` · `#6b1226` |
| Indigo (contre-jour) | `#1a1030` |
| Or (lumière) | `#d9a441` · éclat `#f4d894` |
| Pétales (visibles) | `#e8b18d` → `#c9663f` → `#a84a24` (tous > 3:1 sur le fond) |
| Feuillage | `#7d9a66` · `#4a6b45` |
| Texte | ivoire `#f7ece4`, secondaire `#e8cfc0` |

## Décors floraux
Un **sprite SVG** (`#fl-fleur`, `#fl-fleur2`, `#fl-bouton`, `#fl-feuille`, `#fl-ramure`,
`#fl-couronne`, `#fl-filet`, `#fl-bouquet`, `#fl-fete`, `#fl-anneaux`) est inliné en haut de chaque page et réemployé
via `<use href="#fl-…">`. Le sprite est dupliqué dans les deux fichiers : c'est volontaire
(le `<use>` externe ne fonctionne pas en `file://`). **Toute évolution du sprite doit être
reportée dans les deux pages.**

## Configuration
Tout se règle dans le bloc `CONFIG` en haut du script de `invitation-landing.html` :
date du mariage, capacités par catégorie, PIN admin, URL de backend éventuelle.

**Capacité : 50 invites au total.** Le détail par catégorie (20 / 20 / 10) est une donnée
interne qui sert uniquement à alimenter les barres de progression : **aucun chiffre de
répartition n'est affiché publiquement**, par choix éditorial. Pour modifier le total,
changez les valeurs `stock` de `CONFIG.categories` — le total affiché est calculé
automatiquement.

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
