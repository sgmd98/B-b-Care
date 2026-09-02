# Kit Momen — « BébéCare Terrain »

Ce document contient tout ce qu'il faut pour construire, **sans écrire une ligne
de code**, l'application compagnon qui te qualifie pour le prix
**Best No-Code AI App built with Momen** (2 000 $ + 2 000 $ de crédits).

Temps estimé : **3 à 4 heures**. Prérequis : BébéCare déployé sur Render.

---

## 1. Pourquoi une deuxième application

Soyons clairs sur la règle. Le track Momen dit :

> *Use https://momen.app/ to build apps and agents without code! Entering this
> track qualifies you for the Momen-specific track award, as well as the other
> track awards!*

Le site BébéCare est du code Python et React. Il **ne peut pas** gagner ce prix,
quoi qu'on écrive sur la page Devpost. Le juge de ce track est **Yaokai Jiang,
fondateur et PDG de Momen** : il ouvrira le projet Momen et verra tout de suite
s'il est vide.

En revanche, la même phrase dit que participer au track Momen **ne t'enlève
rien** : tu restes éligible au Best Overall et aux autres prix. La stratégie
optimale est donc :

| Livrable | Cible | Ce que ça vise |
|---|---|---|
| **bebecare.onrender.com** (code) | Grand public, 15 pays | Best Overall, Track 1 Santé |
| **BébéCare Terrain** (Momen) | Agents de santé communautaires | Prix Momen |

Et surtout : ce n'est pas un artifice. Les deux publics sont réellement
différents. Le site sert les parents. L'app Momen sert le soignant qui fait la
tournée de vaccination au village. C'est une histoire cohérente, pas un
remplissage.

---

## 2. Ce que l'app Momen doit faire

Quatre écrans. Rien de plus, le plan gratuit est limité.

```
Écran 1  Connexion agent          (auth native Momen)
Écran 2  Ma tournée du jour       (liste des enfants, base Momen)
Écran 3  Nouvel enfant + Agent IA (formulaire + agent de triage)
Écran 4  Transmettre au SNIS      (Actionflow -> API BébéCare -> DHIS2)
```

### Ce que ça démontre au juge Momen

| Capacité Momen | Où elle est utilisée |
|---|---|
| Base de données visuelle | Table `Enfant` et table `Tournee` |
| Design responsive | Écrans pensés pour un téléphone Android bas de gamme |
| **Agent IA** | Triage conversationnel avec outil externe |
| **API externe** | Appel de l'API BébéCare |
| **Actionflow** | Envoi groupé vers DHIS2 |
| Authentification | Comptes agents |

C'est exactement la liste des piliers de la plateforme : data, logic, design, AI.

---

## 3. Le plan gratuit, et comment tenir dedans

Le plan gratuit donne **1 API, 1 Actionflow, 1 agent IA**. C'est serré, donc le
découpage ci-dessous a été calculé pour rentrer pile dedans :

- **L'API (1)** → `POST /api/assistant` sur ton Render
- **L'Actionflow (1)** → `POST /api/dhis2/seance` sur ton Render
- **L'agent IA (1)** → l'agent de triage, qui utilise l'API ci-dessus comme outil

> Le Discord officiel du hackathon distribue **100 $ de crédits Momen** (500
> gagnants). Rejoins-le dès aujourd'hui, c'est de toute façon **obligatoire**
> pour participer.

---

## 4. La table de base de données

Momen → onglet **Data** → *New table* : `Enfant`

| Champ | Type Momen | Note |
|---|---|---|
| `prenom` | Text | Reste local, ne part jamais dans DHIS2 |
| `age_mois` | Integer | 0 à 60 |
| `sexe` | Enum | `m`, `f` |
| `village` | Text | |
| `vaccins` | Text (multi) | Codes : `BCG`, `PENTA1`… |
| `nutrition_code` | Enum | `MAS`, `MAM`, vide |
| `niveau_triage` | Enum | `rouge`, `orange`, `vert` |
| `transmis` | Boolean | Passe à vrai après l'Actionflow |
| `date_consultation` | Datetime | |

