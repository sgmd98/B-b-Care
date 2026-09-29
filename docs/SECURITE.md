# Diagnostic de sécurité et de conformité

**Projet** : BébéCare, santé de l'enfant 0-5 ans dans les 15 pays de la CEDEAO
**Date du diagnostic** : 29 septembre 2026
**Version auditée** : v2.16, corrigée et livrée en v2.17
**Périmètre** : API FastAPI (`api/`), interface React (`web/`), base des comptes (SQLite en local, PostgreSQL Neon en production), passerelle DHIS2, assistant IA.
**Méthode** : lecture du code ligne à ligne, tests HTTP automatisés sur l'application réelle (52 contrôles), tests du chemin PostgreSQL (`16` contrôles), vérification des en-têtes, des routes, des schémas de saisie et des droits des personnes.

Résultat final : **68 contrôles sur 68 réussis**. Deux scripts permettent de rejouer l'ensemble (`scripts/verif_securite.py`, `scripts/verif_postgres.py`).

---

## 1. Failles trouvées et corrigées

### F1. Traversée de répertoire dans le service des fichiers du site (gravité haute)

Le serveur servait n'importe quel fichier demandé sous `web/dist` en construisant le chemin sans le contrôler. Une requête construite à la main, du type `/%2e%2e/%2e%2e/api/main.py`, permettait de lire le code source de l'API, les scripts de génération de données et toute la configuration du serveur.

**Correction** : le chemin est désormais résolu (`os.path.realpath`) puis comparé au dossier `web/dist`. Toute demande qui sort du dossier retombe sur la page du site. Testé sur quatre écritures différentes de la même attaque.

### F2. Nom de fichier non contrôlé dans le PDF du carnet vaccinal (gravité moyenne)

Le prénom transmis dans l'adresse du PDF finissait dans l'en-tête `Content-Disposition`. Un prénom contenant des guillemets ou un retour à la ligne permettait de manipuler la réponse HTTP.

**Correction** : prénom limité à 40 caractères, liste de vaccins limitée à 2000 caractères, paramètres validés par le schéma Pydantic. Le générateur PDF neutralise déjà les caractères non imprimables.

### F3. Aucune limitation de débit sur les routes sensibles (gravité haute)

Rien n'empêchait d'essayer des milliers de mots de passe, de créer des comptes en masse ou d'épuiser le quota du fournisseur d'IA. Sur une instance gratuite, c'est aussi une cause directe d'indisponibilité.

**Correction** : limiteur de débit en mémoire, par adresse IP et par route (aucune dépendance externe) :

| Route | Quota |
|---|---|
| `POST /api/compte/connexion` | 12 tentatives par 15 minutes |
| `POST /api/compte/inscription` | 6 comptes par heure |
| `POST /api/compte/mot-de-passe` | 6 par heure |
| `POST /api/assistant*` | 40 par 5 minutes |
| `POST /api/dhis2/push`, `seance/envoyer` | 30 par 15 minutes |
| `GET /api/vaccins/calendrier.pdf`, `ics` | 80 par 15 minutes |
| toutes les routes `/api/` | 600 par minute |

Réponse `429` avec un message en français et un en-tête `Retry-After`.

### F4. CORS ouvert à tous (gravité moyenne)

`allow_origins=["*"]` autorisait n'importe quel site à appeler l'API. Le jeton de session étant envoyé par l'interface elle-même, l'exposition restait limitée, mais l'ouverture n'avait aucune raison d'être.

**Correction** : liste blanche fermée (`BEBECARE_ORIGINES`, par défaut `https://bebecare.onrender.com`), méthodes et en-têtes limités à ceux réellement utilisés, `allow_credentials` désactivé.

### F5. Documentation interactive exposée (gravité faible)

`/docs` et `/openapi.json` publiaient la carte complète des routes et des schémas de l'API, sans rien apporter aux utilisateurs.

**Correction** : documentation fermée par défaut, réactivable par `BEBECARE_DOCS=1` pour le jury ou pour un audit.

### F6. Aucun en-tête de sécurité (gravité moyenne)

Ni politique de sécurité du contenu, ni protection contre le détournement de cadre, ni restriction des permissions. Une page de santé infantile doit se protéger de l'injection de script et de l'affichage dans un cadre tiers.

**Correction** : en-têtes ajoutés à toutes les réponses, avec une politique de contenu qui n'autorise que les domaines réellement utilisés (fonds de carte OpenFreeMap, météo Open-Meteo) :

- `Content-Security-Policy` (aucun script en ligne, `object-src 'none'`, `frame-ancestors` restreint)
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (géolocalisation limitée à `self`, caméra et micro fermés)
- `Strict-Transport-Security`, `Cross-Origin-Opener-Policy`, `X-Frame-Options`

### F7. Mots de passe sans borne de taille (gravité moyenne)

