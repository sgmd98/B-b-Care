# Page Devpost — brouillon prêt à copier

> Titre : **BébéCare — la santé de l'enfant 0-5 ans, pour 15 pays d'un seul coup**
> Tagline : *Every official child-health source for West Africa, in one free app that speaks DHIS2.*

---

## Inspiration

Je suis infirmier-puériculteur à Cotonou, au Bénin. Dans mon service, je vois
chaque semaine la même scène : une mère arrive avec un enfant qui a maigri depuis
deux mois, ou avec un carnet de vaccination où il manque trois doses. À chaque
fois, l'information qui aurait évité ça existait déjà — elle était juste
inaccessible.

Le calendrier vaccinal officiel du Bénin ? Un PDF sur le site du ministère.
Les normes de croissance de l'OMS ? Un tableur Excel de 1 857 lignes.
La liste des centres de santé ? Nulle part, en pratique.
Les taux de couverture ? Dans DHIS2, la base nationale — à laquelle aucune mère
n'aura jamais accès.

Les chiffres OMS 2025 disent le résultat : au Bénin, seulement **49 %** des
enfants reçoivent leur première dose de vaccin contre la rougeole. Au Niger,
la mortalité des moins de cinq ans dépasse encore **100 pour 1 000**.

J'ai décidé de rassembler toutes ces sources dans une seule application, gratuite,
et de ne pas la limiter à mon pays.

## Ce que fait BébéCare

**🗺️ Une carte des soins pour 15 pays** — 23 568 structures de santé (hôpitaux,
centres, maternités, pharmacies, laboratoires) dans les 15 pays de la CEDEAO,
extraites d'OpenStreetMap. Un bouton « autour de moi » donne le centre le plus
proche avec la distance et l'itinéraire.

**💉 Un carnet vaccinal qui connaît le calendrier de votre pays** — pas un
calendrier générique : le calendrier national officiel 2025 de chacun des 15 pays,
issu du jeu de données OMS/UNICEF « Vaccine schedule ». On saisit la date de
naissance, l'app calcule chaque rendez-vous, signale les retards et exporte tous
les rappels vers l'agenda du téléphone.

**⚖️ Un dépistage de la malnutrition aux vraies normes OMS** — z-scores
poids-pour-âge, taille-pour-âge et poids-pour-taille calculés avec les tables LMS
officielles de l'OMS, plus le périmètre brachial aux seuils 115/125 mm. Ce sont
exactement les indicateurs qu'utilisent les agents de santé communautaires.

**🩺 Une orientation « que faire maintenant ? »** — un moteur qui applique la
logique PCIME de l'OMS, l'algorithme officiel des centres de santé ouest-africains.
Volontairement prudent : au moindre signe de danger, il envoie au centre de santé
et affiche le numéro d'urgence du pays.

**📊 Une passerelle DHIS2** — voir ci-dessous.

## Pourquoi DHIS2 rend ce projet sérieux

DHIS2 est le système national d'information sanitaire de plus de 80 pays, dont
**14 des 15 pays** couverts par BébéCare. C'est là que remontent les vraies
données de vaccination.

Le problème du terrain : un agent de santé communautaire note les vaccinations sur
papier, et quelqu'un les ressaisit dans DHIS2 des semaines plus tard. Double saisie,
retards, erreurs.

BébéCare fait les deux sens :

1. **Lecture en direct** — les indicateurs de couverture (BCG, Pentavalent 1 et 3,
   rougeole, VPO 3) sont lus en temps réel par l'API `analytics` de DHIS2, district
   par district. Rien n'est en dur : changez de district dans l'app, la requête part.
2. **Écriture conforme** — le carnet et le dépistage sont traduits en un document
   `dataValueSets` valide (bon `dataSet`, bonne période `AAAAMM`, bons
   `dataElement` et `categoryOptionCombo`), prêt à être poussé dans le SNIS.

