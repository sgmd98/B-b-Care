"""Assistant IA de triage pediatrique.

ARCHITECTURE : IA hybride "NLU + moteur deterministe".

Pourquoi pas un simple LLM ? Parce qu'en pediatrie, un modele generatif peut
halluciner un conseil dangereux, et rien ne garantit la reproductibilite d'une
reponse. La conception retenue separe donc deux etages :

  ETAGE 1 - COMPREHENSION (IA)
    Un moteur de comprehension du langage naturel bilingue FR/EN transforme la
    phrase libre d'un parent ("mon bebe de 8 mois a la diarhee depuis 2 jours et
    il ne tete plus") en signes cliniques structures. Il gere :
      - la normalisation et les fautes d'orthographe (distance de Levenshtein)
      - les tournures locales ouest-africaines
      - la NEGATION ("il n'a pas de fievre" ne doit pas declencher "fievre")
      - l'extraction numerique (age, temperature, duree, frequence respiratoire)
      - un score de confiance par signe detecte

  ETAGE 2 - DECISION (deterministe, verifiable)
    Les signes extraits alimentent le moteur PCIME de l'OMS (api/triage.py).
    La decision clinique n'est JAMAIS produite par l'IA : elle est produite par
    un algorithme publie, auditable, et testable.

  ETAGE 3 - DIALOGUE
    Si une information critique manque (age, signes de danger), l'assistant pose
    la question qui fait le plus basculer la decision - comme un infirmier
    d'accueil qui trie.

Resultat : la souplesse du langage naturel, avec la securite d'un protocole OMS.
"""
from __future__ import annotations

import re
import unicodedata

from . import llm
from . import triage as pcime

# --------------------------------------------------------------- LEXIQUE
# Chaque signe -> expressions FR, EN et tournures locales.
LEXIQUE: dict[str, list[str]] = {
    # --- signes generaux de danger (PCIME)
    "convulsions": ["convulsion", "convulsions", "crise convulsive", "tremble tout le corps",
                    "raidit et tremble", "epilepsie", "convulsing", "seizure", "fits",
                    "shaking all over", "corps se raidit"],
    "ne_boit_pas": ["ne boit pas", "ne bois pas", "refuse de boire", "ne tete plus",
                    "ne tete pas", "n'arrive pas a teter", "ne peut pas boire",
                    "refuse le sein", "not drinking", "cannot drink", "refuses breast",
                    "unable to breastfeed", "ne veut plus teter"],
    "vomit_tout": ["vomit tout", "vomit tout ce qu'il mange", "rejette tout",
                   "vomits everything", "throws up everything", "vomit apres chaque tetee"],
    "lethargie": ["lethargique", "inconscient", "ne reagit plus", "ne repond pas",
                  "tres faible", "sans force", "endormi tout le temps", "mou",
                  "ne bouge plus", "lethargic", "unconscious", "unresponsive",
                  "very weak", "floppy", "sleeps all the time", "abattu"],
    "respiration_difficile": ["respiration difficile", "difficulte a respirer",
                              "respire mal", "essouffle", "tirage", "cotes qui rentrent",
                              "thorax se creuse", "manque d'air", "difficulty breathing",
                              "chest indrawing", "labored breathing", "struggling to breathe",
                              "respire vite et fort"],
    "geignement": ["geint", "geignement", "gemit", "bruit en respirant", "sifflement",
                   "grunting", "stridor", "wheezing", "il grogne en respirant"],
    "cyanose": ["levres bleues", "bleu autour de la bouche", "paumes bleues",
                "devient bleu", "blue lips", "bluish", "cyanosis"],
    "yeux_creux": ["yeux enfonces", "yeux creux", "pli cutane", "peau qui reste plissee",
                   "deshydrate", "sunken eyes", "skin pinch", "dehydrated",
                   "yeux dans les orbites"],
    "sang_selles": ["sang dans les selles", "selles sanglantes", "sang quand il fait caca",
                    "dysenterie", "blood in stool", "bloody diarrhea", "bloody stool"],
    "raideur_nuque": ["nuque raide", "raideur de la nuque", "cou raide",
                      "n'arrive pas a baisser la tete", "stiff neck", "neck stiffness"],
    "oedemes": ["pieds gonfles", "jambes gonflees", "oedeme", "oedemes", "enfle",
                "gonflement des pieds", "swollen feet", "swelling", "edema"],
    "fontanelle_bombee": ["fontanelle bombee", "fontanelle gonflee", "bulging fontanelle",
                          "dessus de la tete gonfle"],
    "eruption_generalisee": ["eruption partout", "boutons partout avec fievre",
                             "rougeole", "taches rouges partout", "measles",
                             "rash all over", "generalized rash"],

    # --- symptomes courants
    "diarrhee": ["diarrhee", "diarhee", "diaree", "selles liquides", "sels liquides",
                 "va souvent aux toilettes", "sels molles", "ventre coule",
                 "diarrhea", "diarrhoea", "loose stools", "watery stool", "la courante"],
    "diarrhee_3j": ["diarrhee depuis 3 jours", "diarrhee depuis plusieurs jours",
                    "diarrhee depuis une semaine", "diarrhea for 3 days",
                    "diarrhee qui dure"],
    "vomissements": ["vomit", "vomissement", "vomissements", "il rend", "regurgite beaucoup",
                     "vomiting", "throwing up", "nausea"],
    "toux_14j": ["toux depuis 2 semaines", "toux depuis longtemps", "tousse depuis 14 jours",
                 "toux chronique", "cough for two weeks", "chronic cough",
                 "tousse depuis un mois"],
    "fievre_7j": ["fievre depuis une semaine", "fievre depuis 7 jours",
                  "fievre qui ne passe pas", "fievre depuis longtemps",
                  "fever for a week", "persistent fever"],
    "oreille_ecoulement": ["oreille coule", "pus dans l'oreille", "ecoulement oreille",
                           "mal aux oreilles", "ear discharge", "pus from ear", "otite"],
    "refus_manger": ["ne mange pas", "refuse de manger", "n'a pas d'appetit",
                     "ne veut rien manger", "not eating", "refuses food", "no appetite"],
    "pales": ["paumes pales", "tres pale", "blanc", "anemie", "pale palms", "anemia",
              "yeux blancs"],
    "eruption": ["boutons", "eruption", "plaques sur la peau", "rash", "skin spots",
                 "demangeaisons"],
    "amaigrissement": ["maigrit", "a maigri", "perd du poids", "tres maigre",
                       "losing weight", "wasted", "il fond"],
    "pleurs_inhabituels": ["pleure sans arret", "pleure beaucoup", "cris inhabituels",
                           "crying nonstop", "inconsolable", "ne dort plus a force de pleurer"],
}

