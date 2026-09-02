# Mettre BébéCare en ligne

Guide en français, du ZIP jusqu'au site public. Compte environ **45 minutes** la
première fois. Tout ce qui est utilisé ici est gratuit.

Ordre à respecter :

1. Installer le projet en local et vérifier qu'il tourne
2. Créer la base Neon (5 min)
3. Créer la clé IA gratuite (5 min)
4. Pousser sur GitHub
5. Déployer sur Render
6. Vérifier le site en ligne

---

## Étape 1 : installer et vérifier en local

### 1.1 Décompresser

Le fichier `bebecare-v2.10.zip` est dans **Téléchargements**.

```bash
cd ~/Téléchargements
unzip -o bebecare-v2.10.zip
```

Tu as déjà un dossier `~/bebecare` de la version précédente. On le remplace en
gardant une sauvegarde :

```bash
cd ~
mv bebecare bebecare-sauvegarde-$(date +%Y%m%d-%H%M)
mv ~/Téléchargements/bebecare ~/bebecare
cd ~/bebecare
```

### 1.2 Lancer l'API — terminal 1

```bash
cd ~/bebecare
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000
```

Laisse ce terminal ouvert. Il ne rend jamais la main, c'est normal.

### 1.3 Lancer le site — terminal 2

Ouvre un nouvel onglet avec **Ctrl+Shift+T**.

```bash
cd ~/bebecare/web
npm install
npm run dev
```

Ouvre **http://localhost:5173**.

### 1.4 Vérifier — terminal 3

```bash
curl http://localhost:8000/api/sante
```

Tu dois voir `"moteur": "sqlite"`. En local c'est normal : Neon ne sert qu'en
ligne.

À tester dans le navigateur avant d'aller plus loin :

- **Carte** : les pastilles vertes s'affichent, pas de filigrane sur les tuiles
- **Assistant IA** : tape *« mon bébé de 8 mois a la diarrhée depuis 3 jours et ne veut plus téter »* → verdict rouge
- **Mode soignant** : ajoute deux enfants, clique *Préparer l'envoi DHIS2* → le JSON s'affiche
- **Nigeria** dans le sélecteur de pays → l'interface passe en anglais

---

## Étape 2 : la base de données Neon

Sur Render, le disque est effacé à chaque redéploiement. Sans base externe, tous
les comptes créés disparaîtraient. Neon est du PostgreSQL gratuit et permanent.

1. Va sur **https://neon.tech** → *Sign up* (connexion par GitHub, le plus rapide).
2. *Create project* :
   - **Name** : `bebecare`
   - **Postgres version** : la version proposée par défaut
   - **Region** : `Europe (Frankfurt)` — la même que Render, pour la latence
3. À la création, Neon affiche la **Connection string**. Clique *Copy*.

Elle ressemble à ceci :

