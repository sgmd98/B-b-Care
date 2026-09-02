# Stratégie GatewayHacks 2026 — plan pour gagner

Deadline : **2 octobre 2026, 00 h 00 EDT**. Il reste ~31 jours.

## 1. Comment on est noté

| Critère | Poids | Ce que ça veut dire concrètement | Où on en est |
|---|---|---|---|
| **Social Impact** | 40 % | Le problème est-il réel, documenté, et la solution y répond-elle ? | ✅ chiffres OMS 2025 officiels, 15 pays, 23 568 structures |
| **Technical Execution** | 30 % | Le prototype marche-t-il vraiment ? | ✅ app complète en ligne + API documentée + DHIS2 live |
| Créativité / présentation | 30 % | Idée originale, pitch clair, démo propre | 🔨 à travailler (vidéo + page Devpost) |

**Conclusion : 70 % de la note est déjà dans la boîte.** Le reste se joue sur la
vidéo et la page Devpost. Ne néglige surtout pas ces deux-là — c'est là que la
plupart des bons projets perdent.

## 2. Tracks à cocher

- **Track 1 — Accessibility & Health** : track principal, évident.
- **Track 4 — Open Impact & Community** : si le formulaire autorise un second choix.
- **Best No-Code AI App built with Momen** : tu as dit oui. Voir §6 — c'est
  2 000 $ de crédits en plus pour ~4 h de travail.

## 3. Réponses à tes deux questions

### « On utilise la démo DHIS2 vu que c'est pas officiel, ou bien ? »

**Oui, la démo — et c'est même le choix le plus fort, pas un repli.** Voilà pourquoi :

- Les DHIS2 nationaux (Bénin, Sénégal, Nigéria…) contiennent des **données de santé
  réelles**. L'accès est réservé au ministère. Y toucher sans convention serait
  illégal et te ferait disqualifier.
- L'instance `play.im.dhis2.org` est **publiée par DHIS2 lui-même** avec des
  identifiants publics (`admin` / `district`) et une base **fictive** (Sierra Leone).
  Elle est faite exactement pour ça : démontrer une intégration.
- Le pitch gagnant n'est donc pas « je suis branché sur le SNIS du Bénin » (faux et
  risqué) mais : **« BébéCare parle nativement DHIS2. Voici la preuve en direct.
  Un ministère change trois variables d'environnement et c'est branché sur son
  propre système. »** C'est plus honnête *et* plus impressionnant.
- Bonus narratif : la base de démo DHIS2, c'est la **Sierra Leone** — un des
  15 pays CEDEAO que tu couvres. La démo tombe pile dans ton périmètre.
- Sécurité : l'écriture est **désactivée par défaut** (`BEBECARE_DHIS2_PUSH=0`).
  Tu génères et valides le payload sans jamais polluer la base publique. Dis-le
  dans la vidéo — les juges techniques adorent ce genre de retenue.