# Marqueurs de negation, compares en MOTS ENTIERS.
# Piege corrige : chercher la sous-chaine "ne " declenchait a tort sur
# "u-ne semaine" et niait le signe suivant.
NEGATIONS = {"pas", "aucun", "aucune", "sans", "jamais", "ne", "n'a", "ni",
             "no", "not", "without", "never", "denies", "nothing", "n'est"}

PORTEE_NEGATION = 5  # mots precedant l'expression


# ---------------------------------------------------------- NORMALISATION

def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte)
                   if unicodedata.category(c) != "Mn")


def normaliser(texte: str) -> str:
    t = sans_accents(texte.lower())
    t = re.sub(r"[^\w\s',.°-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def levenshtein(a: str, b: str, plafond: int = 2) -> int:
    """Distance d'edition bornee (tolerance aux fautes de frappe)."""
    if abs(len(a) - len(b)) > plafond:
        return plafond + 1
    precedent = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        courant = [i]
        for j, cb in enumerate(b, 1):
            courant.append(min(precedent[j] + 1, courant[j - 1] + 1,
                               precedent[j - 1] + (ca != cb)))
        precedent = courant
        if min(precedent) > plafond:
            return plafond + 1
    return precedent[-1]


def _mot_approche(mot: str, cible: str) -> bool:
    """Correspondance floue : tolerance 1 faute a partir de 5 lettres, 2 a partir de 8."""
    if mot == cible:
        return True
    if len(cible) < 5:
        return False
    plafond = 1 if len(cible) < 8 else 2
    return levenshtein(mot, cible, plafond) <= plafond


def _expression_presente(texte_norm: str, mots: list[str], expression: str) -> bool:
    exp = normaliser(expression)
    if exp in texte_norm:
        return True
    # correspondance floue mot a mot pour les expressions d'un seul mot
    cibles = exp.split()
    if len(cibles) == 1:
        return any(_mot_approche(m, cibles[0]) for m in mots)
    # expression multi-mots : tous les mots presents (flou) dans une fenetre
    positions = []
    for cible in cibles:
        pos = [i for i, m in enumerate(mots) if _mot_approche(m, cible)]
        if not pos:
            return False
        positions.append(pos)
    # fenetre de 6 mots
    for depart in positions[0]:
        if all(any(depart <= p <= depart + 6 for p in pos) for pos in positions[1:]):
            return True
    return False


def _est_nie(texte_norm: str, expression: str) -> bool:
    """Negation detectee uniquement sur des MOTS ENTIERS, dans les N mots
    qui precedent l'expression, et sans franchir une conjonction ('et', 'mais')
    qui ouvre une nouvelle proposition."""
    exp = normaliser(expression)
    idx = texte_norm.find(exp)
    if idx < 0:
        return False
    avant = texte_norm[:idx].split()
    fenetre = []
    for mot in reversed(avant[-PORTEE_NEGATION:]):
        if mot in ("et", "mais", "and", "but", "puis", "然"):
            break
        fenetre.append(mot.strip(",.';"))
    return any(m in NEGATIONS for m in fenetre)


# ------------------------------------------------------------- EXTRACTION

def extraire_age_mois(texte_norm: str) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(mois|month|months)", texte_norm)
    if m:
        return float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ans?|years?|yrs?)", texte_norm)
    if m:
        return float(m.group(1).replace(",", ".")) * 12
    m = re.search(r"(\d+)\s*(semaines?|weeks?)", texte_norm)
    if m:
        return int(m.group(1)) * 7 / 30.4375
    m = re.search(r"(\d+)\s*(jours?|days?)\s*(de vie|old|d'age)", texte_norm)
    if m:
        return int(m.group(1)) / 30.4375
    if re.search(r"nouveau ?ne|newborn|nouvo ne", texte_norm):
        return 0.5
    return None


