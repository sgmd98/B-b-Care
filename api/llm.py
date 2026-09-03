"""Etage LLM optionnel de l'assistant BebeCare.

ROLE EXACT DU MODELE DE LANGAGE
-------------------------------
Le LLM fait DEUX choses, et rien d'autre :

  1. EXTRACTION  : transformer une phrase libre de parent (mal orthographiee,
     melangeant francais, anglais, ou francais local) en une liste de codes
     cliniques normalises pris dans un vocabulaire FERME. Il ne peut pas
     inventer un signe : tout code hors vocabulaire est rejete par le code.

  2. REFORMULATION : reecrire les conseils deja decides par l'algorithme PCIME
     dans une langue simple et chaleureuse. On lui interdit d'ajouter,
     retirer ou nuancer une recommandation ; la sortie est verifiee.

CE QUE LE LLM NE FAIT JAMAIS
----------------------------
  - Il ne choisit pas le niveau d'urgence (rouge / orange / vert).
  - Il ne produit aucun diagnostic.
  - Il ne remplace jamais le moteur PCIME deterministe de triage.py.

Cette separation est volontaire : un modele de langage peut halluciner, un
arbre de decision de l'OMS ne le peut pas. Le LLM ameliore la COMPREHENSION,
la MACHINE garde la DECISION.

DEGRADATION GRACIEUSE
---------------------
Sans cle d'API, en cas de panne du fournisseur, de reponse invalide ou de
depassement du delai, tout retombe silencieusement sur le NLU local de
ia_triage.py. L'application n'est jamais bloquee par le LLM.

CONFIGURATION (variables d'environnement)
-----------------------------------------
  BEBECARE_LLM_FOURNISSEUR : "groq" (defaut) | "gemini" | "off"
  BEBECARE_LLM_CLE         : la cle d'API
  BEBECARE_LLM_MODELE      : facultatif, pour forcer un modele (desactive le repli)

CHAINES DE REPLI
----------------
Les fournisseurs retirent regulierement des modeles (ex. llama-3.3-70b-versatile
retire par Groq le 16/08/2026). Pour ne jamais tomber en panne, chaque
fournisseur a une liste ORDONNEE de modeles : si le premier echoue (modele
retire, quota, panne), on tente le suivant, et on retient celui qui a repondu
pour les appels suivants. Le triage PCIME local, lui, ne depend d'aucun modele.
"""
from __future__ import annotations

import json
import os
import re
import time

import httpx

FOURNISSEUR = os.environ.get("BEBECARE_LLM_FOURNISSEUR", "groq").strip().lower()
CLE = os.environ.get("BEBECARE_LLM_CLE", "").strip()
MODELE = os.environ.get("BEBECARE_LLM_MODELE", "").strip()
DELAI = float(os.environ.get("BEBECARE_LLM_DELAI", "8"))

# Listes ordonnees : premier = prefere, les suivants = replis automatiques.
MODELES_SECOURS = {
    "groq": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
}
# Dernier modele qui a repondu correctement (teste en premier ensuite).
_MODELE_RETENU: str | None = None

# Statistiques d'usage, exposees dans /api/assistant pour la transparence.
ETAT = {"appels": 0, "succes": 0, "echecs": 0, "dernier_echec": None, "ms_moyen": 0}


def actif() -> bool:
    return bool(CLE) and FOURNISSEUR in MODELES_SECOURS


def _candidats() -> list[str]:
    """Modeles a essayer, dans l'ordre. Le modele retenu passe en premier."""
    if MODELE:                                  # modele force : pas de repli
        return [MODELE]
    candidats = list(MODELES_SECOURS.get(FOURNISSEUR, []))
    if _MODELE_RETENU in candidats:
        candidats.remove(_MODELE_RETENU)
        candidats.insert(0, _MODELE_RETENU)
    return candidats


def statut() -> dict:
    return {
        "actif": actif(),
        "fournisseur": FOURNISSEUR if actif() else None,
        "modele": (_MODELE_RETENU or (_candidats() or [None])[0]) if actif() else None,
        "modeles_prevus": _candidats() if actif() else [],
        "role": "extraction et reformulation uniquement ; la decision reste PCIME",
        **ETAT,
    }


# --------------------------------------------------------------- APPEL BRUT