```
postgresql://neondb_owner:XXXXXXXX@ep-cool-name-12345.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

**Copie-la dans un fichier texte, tu en auras besoin à l'étape 5.** Si tu la
perds : dashboard Neon → *Connection Details* → *Show password*.

> Tu n'as **aucune table à créer**. BébéCare crée son schéma tout seul au premier
> démarrage.

### Tester Neon depuis ton PC (facultatif mais conseillé)

```bash
cd ~/bebecare
source .venv/bin/activate
export DATABASE_URL="colle_ici_ta_chaine_neon"
python3 -c "
import sys; sys.path.insert(0,'.')
from api import comptes, bd
comptes.initialiser()
print('Moteur :', bd.description())
print('Tables créées, base prête.')
"
```

Tu dois lire `'moteur': 'postgresql'`. Si oui, Neon est bon.

---

## Étape 3 : la clé IA gratuite

L'assistant fonctionne sans clé. Avec une clé, il comprend les phrases mal
écrites et répond dans la langue du parent. **Groq** est le plus généreux et le
plus rapide.

1. Va sur **https://console.groq.com** → *Sign up* (GitHub ou Google).
2. Menu **API Keys** → *Create API Key* → nom : `bebecare`.
3. Copie la clé (elle commence par `gsk_...`). **Elle ne sera plus jamais
   réaffichée**, garde-la dans ton fichier texte.

### Tester la clé en local

```bash
cd ~/bebecare
source .venv/bin/activate
export BEBECARE_LLM_FOURNISSEUR=groq
export BEBECARE_LLM_CLE="gsk_ta_cle_ici"
python3 -c "
import sys; sys.path.insert(0,'.')
from api import ia_triage as t
r = t.repondre('mon petit de 8 mwa il fé la diare depui 3 jour é il tet plu', pays='bj')
print('Niveau  :', r['decision']['niveau'])
print('Signes  :', [s['code'] for s in r['comprehension']['signes_detectes']])
print('LLM     :', r['ia']['llm_utilise'], '| ajoutés par le LLM :', r['ia']['signes_ajoutes'])
print('Conseil :', r['decision']['conseils'][0][:90])
"
```

Si `LLM : True`, l'étage IA fonctionne. Si `False`, vérifie la clé — mais le site
marche quand même, il retombe sur le moteur local.

> **Alternative Gemini** : clé sur https://aistudio.google.com/apikey, puis
> `BEBECARE_LLM_FOURNISSEUR=gemini`.

---

## Étape 4 : GitHub

Ton dépôt existe déjà : **https://github.com/sgmd98/B-b-Care**. Il contient la
v0.1 (dossier `front/`, 4 pays). On y pousse la v2.10, qui a une structure
différente (dossier `web/`, 15 pays). Il faut donc **remplacer** le contenu, pas
l'empiler.

> Au passage : le nom `B-b-Care` vient d'une conversion automatique des accents
> par GitHub. Tu peux le renommer proprement en `bebecare` dans
> *Settings → Repository name → Rename*. GitHub redirige automatiquement
> l'ancienne URL, rien ne casse. Fais-le maintenant si tu veux, avant de
> connecter Render.

### 4.1 Récupérer l'historique existant

```bash
cd ~/bebecare
git init
git config user.name "SOSSA Darius"
git config user.email "sante.infantile.benin@gmail.com"
git remote add origin https://github.com/sgmd98/B-b-Care.git
git fetch origin
```

### 4.2 Écraser proprement l'ancienne version

Cette commande place ton nouveau code par-dessus l'historique existant. Le
commit v0.1 reste dans l'historique, mais l'arborescence devient celle de la
v2.10 : l'ancien dossier `front/` disparaît.

```bash
git checkout -b main
git add -A
git commit -m "v2.10 : 15 pays CEDEAO, IA hybride 3 etages, mode soignant DHIS2, Neon"
git merge origin/main --allow-unrelated-histories -X ours -m "Remplacement de la v0.1 par la v2.10"
git push -u origin main
```

Si Git ouvre un éditeur de message pendant le `merge`, appuie sur
**Ctrl+X** (nano) ou tape **:wq** puis Entrée (vim).

> **Si GitHub refuse ton mot de passe** : c'est normal, ils ne les acceptent plus.
> Va dans *Settings → Developer settings → Personal access tokens → Tokens
> (classic) → Generate new token (classic)*, coche la case **repo**, génère, puis
> colle le token à la place du mot de passe.

### 4.3 Vérifier que tout est bon

```bash
git ls-files | grep -E "^front/" && echo "ATTENTION : ancien dossier encore la" || echo "Ancien front/ bien supprime."
git ls-files | grep -E "\.env|\.db$" || echo "Aucun secret dans le depot."
```

Le `.gitignore` exclut déjà `node_modules`, `web/dist`, `.venv` et les bases.
**Aucune clé n'est écrite dans le code** : tout passe par les variables
d'environnement de Render.

Ouvre https://github.com/sgmd98/B-b-Care et vérifie que tu vois bien `api/`,
`web/`, `data/`, `docs/` et le nouveau README.

## Étape 5 : Render

### 5.1 Créer le service

1. **https://dashboard.render.com** → *New +* → **Blueprint**
2. *Connect account* si c'est ta première fois, puis choisis `sgmd98/B-b-Care`
3. Render lit `render.yaml` et propose le service **bebecare** → *Apply*

### 5.2 Ajouter les secrets

Render va te demander `DATABASE_URL` (déclarée en `sync: false`). Colle ta
chaîne Neon.

Ensuite, service **bebecare** → onglet **Environment** → *Add Environment
Variable*, deux fois :

| Key | Value |
|---|---|
| `BEBECARE_LLM_FOURNISSEUR` | `groq` |
| `BEBECARE_LLM_CLE` | ta clé `gsk_...` |

*Save changes* : Render redéploie automatiquement.

### 5.3 Attendre le build

Onglet **Logs**. Le premier déploiement prend **5 à 8 minutes** (installation de
Node, puis build Vite). Tu dois finir sur :

```
Application startup complete.
Your service is live 🎉
```

### Variables déjà dans `render.yaml`, rien à faire

| Variable | Valeur | Rôle |
|---|---|---|
| `BEBECARE_SECRET` | générée par Render | Signature des sessions |
| `BEBECARE_DHIS2_URL` | démo publique DHIS2 | Instance interrogée |
| `BEBECARE_DHIS2_USER` / `_PASSWORD` | `admin` / `district` | Identifiants publics de la démo |
| `BEBECARE_DHIS2_PUSH` | `0` | **Écriture DHIS2 verrouillée** |

---

## Étape 6 : vérifier le site en ligne

Ton URL sera `https://bebecare.onrender.com` (ou le nom que Render a attribué).