def extraire_temperature(texte_norm: str) -> float | None:
    for m in re.finditer(r"(\d{2}(?:[.,]\d)?)\s*(?:°|degre|degres|deg|c\b|celsius)",
                         texte_norm):
        v = float(m.group(1).replace(",", "."))
        if 33 <= v <= 44:
            return v
    m = re.search(r"(?:temperature|temp|fievre de|fever of)\D{0,6}(\d{2}(?:[.,]\d)?)",
                  texte_norm)
    if m:
        v = float(m.group(1).replace(",", "."))
        if 33 <= v <= 44:
            return v
    return None


def extraire_frequence_resp(texte_norm: str) -> int | None:
    m = re.search(r"(\d{2,3})\s*(?:respirations?|mouvements?|breaths?)"
                  r"(?:\s*(?:par|\/|per)\s*(?:min|minute))?", texte_norm)
    if m:
        v = int(m.group(1))
        if 10 <= v <= 140:
            return v
    return None


def extraire_duree_jours(texte_norm: str) -> int | None:
    m = re.search(r"depuis\s*(\d+)\s*(jours?|days?)", texte_norm)
    if m:
        return int(m.group(1))
    m = re.search(r"(?:for|since)\s*(\d+)\s*days?", texte_norm)
    if m:
        return int(m.group(1))
    if re.search(r"depuis\s*(une|1)\s*semaine|for a week", texte_norm):
        return 7
    if re.search(r"depuis\s*(deux|2)\s*semaines|for two weeks", texte_norm):
        return 14
    return None


def detecter_fievre_qualitative(texte_norm: str) -> bool:
    for e in ["fievre", "fever", "corps chaud", "il est chaud", "brulant", "hot body",
              "temperature elevee", "il a chaud"]:
        if normaliser(e) in texte_norm and not _est_nie(texte_norm, e):
            return True
    return False


def analyser(texte: str) -> dict:
    """Etage 1 : comprehension. Renvoie signes + mesures + confiance."""
    texte_norm = normaliser(texte)
    mots = texte_norm.split()

    signes: list[dict] = []
    nies: list[str] = []
    for code, expressions in LEXIQUE.items():
        meilleure = None
        for exp in expressions:
            if _expression_presente(texte_norm, mots, exp):
                if _est_nie(texte_norm, exp):
                    nies.append(code)
                    meilleure = None
                    break
                # confiance : exacte = 0.95, floue = 0.75
                exacte = normaliser(exp) in texte_norm
                score = 0.95 if exacte else 0.75
                if not meilleure or score > meilleure["confiance"]:
                    meilleure = {"code": code, "expression": exp, "confiance": score}
        if meilleure:
            signes.append(meilleure)

    duree = extraire_duree_jours(texte_norm)
    codes = {s["code"] for s in signes}
    # enrichissement par la duree
    if duree and duree >= 3 and "diarrhee" in codes:
        signes.append({"code": "diarrhee_3j", "expression": f"diarrhée depuis {duree} j",
                       "confiance": 0.9})
    if duree and duree >= 7 and detecter_fievre_qualitative(texte_norm):
        signes.append({"code": "fievre_7j", "expression": f"fièvre depuis {duree} j",
                       "confiance": 0.9})
    if duree and duree >= 14 and re.search(r"tou(x|sse)|cough", texte_norm):
        signes.append({"code": "toux_14j", "expression": f"toux depuis {duree} j",
                       "confiance": 0.9})

    # dedoublonnage : on garde la meilleure confiance par signe
    meilleurs: dict[str, dict] = {}
    for s in signes:
        prec = meilleurs.get(s["code"])
        if not prec or s["confiance"] > prec["confiance"]:
            meilleurs[s["code"]] = s
    signes = sorted(meilleurs.values(),
                    key=lambda s: (s["code"] not in pcime.DANGER, -s["confiance"]))

    return {
        "texte_normalise": texte_norm,
        "signes": signes,
        "signes_nies": nies,
        "age_mois": extraire_age_mois(texte_norm),
        "temp_c": extraire_temperature(texte_norm),
        "freq_resp": extraire_frequence_resp(texte_norm),
        "duree_jours": duree,
        "fievre_qualitative": detecter_fievre_qualitative(texte_norm),
    }


