# Checklist GatewayHacks 2026

Vérifié sur la page officielle le 1er septembre 2026.
Deadline : **2 octobre 2026 à 00 h 00 EDT**, soit **05 h 00 à Cotonou**.

---

## Éligibilité : validée

| Règle officielle | Ta situation |
|---|---|
| **Ages 13+** | OK |
| **Students only** | **OK, confirmé.** Master 1 validé et inscrit en master de puériculture et pédiatrie, plus une 1re année en génie logiciel et intelligence artificielle, plus freeCodeCamp. Trois statuts d'étudiant en cours. |
| Companies/professional organizations excluded | Tu participes en ton nom propre, pas au nom d'un employeur. OK |
| Équipe de 1 à 4 | Tu es seul. OK |
| **Rejoindre le Discord : obligatoire** | https://discord.gg/XgsX3f7JV — **à faire aujourd'hui** |

L'éligibilité est réglée. Si un organisateur demande une preuve, un certificat de
scolarité ou une capture de ton tableau de bord de formation en ligne suffit.
Le seul point encore ouvert : **rejoindre le Discord**, qui est obligatoire.

---

## Barème réel des juges

Attention, il a changé par rapport à ce qu'on croyait :

| Critère | Poids | Ce que ça veut dire pour BébéCare |
|---|---|---|
| **Social Impact** | **40 %** | Ton point fort. Chiffres OMS, 15 pays, mortalité infantile |
| **Technical Execution** | **30 %** | Le prototype doit **fonctionner** devant le juge |
| **Innovation** | **20 %** | DHIS2 + IA sous garde-fous PCIME |
| **Design & UX** | **10 %** | Moins déterminant qu'on pensait |

70 % de la note se joue donc sur **l'impact social** et **le fait que ça
marche**. Pas sur la beauté. Concentre ton énergie là-dessus.

### Les deux juges

- **Jonathan Chang**, CTO de GatewayGS
- **Yaokai Jiang**, fondateur et PDG de **Momen** — c'est lui qui jugera le
  track no-code, et il ouvrira ton projet Momen

---

## Durée de la vidéo : attention au piège

La page se contredit :

- Section *Get started* : « a **3-minute** video demo »
- Section *What to Submit* : « A Video Pitch (**Max 5 mins**) »

**Vise 3 minutes.** Une vidéo de 3 min respecte les deux formulations ; une
vidéo de 4 min 30 en viole une. Ce n'est pas un risque à prendre.

### Découpage proposé (3 min)

| Temps | Contenu |
|---|---|
| 0:00-0:25 | Le problème. Toi à l'écran. « Je suis infirmier-puériculteur à Cotonou. Au Bénin, seuls **49 %** des enfants reçoivent leur première dose de vaccin contre la rougeole. » |
| 0:25-0:50 | La carte : 23 568 structures de santé, 15 pays |
| 0:50-1:30 | L'assistant IA. Tape une phrase **mal orthographiée** en direct. Montre le verdict rouge. Explique en une phrase que la décision vient de la PCIME, pas du modèle de langage |
| 1:30-2:10 | Le mode soignant. Deux enfants, puis le JSON DHIS2 qui s'affiche |
| 2:10-2:40 | **L'app Momen** sur un téléphone, en vrai |
| 2:40-3:00 | Ta légitimité : infirmier en master de puériculture **et** développeur en formation génie logiciel/IA. Et : c'est gratuit, sans inscription obligatoire |

---

## À soumettre

| Élément | Obligatoire ? | État |
|---|---|---|
| Page Devpost avec titre, description du problème, **au moins 1 visuel** | Oui | À faire |
| Vidéo ≤ 3 min avec lien public (YouTube non répertorié) | Oui | À faire |
| Dépôt GitHub public | *Optionnel* mais indispensable pour la note technique | https://github.com/sgmd98/B-b-Care |
| Site live | *Optionnel* mais idem | Render, à déployer |
| App Momen publiée | Requis pour le prix Momen | Voir `docs/MOMEN.md` |

> « Optionnel » sur le papier. Dans les faits, **Technical Execution vaut 30 %**
> et se juge sur un prototype qui tourne. Livre les deux.

---

## Choix des tracks

Coche sur Devpost :

1. **Best No-Code AI App built with Momen** — la page précise explicitement que
   ça ne t'enlève pas les autres prix
2. **Track 1 : Accessibility & Health** — « democratize healthcare information »,
   c'est mot pour mot ta description

---

## Les pièges à éviter

| Piège | Parade |
|---|---|
| Le service Render s'endort après 15 min | UptimeRobot toutes les 5 min (voir `DEPLOIEMENT.md`) |
| Le juge ouvre le site et tombe sur une page blanche | Idem, et vérifie le site la veille de la deadline |
| La vidéo dure 4 min | Vise 3 min |
| Projet Momen vide | Le PDG de Momen est juge. Construis-le vraiment |
| Soumission le dernier jour | Devpost sature. Soumets le **30 septembre** |
| Vidéo en privé sur YouTube | Mets « non répertoriée », jamais « privée » |

---

## Ce qui est déjà fait

- 15 pays CEDEAO, 23 568 structures de santé cartographiées
- Assistant IA hybride, décision PCIME déterministe
- Mode soignant DHIS2 avec agrégation correcte
- Comptes utilisateurs, outils utilisables sans inscription
- Interface calquée sur ton design, logo intégré
- README bilingue français et anglais
- Base Neon, guide de déploiement

## Ce qu'il reste

1. Rejoindre le Discord — **obligatoire, à faire aujourd'hui**
2. Déployer sur Render
3. Construire l'app Momen
4. Tourner la vidéo
5. Rédiger la page Devpost
