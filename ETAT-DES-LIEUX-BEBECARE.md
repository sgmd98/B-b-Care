# BébéCare : état des lieux

**Dernière mise à jour** : 29 septembre 2026
**Version du site** : v2.17
**Échéance** : GatewayHacks 2026, clôture le 2 octobre 2026 à 00 h 00 EDT, soit le 2 octobre à 05 h 00 à Cotonou.

---

## Qui je suis

**FR** : SOSSA Gninazé Mingnissê Darius, infirmier diplômé d'État, développeur web et étudiant en Master 1 Puériculture-Pédiatrie, Cotonou, Bénin.

**EN** : SOSSA Gninazé Mingnissê Darius, state-certified nurse, web developer and Master 1 student in Childcare and Pediatrics, Cotonou, Benin.

---

## Les deux livrables

| Livrable | Adresse | État |
|---|---|---|
| Site BébéCare | https://bebecare.onrender.com (dépôt https://github.com/sgmd98/B-b-Care) | en cours, v2.17 prête, à fusionner sur `main` pour déploiement |
| Application BébéCare Terrain (Momen) | https://x3n5k1qy740vn.villa.momenapp.com/ | clos le 16 septembre 2026, 8 tests sur 8 réussis, ne plus modifier |
| Vidéo de présentation | montage local, narration enregistrée | en pause, reprendre après les captures du site à jour |

Le site personnel Django `sante-infantile-benin.onrender.com` est un projet distinct : ne pas le confondre avec BébéCare, ni modifier son dépôt.

---

## Ce qui a été fait en v2.17 (29 septembre 2026)

### Sécurité : diagnostic complet et corrections

13 failles trouvées et corrigées, dont la traversée de répertoire dans le service
des fichiers, l'absence de limitation de débit, le CORS ouvert, le jeton de
session impossible à révoquer et le secret de démonstration utilisé par défaut.
Le diagnostic complet, la correspondance avec l'OWASP Top 10 et les limites
assumées sont dans `docs/SECURITE.md`.

Résultat vérifiable : 52 contrôles de sécurité et 16 contrôles du chemin
PostgreSQL, soit 68 sur 68.

### Documents légaux et consentement

- Politique de confidentialité, conditions d'utilisation et mentions légales,
  en français et en anglais, accessibles sur `/#confidentialite`,
  `/#conditions` et `/#mentions`, versionnées et datées.
- Case de consentement obligatoire à l'inscription, version acceptée et date
  enregistrées en base.
- Droits des personnes implémentés dans Mon espace : export complet en un clic
  et suppression réelle du compte, des enfants et des mesures.
- Informations légales également exposées par l'API (`/api/legal`), pour qu'un
  tiers puisse vérifier sans lire le code.

### Cohérence

- Liens corrigés (GitHub de l'auteur), mention OpenStreetMap et OpenFreeMap au
  titre de la licence ODbL, tableaux de sources avec en-têtes traduits.
- Écran de démonstration de la page d'accueil signalé comme tel, pour ne pas
  laisser croire à des données réelles.
- Bloc de données personnelles ajouté sur la page À propos, avec accès direct
  aux documents légaux.
- Textes vérifiés : aucun tiret cadratin ni demi-cadratin dans les contenus
  publics.

### Responsive et confort de lecture

- Contrastes corrigés au seuil WCAG AA, lien d'évitement, focus visible,
  titres hiérarchisés, zones tactiles de 44 px, respect de la réduction des
  animations.
- Mise en page légale en onglets, sommaire cliquable, impression propre.
- Message explicite si le fond de carte ne charge pas, au lieu d'une carte vide.
- Favicon, icône iOS, manifeste et image de partage (1200 × 630) aux couleurs du
  site, à la place des fichiers du modèle de départ.

---

## Ce qui reste à faire

1. Fusionner la branche de travail sur `main` pour que Render redéploie, puis
   contrôler `https://bebecare.onrender.com/api/sante` (version 2.17) et les
   en-têtes de sécurité.
2. Prendre les captures d'écran du site à jour (accueil, carte, vaccins,
   nutrition, assistant, documents légaux) pour le montage vidéo.
3. Terminer le montage de la vidéo à partir de la narration enregistrée.
4. Vérifier la page de soumission GatewayHacks et l'envoyer avant le
   2 octobre 2026, 05 h 00 à Cotonou.
5. Contrôler une dernière fois l'application Momen (lecture seule), sans y
   toucher.

---

## Comment vérifier le dépôt

```bash
# Site
cd web && npm ci && npm run build

# API et sécurité
python3 -m venv /tmp/venv
/tmp/venv/bin/pip install -r api/requirements.txt httpx
/tmp/venv/bin/python scripts/verif_securite.py      # 52 controles
/tmp/venv/bin/python scripts/verif_postgres.py      # 16 controles
```

Règle de travail : ne jamais pousser si un contrôle échoue. Render ne redéploie
que la branche `main`.

---

## Journal des versions

| Version | Date | Contenu |
|---|---|---|
| v0.1 | 2026 | 4 pays, dossier `front/` |
| v2.10 | 2026 | 15 pays CEDEAO, IA hybride à trois étages, mode soignant DHIS2 |
| v2.13 | 2026 | allègement de l'assistant, vraie adaptation mobile |
| v2.15 | 2026 | propreté mobile après retours de terrain |
| v2.16 | 28 septembre 2026 | point enfant corrigé sur les courbes OMS |
| v2.17 | 29 septembre 2026 | sécurité, documents légaux, droits des personnes, accessibilité |

---

## Règles du projet

- Aucun tiret cadratin ni demi-cadratin dans les textes publics.
- Une seule action de correction à la fois, et un test de compilation après
  chaque modification.
- Jamais de suppression récursive d'un dossier du projet.
- Ce fichier est mis à jour à chaque jalon.