# ------------------------------------------------------- DIALOGUE / RELANCE

QUESTIONS = {
    "age": {
        "question": "Quel âge a votre enfant ? (en mois)",
        "question_en": "How old is your child? (in months)",
        "type": "nombre", "champ": "age_mois",
        "pourquoi": "Les seuils de gravité de l'OMS changent complètement avant 2 mois.",
    },
    "temperature": {
        "question": "Avez-vous pris sa température ? Si oui, combien ?",
        "question_en": "Have you taken his/her temperature? If yes, what was it?",
        "type": "nombre", "champ": "temp_c",
        "pourquoi": "Chez un nourrisson de moins de 2 mois, 37,5 °C suffit à imposer "
                    "une consultation urgente.",
    },
    "danger": {
        "question": "Est-ce que l'enfant arrive encore à boire ou à téter normalement ?",
        "question_en": "Is the child still able to drink or breastfeed normally?",
        "type": "oui_non", "champ": "ne_boit_pas",
        "pourquoi": "L'incapacité à boire est un signe général de danger de la PCIME.",
    },
    "respiration": {
        "question": "Sa respiration vous paraît-elle rapide ou difficile ?",
        "question_en": "Does his/her breathing look fast or difficult?",
        "type": "oui_non", "champ": "respiration_difficile",
        "pourquoi": "La pneumonie est une des premières causes de décès avant 5 ans.",
    },
}


def questions_manquantes(analyse: dict, deja_posees: list[str]) -> list[dict]:
    """Ordonne les questions par gain d'information decisionnel."""
    manquantes = []
    codes = {s["code"] for s in analyse["signes"]}
    if analyse.get("age_mois") is None and "age" not in deja_posees:
        manquantes.append({"cle": "age", **QUESTIONS["age"]})
    if (analyse.get("temp_c") is None and not analyse.get("fievre_qualitative")
            and "temperature" not in deja_posees):
        manquantes.append({"cle": "temperature", **QUESTIONS["temperature"]})
    if not (codes & set(pcime.DANGER)) and "danger" not in deja_posees:
        manquantes.append({"cle": "danger", **QUESTIONS["danger"]})
    if ("respiration_difficile" not in codes and analyse.get("freq_resp") is None
            and "respiration" not in deja_posees):
        manquantes.append({"cle": "respiration", **QUESTIONS["respiration"]})
    return manquantes


def fusionner(local: dict, ia: dict | None) -> tuple[dict, dict]:
    """Fusionne le NLU local et l'extraction LLM.

    Regle de fusion : l'union des signes, en gardant pour chacun la meilleure
    confiance. Un signe nie par l'un des deux etages est retire des deux.
    Les mesures (age, temperature...) suivent le principe "le local d'abord" :
    une valeur extraite par regex est plus sure qu'une valeur produite par un
    modele de langage.
    """
    if not ia:
        return local, {"llm_utilise": False, "signes_ajoutes": [], "signes_locaux": len(local["signes"])}

    par_code = {s["code"]: dict(s) for s in local["signes"]}
    ajoutes = []
    for s in ia["signes"]:
        c = s["code"]
        if c in par_code:
            if s["confiance"] > par_code[c]["confiance"]:
                par_code[c] = dict(s)
        else:
            par_code[c] = dict(s)
            ajoutes.append(c)

    nies = set(local["signes_nies"]) | set(ia["signes_nies"])
    for c in nies:
        par_code.pop(c, None)

    fusion = {
        "signes": sorted(par_code.values(), key=lambda x: -x["confiance"]),
        "signes_nies": sorted(nies),
        "age_mois": local["age_mois"] if local["age_mois"] is not None else ia["age_mois"],
        "temp_c": local["temp_c"] if local["temp_c"] is not None else ia["temp_c"],
        "freq_resp": local["freq_resp"] if local["freq_resp"] is not None else ia["freq_resp"],
        "duree_jours": local["duree_jours"] if local["duree_jours"] is not None else ia["duree_jours"],
        "fievre_qualitative": local["fievre_qualitative"],
    }
    trace = {
        "llm_utilise": True,
        "signes_locaux": len(local["signes"]),
        "signes_ajoutes": ajoutes,
        "langue_detectee": ia.get("langue", "fr"),
    }
    return fusion, trace