Un mot de passe de plusieurs mégaoctets faisait tourner PBKDF2 pendant des minutes : quelques requêtes suffisaient à saturer un processeur.

**Correction** : longueur bornée (8 à 200 caractères) à l'inscription, à la connexion et au changement de mot de passe, avec message explicite.

### F8. Jeton de session impossible à révoquer (gravité moyenne)

Un jeton volé restait valable 30 jours, même après un changement de mot de passe. Le compte supprimé laissait un jeton signé valide, sans utilisateur derrière.

**Correction** : chaque compte porte un numéro de génération de jetons. Le changement de mot de passe l'incrémente : tous les jetons déjà émis deviennent inutilisables immédiatement. La suppression du compte invalide aussi tout. La vérification d'un jeton contrôle désormais la signature, l'expiration, la génération et l'existence du compte.

### F9. Validation des saisies trop permissive (gravité moyenne)

Les schémas acceptaient `role` libre, `langue` libre, identifiant de 5000 caractères, vaccins sans limite, dates de naissance dans le futur, identifiants contenant du balisage.

**Correction** : valeurs fermées (`Literal`), bornes de taille sur chaque champ, format d'identifiant contrôlé (lettres, chiffres, ponctuation d'adresse ou de numéro uniquement), dates plausibles (passé, après 1900), listes de vaccins bornées à 200 entrées.

### F10. Secret de démonstration par défaut (gravité haute)

Sans `BEBECARE_SECRET`, la clé de signature valait `dev-secret-a-changer-en-production` : un secret public, écrit dans le dépôt, avec lequel n'importe qui pouvait forger un jeton de session valide.

**Correction** : sans variable d'environnement, un secret aléatoire est généré à chaque démarrage, avec un avertissement clair dans les journaux. Les sessions ne survivent pas à un redémarrage, ce qui est le bon compromis. Render génère déjà la valeur (`generateValue: true`).

### F11. Écriture DHIS2 ouverte (gravité moyenne)

L'envoi vers DHIS2 était possible sans compte, donc par n'importe qui.

**Correction** : l'envoi est réservé aux comptes déclarés soignants (`403` pour un compte parent, `401` sans compte). La préparation du document reste libre, l'écriture réelle reste bloquée tant que `BEBECARE_DHIS2_PUSH` ne vaut pas `1`.

### F12. Routes API inconnues renvoyant la page du site (gravité faible)

`/api/route-inexistante` répondait `200` avec du HTML : les erreurs étaient masquées et un client d'API pouvait interpréter du HTML comme une réponse valide.

**Correction** : toutes les routes `api/`, `docs`, `redoc` et `openapi.json` renvoient un `404` en JSON, jamais la page du site.

### F13. Réponses de compte mises en cache (gravité faible)

Aucun en-tête n'empêchait un navigateur partagé ou un proxy de conserver une réponse contenant les données d'un enfant.

**Correction** : `Cache-Control: no-store` sur toutes les routes `/api/compte/`, et nulle part ailleurs (les données publiques restent cacheables).

---

## 2. Durcissements ajoutés sans faille identifiée

- **Migration de base idempotente** : les colonnes de consentement et de génération de jetons sont ajoutées après contrôle du catalogue (`PRAGMA table_info` en SQLite, `information_schema` en PostgreSQL) au lieu de tenter un `ALTER TABLE` à l'aveugle, qui annulerait la transaction en cours sur PostgreSQL.
- **Consentement horodaté** : la version des documents acceptée et sa date sont enregistrées à l'inscription. C'est la preuve du consentement, exigée pour des données de santé.
- **Droits des personnes implémentés côté serveur** : export complet (`GET /api/compte/export`) et suppression réelle (`DELETE /api/compte/moi`), avec vérification du mot de passe. Aucune copie conservée.
- **Informations légales exposées par l'API** (`/api/legal`, `/api/legal/version`) : un tiers peut vérifier sans lire le code.
- **En-tête de version** (`X-BebeCare-Version`) : permet de savoir quelle version répond.
- **Géolocalisation** : elle n'est lue que sur appui explicite du bouton « Autour de moi », et uniquement par le navigateur de l'utilisateur. Aucune position n'est enregistrée côté serveur.

---

## 3. Conformité

### Protection des données

| Exigence | État | Mise en oeuvre |
|---|---|---|
| Base légale et consentement | OK | case obligatoire à l'inscription, version et date enregistrées |
| Information des personnes | OK | politique de confidentialité, conditions d'utilisation, mentions légales, versions datées |
| Minimisation | OK | identifiant, prénom, sexe, date de naissance, mesures. Rien de plus |
| Durée de conservation | OK | tant que le compte existe, suppression immédiate à la demande |
| Droit d'accès et de portabilité | OK | export JSON en un clic depuis Mon espace |
| Droit à l'effacement | OK | suppression du compte, des enfants et des mesures, sans copie |
| Droit de rectification | OK | chaque champ du compte, de l'enfant et des mesures est modifiable |
| Retrait du consentement | OK | documenté, équivaut à la suppression du compte |
| Sécurité du traitement | OK | voir section 1 |
| Traçabilité des sources | OK | chaque donnée affichée indique sa source, sa licence et sa date |
| Autorité de contrôle | OK | APDP citée dans la politique de confidentialité |