**Aucun problème juridique** au global :
- OpenStreetMap → ODbL, attribution affichée sur la carte. ✅
- OMS (GHO, WUENIC, calendriers, tables de croissance) → données ouvertes, sources citées. ✅
- DHIS2 → instance de démo publique, données fictives, pas d'écriture. ✅
- Données utilisateur → jamais envoyées à un serveur, tout en `localStorage`. ✅
  (Ça t'évite en plus toute question RGPD / données de santé.)
- Avertissement médical présent sur chaque module clinique. ✅

### « Combien de pays tu me recommandes ? »

**Les 15 pays de la CEDEAO — c'est déjà fait.** Pourquoi ce choix et pas 54 :

1. La CEDEAO est une **entité politique réelle**. « Une plateforme pour la CEDEAO »
   est un pitch net ; « une plateforme pour l'Afrique » sonne creux et fait
   amateur.
2. 23 568 structures, c'est déjà massif à l'écran — les juges voient une carte
   dense, pas un prototype.
3. 15 pays, ça reste **vérifiable** : tu peux défendre chaque calendrier vaccinal.
   Sur 54, un juge trouve une erreur et ta crédibilité tombe.
4. Ça laisse une **roadmap** crédible à annoncer : « la CEDEAO d'abord, l'Union
   africaine ensuite » — les juges aiment un projet qui sait où il va.

Pays couverts : Bénin, Burkina Faso, Cabo Verde, Côte d'Ivoire, Gambie, Ghana,
Guinée, Guinée-Bissau, Liberia, Mali, Niger, Nigéria, Sénégal, Sierra Leone, Togo.

## 4. Ce qui est déjà construit

- API FastAPI, 20 routes, documentation OpenAPI auto sur `/docs`
- 23 568 structures de santé indexées spatialement (recherche « le plus proche » instantanée)
- Calendriers vaccinaux **officiels OMS 2025** pour les 15 pays
- Z-scores OMS avec les **vraies tables LMS** (poids/âge, taille/âge, poids/taille, PB)
- Moteur de triage PCIME
- Passerelle DHIS2 : statut live, analytics live par district, payload `dataValueSets` validé
- Front React : carte clusterisée, carnet vaccinal avec export `.ics`, courbes de croissance

## 5. Plan des 31 jours

**Semaine 1 (2-8 sept.) — crédibilité clinique**
- [ ] Faire relire tes règles de triage par un collègue soignant. **Note son nom et
      son titre dans le README** : « algorithme revu par X, infirmier d'État ».
      C'est un différenciateur énorme face à des lycéens.
- [ ] Vérifier 3 calendriers vaccinaux (Bénin, Sénégal, Nigéria) contre les PDF du PEV
      et documenter les écarts éventuels.
- [ ] Déployer sur Render depuis le nouveau dépôt et vérifier le démarrage à froid.

**Semaine 2 (9-15 sept.) — terrain**
- [ ] Montrer l'app à **5 mères à Cotonou** et 2 agents de santé. Filme 20 secondes
      de leurs réactions (avec accord). Une seule citation réelle vaut dix slides.
- [ ] Corriger ce qu'elles ne comprennent pas. C'est là que tu gagnes les 40 %.
- [ ] Ajouter le mode hors-ligne (PWA + service worker) : décisif en zone rurale,
      et très visible en démo (couper le wifi et l'app marche encore).

**Semaine 3 (16-22 sept.) — finition**
- [ ] Rappels vaccinaux par SMS/WhatsApp, ou au minimum un lien `wa.me` prérempli
- [ ] Traduction EN complète (le jury est anglophone : Jonathan Chang, Yaokai Jiang)
- [ ] Page Devpost rédigée (voir `DEVPOST.md`)
- [ ] Vitrine Momen (§6)

**Semaine 4 (23-30 sept.) — la vidéo**
- [ ] Tourner et monter (voir `VIDEO.md`). Vise 3 min 30, max 5 min.
- [ ] Soumettre **le 29 septembre**, pas le 1er octobre. Devpost sature à la deadline.

## 6. Le prix Momen (2 000 $ de crédits)

Tu as dit oui. La façon rentable de le faire, sans refaire l'app :

Construis sur [momen.app](https://momen.app) un **« BébéCare Agent »** : un petit
agent conversationnel no-code où une mère tape « mon bébé de 8 mois a la diarrhée
depuis 2 jours » et qui appelle **ton API BébéCare** (`POST /api/triage`,
`GET /api/carte/proches`) pour répondre. Tu as déjà les endpoints, ils sont publics
et documentés.

Argument de pitch : *« BébéCare n'est pas qu'une app, c'est une infrastructure de
données pour la santé de l'enfant. Voici un second produit construit dessus en une
après-midi, sans code. »* Ça coche le track Momen ET renforce ton score technique.

## 7. Les cinq phrases à répéter partout

1. « 15 pays, 23 568 structures de santé, un seul lien. »
2. « Chaque chiffre vient d'une source officielle OMS, citée et datée. »
3. « BébéCare parle nativement DHIS2 : le système d'information sanitaire de
    14 des 15 pays qu'il couvre. »
4. « Aucune donnée de l'enfant ne quitte le téléphone. »
5. « Conçu par un infirmier-puériculteur qui exerce sur le terrain. » ← **ton
    avantage décisif.** Aucun autre participant n'a ça. Mets-le dès la première
    phrase de la page Devpost et dès la 10ᵉ seconde de la vidéo.

## 8. Les pièges à éviter

- ❌ Prétendre être connecté au DHIS2 national d'un pays. Un juge vérifie, tu perds tout.
- ❌ Une vidéo qui montre du code. Montre l'app, montre une mère, montre la carte.
- ❌ Oublier de rejoindre le Discord Gateway : c'est **obligatoire** dans le règlement.
- ❌ Soumettre sans le lien du dépôt public et sans capture d'écran.
- ❌ Laisser l'instance Render en veille le jour du jugement : garde un ping
      toutes les 10 min (cron-job.org gratuit) pour que la démo réponde instantanément.