Deuxième table `Tournee` : `date`, `formation_sanitaire`, `org_unit_dhis2`,
`agent` (relation vers l'utilisateur).

---

## 5. L'API externe à déclarer

Momen → onglet **API** → *New API* → *REST*.

**Nom** : `BebeCareTriage`
**Méthode** : `POST`
**URL** : `https://bebecare.onrender.com/api/assistant`
**Header** : `Content-Type: application/json`

**Corps de la requête** (Request body) :

```json
{
  "texte": "{{texte}}",
  "age_mois": {{age_mois}},
  "pays": "bj"
}
```

**Réponse à mapper** — voici la structure réelle, vérifiée :

```json
{
  "decision": {
    "verdict": "urgence",
    "niveau": "rouge",
    "titre": "Allez au centre de santé MAINTENANT",
    "raisons": ["L'enfant ne peut ni boire ni téter", "Diarrhée"],
    "conseils": ["Partez maintenant vers le centre de santé le plus proche…"],
    "regles_appliquees": ["PCIME : tout signe général de danger…"],
    "source": "Algorithme dérivé de la PCIME (OMS/UNICEF), version conservatrice",
    "avertissement": "BébéCare n'est pas un diagnostic médical…"
  },
  "comprehension": {
    "signes_detectes": [{"code": "diarrhee", "confiance": 0.95}],
    "age_mois": 8,
    "duree_jours": 3
  },
  "ia": { "llm_utilise": true, "signes_ajoutes": ["ne_boit_pas"] }
}
```

Dans Momen, les champs à récupérer sont donc `decision.niveau`,
`decision.titre`, `decision.conseils`, `decision.raisons`.

### Tester avant de brancher

Colle ceci dans un terminal pour voir la réponse exacte :

```bash
curl -X POST https://bebecare.onrender.com/api/assistant \
  -H "Content-Type: application/json" \
  -d '{"texte":"bebe de 8 mois, diarrhee depuis 3 jours, ne tete plus","pays":"bj"}'
```

> Le CORS de l'API est ouvert (`allow_origins=["*"]`), Momen peut appeler sans
> réglage supplémentaire.

---

## 6. L'agent IA

Momen → onglet **AI** → *New Agent*. Nom : `Agent Terrain`.

### Prompt système (à copier tel quel)

```
Tu es l'assistant de terrain de BébéCare, utilisé par des agents de santé
communautaires en Afrique de l'Ouest pendant leurs tournées de vaccination.

TON RÔLE
Recueillir les symptômes d'un enfant de 0 à 5 ans en langage simple, puis
appeler l'outil BebeCareTriage pour obtenir la conduite à tenir.

RÈGLE ABSOLUE
Tu ne décides JAMAIS toi-même du niveau d'urgence. Le niveau vient uniquement
de l'outil BebeCareTriage, qui applique l'algorithme PCIME de l'OMS. Si l'outil
ne répond pas, dis-le honnêtement et conseille d'orienter vers le centre de
santé par prudence. N'invente jamais un verdict.

COMMENT TU PARLES
Phrases courtes. Vocabulaire simple. Pas de jargon médical. L'agent est souvent
debout, sous le soleil, sur un téléphone à petit écran.
Si l'utilisateur écrit en anglais, réponds en anglais.

CE QUE TU FAIS
1. Demande l'âge en mois si tu ne l'as pas.
2. Demande de décrire les symptômes avec ses mots.
3. Appelle BebeCareTriage avec le texte complet et l'âge.
4. Restitue le résultat dans cet ordre : le niveau (ROUGE, ORANGE ou VERT),
   le titre, puis les conseils sous forme de liste.
5. Termine toujours par : "BébéCare ne pose pas de diagnostic. En cas de doute,
   référez l'enfant."

CE QUE TU NE FAIS JAMAIS
- Nommer une maladie (pas de "c'est le paludisme").
- Proposer un médicament ou une posologie.
- Minimiser un signe de danger.
```

### Outil de l'agent

Dans la section *Tools* de l'agent, ajoute l'API `BebeCareTriage` créée à
l'étape 5. Description de l'outil :

```
Analyse les symptômes décrits d'un enfant de 0 à 5 ans et renvoie le niveau
d'urgence PCIME (rouge, orange, vert) avec les conseils officiels OMS.
À appeler dès que l'utilisateur a décrit des symptômes et donné un âge.
```

---

## 7. L'Actionflow de transmission

Momen → onglet **Logic** → *New Actionflow* : `TransmettreAuSNIS`

```
Déclencheur : bouton "Transmettre" sur l'écran 4
   |
1. Database Query
   Table Enfant, filtre : transmis = false
   |
2. Code / Transform  (assemblage du corps de requête)
   {
     "org_unit": <org_unit_dhis2 de la tournée>,
     "periode":  <année+mois du jour, format AAAAMM>,
     "consultations": [
       { "prenom": …, "age_mois": …, "vaccins": [...],
         "nutrition_code": … }
     ]
   }
   |
3. Third-party API call
   POST https://bebecare.onrender.com/api/dhis2/seance
   |
4. Condition
   Si validation.valide = true  ->  passer transmis = true
   Sinon                        ->  afficher les erreurs
   |
5. Afficher : "X enfants transmis, Y lignes DHIS2 générées"
```

Le champ à lire dans la réponse pour l'affichage final :
`resume.nb_lignes_dhis2` et `resume.doses_par_vaccin`.

---

## 8. Charte graphique, pour que ça ressemble à BébéCare

Reprends exactement les couleurs du site :

| Usage | Code |
|---|---|
| Vert principal | `#00695c` |
| Vert foncé (barres) | `#06322c` |
| Vert clair (fonds) | `#e0f2f1` |
| Fond de page | `#f6fbfa` |
| Ambre (accents) | `#e0a000` |
| Rouge (urgence) | `#e53935` |
| Vert (rassurant) | `#2e9e4f` |
| Texte | `#0f2b27` |
| Arrondi des cartes | 18 px |

Le logo est dans le ZIP : `web/public/logo-bebecare.png`.

Pour les niveaux de triage, garde le code couleur du site : pastille rouge,
orange ou verte, grande, en haut de la carte de résultat. Un agent doit
comprendre en une seconde.

---

## 9. Publier

Plan gratuit → publication sur un sous-domaine `*.momen.app` avec la marque
Momen. C'est **suffisant** pour le hackathon, et ça montre honnêtement que
l'app a été faite avec Momen.

Note l'URL publiée : elle ira sur la page Devpost, dans le champ
*Try it out links*, à côté de celle de Render.

---

## 10. Ce qu'il faut dire sur la page Devpost

Le juge Momen cherche une utilisation **substantielle**, pas décorative.
Formule proposée :

> **BébéCare Terrain** est l'application compagnon construite entièrement sur
> Momen, sans code, pour les agents de santé communautaires. Elle utilise la
> base de données visuelle de Momen pour le registre de tournée, un agent IA
> Momen pour le triage conversationnel, et un Actionflow Momen pour transmettre
> la séance de vaccination vers DHIS2, le système d'information sanitaire
> utilisé par plus de 80 pays.
>
> L'agent IA ne décide jamais seul : il appelle l'algorithme PCIME de l'OMS via
> un outil externe et se contente de restituer la décision. Momen nous a permis
> de livrer une seconde interface, destinée à un public totalement différent de
> celui du site grand public, en une journée au lieu d'une semaine.

Et dans la vidéo, consacre **40 à 50 secondes** à montrer l'app Momen en vrai,
sur un écran de téléphone. Pas une capture : un enregistrement où tu cliques.

---

## 11. Ordre de travail conseillé

| Jour | Tâche |
|---|---|
| J1 | Rejoindre le Discord (obligatoire) + récupérer les 100 $ de crédits |
| J1 | Déployer BébéCare sur Render (guide `DEPLOIEMENT.md`) |
| J2 | Momen : compte, tables `Enfant` et `Tournee`, écrans 1 et 2 |
| J3 | Momen : API `BebeCareTriage` + agent IA + écran 3 |
| J4 | Momen : Actionflow DHIS2 + écran 4 + charte graphique |
| J5 | Publier, tester sur un vrai téléphone |
| J6 | Vidéo et page Devpost |

Tu as jusqu'au **2 octobre 2026, 00 h 00 EDT**, soit **05 h 00 à Cotonou**.
Ne vise pas le dernier jour : Devpost sature.