```bash
curl https://bebecare.onrender.com/api/sante
```

Trois choses à contrôler dans la réponse :

- `"statut": "ok"`
- `"structures_sante": 23568`
- `"base": {"moteur": "postgresql", ...}` ← **Neon est bien branché**

Puis :

```bash
curl https://bebecare.onrender.com/api/assistant/statut
```

`"actif": true` signifie que la clé IA est reconnue.

Enfin, dans le navigateur :

1. Crée un compte → déconnecte-toi → reconnecte-toi (valide Neon)
2. Ouvre la carte, zoome sur Cotonou
3. Teste l'assistant avec une phrase mal écrite
4. Mode soignant : deux enfants, *Préparer l'envoi DHIS2*

---

## Le piège du plan gratuit : la mise en veille

Un service gratuit Render s'endort après **15 minutes** sans visite, et met
**environ 50 secondes** à se réveiller. Si un juge ouvre ton lien à ce
moment-là, il voit une page blanche et il s'en va.

**Deux protections :**

1. **Un réveil automatique.** Crée un compte gratuit sur
   https://uptimerobot.com → *Add New Monitor* → type **HTTP(s)** → URL
   `https://bebecare.onrender.com/api/sante` → intervalle **5 minutes**. Le
   service ne dort plus jamais.
2. **Le jour de la démo**, ouvre le site 3 minutes avant d'enregistrer.

---

## Mettre à jour ensuite

```bash
cd ~/bebecare
git add -A
git commit -m "description de la correction"
git push
```

Render redéploie tout seul en 3 à 5 minutes.

---

## Si ça casse

| Symptôme | Cause probable | Solution |
|---|---|---|
| Build échoue sur `npm ci` | `package-lock.json` absent du dépôt | `git add -f web/package-lock.json && git commit && git push` |
| `"moteur": "sqlite"` en ligne | `DATABASE_URL` non enregistrée | Render → Environment, vérifier la variable, *Save changes* |
| Erreur `SSL required` au démarrage | `?sslmode=require` manquant | Le rajouter à la fin de la chaîne Neon |
| `"actif": false` sur `/api/assistant/statut` | Clé Groq absente ou invalide | Régénérer la clé, la recoller dans Render |
| Assistant lent (3 s et plus) | Réveil du service, ou latence LLM | Normal au réveil. Sinon baisser `BEBECARE_LLM_DELAI` |
| Page blanche au premier chargement | Service endormi | Attendre 50 s, puis mettre UptimeRobot en place |

---

## Ce qu'il y a dans le projet

```
bebecare/
├── api/
│   ├── main.py             Toutes les routes REST
│   ├── ia_triage.py        Étage 1 : NLU local + fusion avec le LLM
│   ├── llm.py              Étage LLM optionnel, avec ses garde-fous
│   ├── triage.py           Étage 2 : PCIME OMS, la décision, 100 % déterministe
│   ├── comptes.py          Comptes, mots de passe, jetons de session
│   ├── bd.py               SQLite en local, PostgreSQL/Neon en ligne
│   ├── croissance.py       Z-scores OMS
│   └── dhis2.py            Passerelle DHIS2 + agrégation du mode soignant
├── web/src/
│   ├── sib.css             Le design system
│   ├── App.jsx             Navigation, pied de page, routage
│   └── pages/Soignant.jsx  Le mode soignant
├── data/                   Données OMS et OpenStreetMap
├── README.md               Présentation en français
├── README.en.md            Présentation en anglais (pour les juges)
└── render.yaml             Configuration du déploiement
```

---

## Étape 7 : l'application Momen (pour le prix no-code)

Une fois Render en ligne, tu as l'URL dont l'app Momen a besoin. Enchaîne avec
**`docs/MOMEN.md`** : il contient la structure des tables, l'URL et le corps
exact de l'API à déclarer, le prompt système de l'agent IA, le schéma de
l'Actionflow DHIS2 et la charte graphique.

Compte 3 à 4 heures. C'est ce qui te qualifie pour les 2 000 $ du track Momen,
et ça ne t'enlève aucun autre prix.

Avant tout ça, lis **`docs/CHECKLIST_HACKATHON.md`** : il y a un point
d'éligibilité à vérifier en priorité.