**Point important d'éthique** : BébéCare ne se connecte à **aucune base nationale
de production** — ce sont des données de santé réelles, réservées aux ministères.
La démonstration tourne sur l'instance publique officielle de DHIS2 (base
Sierra Leone, données fictives). Et l'écriture est **désactivée par défaut** :
l'app génère et valide le payload sans jamais modifier une base publique.
Un ministère n'a que trois variables d'environnement à changer pour brancher
BébéCare sur son propre DHIS2.

## Comment c'est construit

- **Backend** : FastAPI (Python), 20 routes REST, documentation OpenAPI automatique.
  Index spatial en grille de 0,25° construit en mémoire au démarrage : la recherche
  « centre le plus proche » parmi 23 568 points répond en quelques millisecondes,
  sans base de données.
- **Frontend** : React 19 + Vite, Leaflet avec clustering Supercluster (afficher
  23 568 marqueurs sans clustering fige n'importe quel téléphone), Recharts pour
  les courbes de croissance et les graphiques DHIS2.
- **Données** : quatre pipelines reproductibles (`scripts/`) qui vont chercher
  OpenStreetMap via Overpass, l'OMS GHO (WUENIC), les tables de croissance OMS et
  les calendriers vaccinaux WIISE. Tout est régénérable d'une commande.
- **Déploiement** : un seul service web sur Render, l'API sert le front compilé.
  Démarrage en moins d'une seconde, tient sur une instance gratuite.

## Sources — aucun chiffre inventé

| Donnée | Source | Licence |
|---|---|---|
| Structures de santé | OpenStreetMap | ODbL 1.0 |
| Calendriers vaccinaux | OMS/UNICEF, *Vaccine schedule* (WIISE) | Données ouvertes OMS |
| Couverture vaccinale, mortalité | OMS GHO — estimations WUENIC 2025 | Données ouvertes OMS |
| Normes de croissance | WHO Child Growth Standards (tables LMS) | OMS |
| Logique de triage | PCIME (OMS/UNICEF) | OMS |
| Interopérabilité | DHIS2 — instance de démonstration publique | Données fictives |

## Les difficultés

**Afficher 23 568 points sans tuer le téléphone.** La première version chargeait
tout le pays d'un coup et gelait le navigateur. J'ai fini par combiner une requête
serveur par emprise de carte (grille spatiale côté API) et un clustering
Supercluster côté client. La carte reste fluide même sur le Nigéria, 7 555 points.

**Faire parler DHIS2 correctement.** Un payload `dataValueSets` refusé ne dit pas
pourquoi. Il a fallu explorer les métadonnées de l'instance pour trouver le bon
`dataSet` (Child Health), les bons `dataElement` par vaccin, et surtout la bonne
`categoryOptionCombo` (« Fixed, <1y »). J'ai ajouté un validateur local qui vérifie
le schéma avant tout envoi.

**Les queues de z-scores.** La formule LMS brute donne des valeurs aberrantes
au-delà de ±3 écarts-types — précisément la zone qui nous intéresse en malnutrition
sévère. J'ai implémenté l'ajustement officiel de l'OMS (méthode *igrowup*) pour que
les cas graves soient classés correctement.

## Ce dont je suis fier

- Chaque chiffre affiché est traçable jusqu'à une source officielle, citée et datée.
- Aucune donnée de l'enfant ne quitte le téléphone : ni compte, ni serveur, ni traceur.
- Le projet est conçu par quelqu'un qui exerce sur le terrain, pas depuis un tableur.
- Le pont DHIS2 fonctionne réellement, et il est honnête sur ce qu'il fait.

## La suite

- Mode hors ligne complet (PWA) — décisif en zone rurale
- Rappels vaccinaux par SMS et WhatsApp
- Langues locales : fon, yoruba, wolof, haoussa
- Conventions avec un ministère pilote pour activer l'écriture DHIS2 en vrai
- Extension aux 54 pays de l'Union africaine

## Essayer

- 🌍 Démo : *(ton lien Render)*
- 💻 Code : https://github.com/sgmd98/B-b-Care
- 📖 API : *(ton lien Render)*/docs

---

**Avertissement** : BébéCare est un outil d'information et de dépistage. Il ne pose
aucun diagnostic et ne remplace jamais l'avis d'un professionnel de santé.