Cadre applicable : Code du numérique de la République du Bénin (loi n° 2017-20) et principes du RGPD.

### Référentiel OWASP Top 10 (2021)

| Risque | État | Mesure |
|---|---|---|
| A01 Contrôle d'accès défaillant | corrigé | `_uid` et `_soignant` sur toutes les routes privées, vérification d'appartenance de chaque enfant |
| A02 Défaillances cryptographiques | corrigé | PBKDF2 240 000 itérations, sel unique, secret aléatoire, HSTS |
| A03 Injection | corrigé | requêtes paramétrées partout, aucune concaténation de valeur, validation Pydantic stricte |
| A04 Conception non sécurisée | corrigé | limiteur de débit, quotas, consentement, minimisation |
| A05 Mauvaise configuration | corrigé | CORS fermé, documentation fermée, en-têtes de sécurité, aucun secret dans le dépôt |
| A06 Composants vulnérables | à surveiller | dépendances épinglées (`api/requirements.txt`, `web/package-lock.json`) |
| A07 Identification et authentification | corrigé | hachage fort, génération de jetons, anti force brute, invalidation |
| A08 Intégrité des données et du logiciel | partiel | aucune donnée d'enfant envoyée à DHIS2, écriture désactivée par défaut |
| A09 Journalisation et surveillance | partiel | journaux Render, compteurs d'usage de l'IA, pas d'alerte automatique |
| A10 Falsification de requête côté serveur | non applicable | aucune URL fournie par l'utilisateur n'est appelée par le serveur |

### Accessibilité (WCAG 2.2, niveau AA visé)

- lien d'évitement vers le contenu principal, en première position dans l'ordre de tabulation ;
- focus visible sur tous les éléments interactifs, jamais supprimé ;
- contrastes corrigés : les deux gris de l'interface passent le seuil de 4,5:1 ;
- titres hiérarchisés (un seul `h1` par page, sections en `h2`) ;
- libellés associés à chaque champ, messages d'erreur en français lisible ;
- zones tactiles de 44 px minimum dans le menu mobile ;
- respect du réglage système de réduction des animations ;
- texte redimensionnable, mise en page qui reste lisible jusqu'à 320 px de large ;
- titres de page et de documents légaux imprimables, structure lisible sans CSS ;
- message explicite si le fond de carte ne charge pas, plutôt qu'une carte vide.

---

## 4. Limites assumées

Ces points sont connus, documentés et volontairement hors périmètre de cette version.

1. **Pas d'authentification à deux facteurs.** Elle suppose l'envoi de SMS, donc un coût et un sous-traitant supplémentaire.
2. **Limiteur de débit en mémoire.** Une seconde instance Render aurait son propre compteur. Avec une seule instance gratuite, le comportement est correct.
3. **Journalisation minimale.** Les journaux Render conservent les requêtes quelques jours. Aucun outil d'alerte n'est branché.
4. **Pas d'audit externe.** Ce diagnostic est interne. Pour une mise en service en établissement, un test d'intrusion par un tiers reste recommandé.
5. **Base gratuite.** Neon et Render en offre gratuite : disponibilité sans engagement contractuel. Les données de compte sont donc à sauvegarder par export si le service devient critique.
6. **Données cartographiques participatives.** Un centre de santé peut être fermé ou déplacé. L'interface le signale et renvoie au centre de santé de référence.

---

## 5. Rejouer les vérifications

```bash
# Dépendances (une seule fois, environnement isolé)
python3 -m venv /tmp/venv
/tmp/venv/bin/pip install -r api/requirements.txt httpx

# 52 contrôles de sécurité sur l'application réelle
/tmp/venv/bin/python scripts/verif_securite.py

# 16 contrôles du chemin PostgreSQL (Neon) sans serveur PostgreSQL
/tmp/venv/bin/python scripts/verif_postgres.py

# Compilation du site
cd web && npm ci && npm run build
```

Les deux scripts sortent avec un code d'erreur non nul si un contrôle échoue : ils peuvent servir de garde-fou avant chaque déploiement.

---

## 6. Journal des versions de sécurité

| Version | Date | Contenu |
|---|---|---|
| v2.16 | 28 septembre 2026 | point enfant corrigé sur les courbes OMS |
| v2.17 | 29 septembre 2026 | ce diagnostic : 13 failles corrigées, documents légaux, droits des personnes, accessibilité, en-têtes de sécurité, limiteur de débit |

Toute nouvelle faille corrigée doit être ajoutée à ce journal avec sa version.