def repondre(texte: str, age_mois: float | None = None,
             signes_confirmes: list[str] | None = None,
             deja_posees: list[str] | None = None,
             pays: str | None = None) -> dict:
    """Pipeline complet : comprehension (NLU local + LLM) -> relance -> PCIME.

    Le LLM n'intervient qu'aux etages 1 (comprendre) et 3 (reformuler).
    L'etage 2, la decision clinique, reste 100 % deterministe.
    """
    local = analyser(texte)
    extraction_ia = llm.extraire(texte, list(LEXIQUE))
    analyse, trace_ia = fusionner(local, extraction_ia)
    deja_posees = deja_posees or []
    signes_confirmes = signes_confirmes or []

    age = age_mois if age_mois is not None else analyse["age_mois"]
    codes = sorted({s["code"] for s in analyse["signes"]} | set(signes_confirmes))

    temp = analyse["temp_c"]
    if temp is None and analyse["fievre_qualitative"]:
        temp = 38.5  # fievre rapportee sans thermometre : hypothese prudente

    manquantes = questions_manquantes(
        {**analyse, "age_mois": age, "signes": [{"code": c} for c in codes]},
        deja_posees)

    decision = None
    if age is not None:
        decision = pcime.evaluer(age, codes, temp, analyse["freq_resp"], None, pays)

    # Etage 3 : le LLM reformule les conseils DEJA decides par PCIME.
    # Il ne peut ni en ajouter, ni en retirer : la sortie est verifiee dans llm.py.
    # Les conseils d'origine restent exposes dans "conseils_source".
    reformules = False
    if decision and decision.get("conseils"):
        origine = list(decision["conseils"])
        clairs = llm.reformuler(origine, decision.get("niveau", "vert"),
                                trace_ia.get("langue_detectee", "fr"))
        if clairs:
            decision = {**decision, "conseils": clairs, "conseils_source": origine}
            reformules = True

    methode_llm = (
        "Etage 1 : le NLU local (lexique bilingue, correction orthographique par "
        "distance d'edition, detection de negation) est complete par un modele de "
        "langage contraint a un vocabulaire clinique ferme de 24 codes. "
        "Etage 2 : la decision est prise par l'algorithme PCIME de l'OMS, "
        "deterministe, jamais par le modele de langage. "
        "Etage 3 : le modele reformule les conseils deja decides, sans pouvoir "
        "en ajouter ni en retirer."
    ) if trace_ia["llm_utilise"] else (
        "Comprehension du langage naturel locale (lexique bilingue, correction "
        "orthographique par distance d'edition, detection de negation) puis "
        "decision par l'algorithme PCIME de l'OMS. La recommandation clinique "
        "n'est jamais generee par un modele de langage."
    )

    return {
        "comprehension": {
            "signes_detectes": [
                {"code": s["code"],
                 "libelle": pcime.DANGER.get(s["code"]) or pcime.CONSULTATION.get(s["code"], s["code"]),
                 "extrait": s["expression"],
                 "confiance": s["confiance"],
                 "danger": s["code"] in pcime.DANGER}
                for s in analyse["signes"]
            ],
            "signes_ecartes_par_negation": analyse["signes_nies"],
            "age_mois": age,
            "temperature_c": temp,
            "temperature_estimee": analyse["temp_c"] is None and analyse["fievre_qualitative"],
            "frequence_respiratoire": analyse["freq_resp"],
            "duree_jours": analyse["duree_jours"],
        },
        "questions": manquantes[:2],
        "decision": decision,
        "ia": {**trace_ia, "conseils_reformules": reformules, **llm.statut()},
        "pret": decision is not None and not manquantes,
        "methode": methode_llm,
        "avertissement": ("Cet assistant n'établit aucun diagnostic. En cas de doute "
                          "ou d'aggravation, consultez immédiatement un soignant."),
    }
