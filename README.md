# Invitation — Daria & Hermann

Site statique (HTML/CSS/JS vanilla, sans dépendance ni build).
Mariage : vendredi 18 décembre 2026 — mairie à 15h00, puis Table des Élites (Akwa, Douala) de 16h00 à 23h00.

## Fichiers
| Fichier | Rôle |
|---|---|
| `index.html` | Page d'intro : « Invitation au mariage de », enveloppe fleurie DH → photo → RSVP |
| `invitation-landing.html` | Page principale : couverture, compte à rebours, programme, places, réservation, espace photo (filtre des mariés), espace cadeaux, espace organisateurs |
| `styles.css` | Socle commun : palette, reset, utilitaires, accessibilité |
| `assets/invitation/` | Décor repris du modèle : fond fleuri, enveloppe, filet, bouquet d'angle |
| `favicon.svg` | Icône du site |
| `photo-couple.jpg` | Photo de couverture (partagée par les balises OG) |

## Direction artistique — « Terracotta »
Mise en page inspirée d'un modèle de faire-part (« Invitation au mariage de ») :
papier ivoire, bouquets photographiques, filets fins, prénoms en calligraphie.
Les fleurs du modèle (fuchsia et rose à l'origine) ont été virées vers la gamme
terracotta ; crèmes, ors et feuillages sont inchangés. Le monogramme « GA » de
l'enveloppe a été effacé et remplacé par « DH » en HTML (`.env-mono`).

Typographie : **Great Vibes** (prénoms, titres de section), **Cinzel** (capitales,
chiffres), **Cormorant Garamond** (textes en italique), **Jost** (interface).

| Rôle | Couleur |
|---|---|
| Fond ivoire | `#fdfaf6` → `#f4e9dd` |
| Terracotta | `#b85c38` · foncé `#8a3416` · clair `#c97b4e` |
| Or | `#c9a55e` · profond `#a8761f` |
| Texte | brun `#4a2416` |

Dress code annoncé : **Terracotta**.

## Sprite SVG
Un petit **sprite SVG** (`#fl-anneaux`, `#fl-feuille`, …) est inliné en haut de chaque page
et réemployé via `<use href="#fl-…">`. Il est dupliqué dans les deux fichiers : c'est
volontaire (le `<use>` externe ne fonctionne pas en `file://`). Il est régénéré par
`tools/floral-sprite.py`.

## Configuration
Tout se règle dans le bloc `CONFIG` en haut du script de `invitation-landing.html` :
date du mariage, capacités par catégorie, PIN admin, URL de backend éventuelle.

**Capacité : 60 invités au total.** Le détail par catégorie (24 / 24 / 12) est une donnée
interne qui sert uniquement à alimenter les barres de progression : **aucun chiffre de
répartition n'est affiché publiquement**, par choix éditorial. Pour modifier le total,
changez les valeurs `stock` de `CONFIG.categories` — le total affiché est calculé
automatiquement.

## Lancer en local
```bash
python3 -m http.server 8000
# puis http://localhost:8000
```

## Stockage des réservations — Google Form + Google Sheets

Les réservations sont envoyées à un **Google Form** (donc visibles dans Google
Sheets), et lues en retour depuis la **feuille Sheets liée au formulaire**. Aucun
serveur, aucune clé API, aucun build.

### 1. Créer le formulaire

Google Forms → *Nouveau*. Questions à créer, dans cet ordre :

| # | Question | Type | Nom de colonne attendu |
|---|---|---|---|
| 1 | Nom & prénom(s) | Réponse courte | `Nom` |
| 2 | Téléphone (WhatsApp) | Réponse courte | `Téléphone` |
| 3 | Catégorie | Liste déroulante : `Famille`, `Amis`, `Collègues` | `Catégorie` |
| 4 | Nombre de places | Liste déroulante : `1`…`10` | `Places` |
| 5 | Code de réservation | Réponse courte | `Code` |

> Les colonnes sont reconnues **par leur en-tête** (insensible à la casse et aux
> accents) : `Nom`, `Téléphone`, `Catégorie`, `Places`, `Code` suffisent.
> Le nom de la colonne « Places » est important : le nombre de places est lu
> depuis cette colonne.

Puis *Réponses → Lier à Google Sheets* (crée une feuille avec l'onglet
`Réponses du formulaire`).

### 2. Feuille « Compteur public » (vie privée)

La feuille des réponses contient les noms et téléphones : **elle reste privée**.
Le site lit à la place une seconde feuille, « Compteur public », dont la cellule
A1 contient :

```
=QUERY(IMPORTRANGE("<ID_FEUILLE_REPONSES>";"'Réponses au formulaire 1'!A:F");
  "select Col1, Col6, Col4, Col5 where Col1 is not null
   label Col1 'Horodatage', Col6 'Catégorie', Col4 'Places', Col5 'Code'";1)
```

(colonnes de la feuille des réponses : Horodateur, Nom, Téléphone, Nombre de
places, Code de réservation, Catégorie — adapter les numéros `ColN` si l'ordre
des questions change.)

Seule cette feuille est partagée : **Partager → Toute personne ayant le lien →
Lecteur**. Sans ce partage, la lecture échoue silencieusement et le site retombe
sur son cache local. Les organisateurs consultent les noms dans la feuille privée.

### 3. Relever les identifiants

```bash
python3 tools/google-form-ids.py 'https://docs.google.com/forms/d/e/FORM_ID/edit'
```

Le script affiche le `formId` et la liste des `entry.XXXX` avec le libellé de
chaque question, pour les recopier dans `CONFIG.google`.

### 4. Renseigner `CONFIG.google`

Dans `invitation-landing.html` :

```js
google: {
  formId: '1AbC…',
  entries: { name: 'entry.123', phone: 'entry.456', cat: 'entry.789',
             places: 'entry.101', code: 'entry.111' },
  sheetId: '1XyZ…',
  sheetGid: '0',
  configTab: 'Config',
  remoteAuthoritative: true
}
```

- `formId` → dans l'URL `…/forms/d/e/<FORM_ID>/edit`
- `sheetId` → l'ID de la feuille **Compteur public** (`…/spreadsheets/d/<SHEET_ID>/edit`)
- `entries` → les `entry.XXXX` (l'ordre des questions est celui du formulaire)
- `configTab` → nom d'un onglet du **Compteur public** où `A1 = CLOSED` ferme
  les réservations pour tout le monde (voir plus bas)

### 5. Fermer les réservations pour tous

Deux mécanismes, distincts :

- **Bouton « Clore les réservations »** (espace organisateurs) → clôture **locale**
  au navigateur de l'organisateur. Le site ne peut pas écrire dans Google
  Sheets depuis le navigateur (l'API exige une clé serveur), ce bouton est
  donc volontairement local.
- **Onglet `Config` de la feuille liée** → clôture **globale** :
  - `A1 = CLOSED` → tous les invités voient « réservations closes » ;
  - `A1 = OPEN` → les réservations sont rouvrées ;
  - onglet vide → l'état local est conservé tel quel.

La clôture globale est lue à chaque synchronisation (au chargement, toutes les
60 s, et après chaque envoi).

## Accès organisateurs
5 clics sur le logo « DH » (ou URL `invitation-landing.html#admin`), puis le PIN.

## État actuel
Les réservations sont stockées dans un **Google Form** (donc dans la feuille
`Réponses du formulaire`). Le site relit cette feuille au chargement puis
toutes les 60 s : les compteurs de places et le tableau organisateur sont donc
**synchronisés entre tous les invités**.

Le `localStorage` n'est plus qu'un cache local : si Google Sheets est
injoignable (feuille non partagée, hors ligne), le site continue de fonctionner
avec son cache et l'envoi au formulaire reste tenté.

## Téléphone obligatoire et unicité
Le numéro WhatsApp est obligatoire. Il est normalisé au format international
(un numéro à 9 chiffres est supposé camerounais : `+237…`), et le **code de
réservation en est dérivé** (SHA-256 tronqué). Un même numéro donne donc
toujours le même code : le site relit la feuille juste avant l'envoi et refuse
une seconde réservation, sans que les téléphones soient publiés dans le
Compteur public.

## Confirmation WhatsApp automatique
Le site statique ne peut pas envoyer de WhatsApp lui-même (le jeton d'accès
serait public). L'envoi est fait par **Google Apps Script** dans la feuille
privée des réponses : `tools/whatsapp-confirmation.gs` (instructions en tête
du fichier). Il utilise l'**API WhatsApp Cloud de Meta**, ce qui demande :
- un compte Meta Business et une app « WhatsApp » sur developers.facebook.com ;
- un numéro expéditeur dédié (pas déjà utilisé dans l'application WhatsApp) ;
- un modèle de message « Utilitaire » approuvé (texte en tête du script) ;
- un moyen de paiement : chaque confirmation est facturée par Meta.

Une fois en place, passer `CONFIG.whatsappAuto` à `true` : le bouton
« Envoyer sur WhatsApp » disparaît de la confirmation.