def _appel_brut(modele: str, systeme: str, utilisateur: str, json_attendu: bool) -> str:
    """Un seul appel HTTP vers `modele`. Leve une exception en cas d'echec."""
    if FOURNISSEUR == "groq":
        corps = {
            "model": modele,
            "messages": [
                {"role": "system", "content": systeme},
                {"role": "user", "content": utilisateur},
            ],
            "temperature": 0,
            "max_tokens": 1200,
        }
        if json_attendu:
            corps["response_format"] = {"type": "json_object"}
        # Les modeles gpt-oss raisonnent avant de repondre : on limite cet
        # effort pour garder reponses rapides et budget de tokens preserve.
        if modele.startswith("openai/gpt-oss"):
            corps["reasoning_effort"] = "low"
        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {CLE}"},
            json=corps, timeout=DELAI,
        )
        # Certains modeles refusent le mode JSON : repli sans response_format,
        # notre analyseur _json sait extraire un objet d'un texte libre.
        if r.status_code == 400 and json_attendu and "json" in r.text.lower():
            corps.pop("response_format", None)
            r = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {CLE}"},
                json=corps, timeout=DELAI,
            )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # gemini
    corps = {
        "system_instruction": {"parts": [{"text": systeme}]},
        "contents": [{"parts": [{"text": utilisateur}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 1200},
    }
    if json_attendu:
        corps["generationConfig"]["responseMimeType"] = "application/json"
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent",
        headers={"x-goog-api-key": CLE},
        json=corps, timeout=DELAI,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _appeler(systeme: str, utilisateur: str, json_attendu: bool = True) -> str | None:
    """Appel resilient : essaie les modeles dans l'ordre jusqu'a une reponse."""
    global _MODELE_RETENU
    if not actif():
        return None
    debut = time.time()
    ETAT["appels"] += 1
    erreurs: list[str] = []
    for modele in _candidats():
        try:
            texte = _appel_brut(modele, systeme, utilisateur, json_attendu)
        except Exception as exc:  # modele retire, quota, delai, cle invalide...
            erreurs.append(f"{modele} : {type(exc).__name__} {exc}"[:110])
            continue
        if texte and texte.strip():
            _MODELE_RETENU = modele
            ms = int((time.time() - debut) * 1000)
            ETAT["succes"] += 1
            ETAT["ms_moyen"] = int((ETAT["ms_moyen"] * (ETAT["succes"] - 1) + ms) / ETAT["succes"])
            return texte
        erreurs.append(f"{modele} : reponse vide")
    ETAT["echecs"] += 1
    ETAT["dernier_echec"] = ("aucun modele disponible : " + " ; ".join(erreurs))[:240]
    return None


def _json(texte: str | None) -> dict | None:
    if not texte:
        return None
    try:
        return json.loads(texte)
    except Exception:
        bloc = re.search(r"\{.*\}", texte, re.S)
        if bloc:
            try:
                return json.loads(bloc.group(0))
            except Exception:
                return None
    return None


# ------------------------------------------------------- 1. EXTRACTION

SYSTEME_EXTRACTION = """Tu es un module d'extraction clinique pour un service de sante infantile en Afrique de l'Ouest.
Tu ne poses AUCUN diagnostic et tu ne donnes AUCUN conseil. Tu extrais uniquement des faits.

Le parent ecrit en francais, en anglais, ou en francais local, souvent avec des fautes.

Tu renvoies STRICTEMENT un objet JSON avec ces cles :
{
  "signes": [{"code": "<code du vocabulaire>", "extrait": "<les mots exacts du parent>", "confiance": 0.0-1.0}],
  "signes_nies": ["<codes explicitement nies par le parent>"],
  "age_mois": <nombre ou null>,
  "temperature_c": <nombre ou null>,
  "frequence_respiratoire": <entier ou null>,
  "duree_jours": <entier ou null>,
  "langue": "fr" ou "en"
}

VOCABULAIRE FERME : tu ne peux utiliser QUE ces codes, aucun autre.
%(vocabulaire)s

REGLES ABSOLUES :
- Un code absent de la liste est interdit. Dans le doute, n'extrais rien.
- "extrait" doit reprendre les mots reels du parent, jamais une reformulation.
- Une negation ("il ne vomit pas", "pas de fievre") va dans "signes_nies", jamais dans "signes".
- Une temperature "chaud au toucher" sans chiffre : temperature_c reste null.
- Convertis les ages : "2 ans" -> 24, "6 semaines" -> 1.4, "nouveau-ne" -> 0.5.
- confiance 0.9+ si le parent l'ecrit clairement, 0.6-0.8 si c'est une deduction.
"""

LIBELLES = {
    "convulsions": "convulsions / crises",
    "ne_boit_pas": "incapable de boire ou de teter",
    "vomit_tout": "vomit absolument tout ce qu'il avale",
    "lethargie": "lethargique, inconscient, ne reagit pas",
    "respiration_difficile": "respiration difficile, tirage, battement des ailes du nez",
    "geignement": "geint a chaque respiration",
    "cyanose": "levres ou extremites bleues",
    "yeux_creux": "yeux enfonces, pli cutane persistant (deshydratation severe)",
    "sang_selles": "sang dans les selles",
    "raideur_nuque": "nuque raide",
    "oedemes": "gonflement des deux pieds (oedemes)",
    "fontanelle_bombee": "fontanelle bombee",
    "eruption_generalisee": "eruption cutanee generalisee",
    "diarrhee": "diarrhee",
    "diarrhee_3j": "diarrhee depuis 3 jours ou plus",
    "vomissements": "vomissements",
    "toux_14j": "toux depuis 14 jours ou plus",
    "fievre_7j": "fievre depuis 7 jours ou plus",
    "oreille_ecoulement": "ecoulement de l'oreille",
    "refus_manger": "refuse de manger",
    "pales": "paleur des paumes ou des conjonctives",
    "eruption": "eruption cutanee localisee",
    "amaigrissement": "amaigrissement visible",
    "pleurs_inhabituels": "pleurs inhabituels, incessants",
}


def _vocabulaire(codes) -> str:
    return "\n".join(f'- "{c}" : {LIBELLES.get(c, c)}' for c in codes)


def extraire(texte: str, codes_autorises) -> dict | None:
    """Etage 1 par LLM. Renvoie None si indisponible ou invalide."""
    if not actif() or not texte.strip():
        return None

    systeme = SYSTEME_EXTRACTION % {"vocabulaire": _vocabulaire(codes_autorises)}
    brut = _json(_appeler(systeme, texte.strip()))
    if not isinstance(brut, dict):
        return None

    autorises = set(codes_autorises)

    signes = []
    for s in brut.get("signes") or []:
        if not isinstance(s, dict):
            continue
        code = str(s.get("code", "")).strip()
        if code not in autorises:           # garde-fou : vocabulaire ferme
            continue
        try:
            conf = float(s.get("confiance", 0.8))
        except (TypeError, ValueError):
            conf = 0.8
        signes.append({
            "code": code,
            "expression": str(s.get("extrait", ""))[:120] or code,
            "confiance": max(0.0, min(1.0, conf)),
        })

    def nombre(cle, mini, maxi, entier=False):
        v = brut.get(cle)
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not (mini <= v <= maxi):         # garde-fou : plages physiologiques
            return None
        return int(v) if entier else v

    return {
        "signes": signes,
        "signes_nies": [c for c in (brut.get("signes_nies") or []) if c in autorises],
        "age_mois": nombre("age_mois", 0, 60),
        "temp_c": nombre("temperature_c", 30, 45),
        "freq_resp": nombre("frequence_respiratoire", 10, 120, entier=True),
        "duree_jours": nombre("duree_jours", 0, 365, entier=True),
        "langue": "en" if str(brut.get("langue", "fr")).lower().startswith("en") else "fr",
    }


# --------------------------------------------------- 2. REFORMULATION

SYSTEME_REFORMULATION = """Tu reformules des consignes de sante deja validees par un algorithme medical de l'OMS.

INTERDICTIONS ABSOLUES :
- Ne change JAMAIS le niveau d'urgence.
- N'ajoute AUCUN conseil qui ne figure pas dans la liste fournie.
- Ne retire AUCUN conseil de la liste.
- Ne propose aucun medicament, aucune posologie, aucun diagnostic.

TA SEULE TACHE : reecrire chaque consigne dans une langue simple, directe et
rassurante, comprehensible par un parent qui n'a pas fait d'etudes. Phrases
courtes. Tutoiement interdit, vouvoiement. Pas de jargon medical.

Tu renvoies STRICTEMENT ce JSON :
{"conseils": ["<consigne 1 reformulee>", "<consigne 2 reformulee>", ...]}

La liste renvoyee doit contenir EXACTEMENT le meme nombre d'elements, dans le
meme ordre, que la liste recue.
"""


def reformuler(conseils: list[str], niveau: str, langue: str = "fr") -> list[str] | None:
    """Etage 3 par LLM. Renvoie None si indisponible ou si le controle echoue."""
    if not actif() or not conseils:
        return None

    demande = json.dumps({
        "langue_de_sortie": "francais" if langue == "fr" else "anglais",
        "niveau_urgence": niveau,
        "conseils": conseils,
    }, ensure_ascii=False)

    brut = _json(_appeler(SYSTEME_REFORMULATION, demande))
    if not isinstance(brut, dict):
        return None

    sortie = brut.get("conseils")
    # Controle : meme nombre d'elements, que du texte, longueur raisonnable.
    if (not isinstance(sortie, list)
            or len(sortie) != len(conseils)
            or not all(isinstance(c, str) and 3 < len(c) < 400 for c in sortie)):
        ETAT["echecs"] += 1
        ETAT["dernier_echec"] = "reformulation rejetee par le controle de conformite"
        return None

    return [c.strip() for c in sortie]


# --------------------------------------------------------------- CONVERSATION

SYSTEME_QUESTION = """Tu es l'assistant de BebeCare, une plateforme gratuite de sante de
l'enfant de 0 a 5 ans utilisee dans les 15 pays de la CEDEAO (Afrique de l'Ouest).
Tu reponds aux questions des parents sur la sante, l'alimentation, le sommeil,
le developpement, l'hygiene et la vaccination de leur enfant.

TON CADRE
- Tu es un assistant d'information, pas un medecin.
- Tu ne poses JAMAIS de diagnostic. Tu ne nommes jamais une maladie precise
  pour l'enfant de l'utilisateur.
- Tu ne donnes JAMAIS de medicament ni de posologie, meme pour du paracetamol.
- Si la question decrit des symptomes inquietants, tu ne tranches pas toi-meme :
  tu invites a utiliser l'onglet Assistant de triage de BebeCare et, en cas de
  doute, a consulter.
- Si la question sort de la sante de l'enfant de 0 a 5 ans, tu le dis avec
  bienveillance et tu ramenes vers ce que BebeCare sait faire.

TON CONTEXTE
Tu t'adresses a des parents d'Afrique de l'Ouest. Tes exemples d'aliments, de
pratiques et de recours aux soins doivent etre realistes pour cette region :
bouillie de mil ou de mais enrichie, arachide, niebe, moringa, poisson fume,
mangue, papaye, centre de sante, agent de sante communautaire. Ne propose pas
d'aliments ou de services indisponibles sur place.

TA FORME
- Reponds dans la langue de la question. Francais si la question est en
  francais, anglais si elle est en anglais.
- 120 mots maximum. Phrases courtes.
- Va droit au but. Pas de preambule du type "Bonne question".
- Termine par une seule phrase de prudence, courte, adaptee au sujet.
"""


def repondre_question(question: str, pays: str | None = None,
                      age_mois: float | None = None,
                      historique: list | None = None) -> dict | None:
    """Reponse conversationnelle libre. Renvoie None si le LLM est indisponible.

    Cette fonction ne decide jamais d'un niveau d'urgence : le triage reste le
    role de triage.py. Elle sert aux questions du quotidien, celles pour
    lesquelles un formulaire de triage n'a aucun sens.
    """
    if not actif():
        return None

    contexte = []
    if pays:
        contexte.append(f"Pays de l'utilisateur : {pays}.")
    if age_mois is not None:
        contexte.append(f"Age de l'enfant : {age_mois} mois.")
    if historique:
        derniers = historique[-4:]
        echanges = "\n".join(
            f"{'Parent' if m.get('role') == 'user' else 'Assistant'} : {m.get('texte', '')[:300]}"
            for m in derniers)
        contexte.append("Echanges precedents :\n" + echanges)

    invite = "\n".join(contexte + [f"Question du parent : {question}"])
    texte = _appeler(SYSTEME_QUESTION, invite, json_attendu=False)
    if not texte:
        return None

    texte = texte.strip()
    # Garde-fou de longueur : une reponse fleuve trahit un modele parti en roue libre.
    if len(texte) < 10 or len(texte) > 2000:
        ETAT["dernier_echec"] = "reponse conversationnelle hors limites"
        return None

    return {"reponse": texte, "modele": _MODELE_RETENU or (_candidats() or [None])[0],
            "fournisseur": FOURNISSEUR}
