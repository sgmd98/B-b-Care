"""Triage pediatrique 0-5 ans, base sur la PCIME de l'OMS.

Le moteur applique la logique PCIME (Prise en charge integree des maladies
de l'enfant) : signes generaux de danger -> urgence, puis symptomes.
Volontairement CONSERVATEUR : le doute conduit toujours au centre de sante.
Reference : OMS/UNICEF, "Prise en charge integree des maladies de l'enfant,
mementos du personnel de sante", chart booklet 2014/2019.
"""
from __future__ import annotations

# Signes generaux de danger PCIME -> referer d'urgence
DANGER = {
    "convulsions": "Convulsions (maintenant ou pendant cette maladie)",
    "ne_boit_pas": "L'enfant ne peut ni boire ni téter",
    "vomit_tout": "Vomit tout ce qu'il consomme",
    "lethargie": "Léthargique ou inconscient",
    "respiration_difficile": "Difficulté respiratoire / tirage sous-costal",
    "geignement": "Geignement expiratoire ou stridor au repos",
    "cyanose": "Lèvres ou paumes bleutées",
    "yeux_creux": "Yeux enfoncés + pli cutané persistant (déshydratation sévère)",
    "sang_selles": "Sang dans les selles",
    "raideur_nuque": "Raideur de la nuque",
    "oedemes": "Œdèmes des deux pieds",
    "fontanelle_bombee": "Fontanelle bombée",
    "eruption_generalisee": "Éruption généralisée avec fièvre",
}

# Symptomes -> consultation dans la journee / 24 h
CONSULTATION = {
    "diarrhee": "Diarrhée",
    "diarrhee_3j": "Diarrhée depuis 3 jours ou plus",
    "vomissements": "Vomissements répétés",
    "toux_14j": "Toux depuis 14 jours ou plus",
    "fievre_7j": "Fièvre depuis 7 jours ou plus",
    "oreille_ecoulement": "Écoulement de l'oreille",
    "refus_manger": "Refuse de manger depuis 24 h",
    "pales": "Paumes très pâles (anémie)",
    "eruption": "Éruption cutanée",
    "amaigrissement": "Amaigrissement visible",
    "pleurs_inhabituels": "Pleurs inhabituels et prolongés",
}

# Frequence respiratoire : seuils PCIME de "respiration rapide"
SEUIL_FR = [(2, 60), (12, 50), (60, 40)]


def seuil_respiration(age_mois: float) -> int:
    for plafond, seuil in SEUIL_FR:
        if age_mois < plafond:
            return seuil
    return 40


def evaluer(age_mois: float, signes: list[str], temp_c: float | None = None,
            freq_resp: int | None = None, allaite: bool | None = None,
            pays: str | None = None) -> dict:
    signes = [s for s in signes if s]
    verdict = "surveiller"
    raisons: list[str] = []
    regles: list[str] = []

    # 1) Nouveau-ne : toute fievre ou hypothermie = urgence
    if age_mois < 2:
        if temp_c is not None and (temp_c >= 37.5 or temp_c < 35.5):
            verdict = "urgence"
            raisons.append(f"Température {temp_c} °C chez un nourrisson de moins de 2 mois")
            regles.append("PCIME nourrisson 0-2 mois : fièvre ≥ 37,5 °C ou hypothermie "
                          "< 35,5 °C = maladie grave possible → référer d'urgence")

    # 2) Signes generaux de danger
    for s in signes:
        if s in DANGER:
            verdict = "urgence"
            raisons.append(DANGER[s])
    if any(s in DANGER for s in signes):
        regles.append("PCIME : tout signe général de danger impose une référence "
                      "immédiate vers un établissement de santé")

    # 3) Temperature
    if temp_c is not None and verdict != "urgence":
        if temp_c >= 39.5:
            verdict = "urgence"
            raisons.append(f"Fièvre très élevée ({temp_c} °C)")
            regles.append("Fièvre ≥ 39,5 °C chez un enfant < 5 ans : évaluation rapide "
                          "requise (paludisme grave possible en zone endémique)")
        elif temp_c >= 38.0:
            verdict = max(verdict, "consultation", key=_rang)
            raisons.append(f"Fièvre ({temp_c} °C)")
            regles.append("En zone d'endémie palustre, toute fièvre chez l'enfant doit "
                          "faire l'objet d'un test de diagnostic rapide du paludisme (OMS)")

    # 4) Respiration rapide
    if freq_resp is not None:
        seuil = seuil_respiration(age_mois)
        if freq_resp >= seuil:
            verdict = max(verdict, "consultation", key=_rang)
            raisons.append(f"Respiration rapide ({freq_resp}/min, seuil {seuil}/min à cet âge)")
            regles.append(f"PCIME pneumonie : respiration rapide = ≥ {seuil} mouvements/min "
                          f"pour un enfant de {age_mois:.0f} mois")

    # 5) Autres symptomes
    for s in signes:
        if s in CONSULTATION:
            verdict = max(verdict, "consultation", key=_rang)
            raisons.append(CONSULTATION[s])

    # 6) Deshydratation : diarrhee chez le tout-petit
    if "diarrhee" in signes and age_mois < 6:
        verdict = max(verdict, "consultation", key=_rang)
        raisons.append("Diarrhée chez un nourrisson de moins de 6 mois")

    conseils = _conseils(verdict, signes, age_mois, allaite)
    return {
        "verdict": verdict,
        "niveau": {"urgence": "rouge", "consultation": "orange", "surveiller": "vert"}[verdict],
        "titre": {
            "urgence": "Allez au centre de santé MAINTENANT",
            "consultation": "Consultez un soignant dans les 24 heures",
            "surveiller": "Surveillez à la maison",
        }[verdict],
        "raisons": raisons or ["Aucun signe d'alerte saisi"],
        "regles_appliquees": regles or [
            "PCIME : en l'absence de signe de danger, surveillance à domicile "
            "avec consignes de retour"
        ],
        "conseils": conseils,
        "signes_retour": [
            "L'enfant boit ou tète mal",
            "L'état s'aggrave",
            "Apparition de fièvre",
            "Respiration rapide ou difficile",
            "Sang dans les selles",
        ],
        "source": "Algorithme dérivé de la PCIME (OMS/UNICEF), version conservatrice",
        "avertissement": ("BébéCare n'est pas un diagnostic médical. En cas de doute, "
                          "consultez toujours un professionnel de santé."),
    }


def _rang(v: str) -> int:
    return {"surveiller": 0, "consultation": 1, "urgence": 2}[v]


def _conseils(verdict: str, signes: list[str], age_mois: float, allaite: bool | None) -> list[str]:
    c: list[str] = []
    if verdict == "urgence":
        c.append("Partez maintenant vers le centre de santé le plus proche "
                 "(voir la carte, bouton « Trouver un centre »).")
        c.append("En route, gardez l'enfant hydraté s'il peut boire, et au frais.")
    if "diarrhee" in signes or "diarrhee_3j" in signes:
        c.append("Donnez une solution de réhydratation orale (SRO) après chaque selle "
                 "liquide, plus du zinc pendant 10 à 14 jours (recommandation OMS).")
        c.append("Continuez à nourrir l'enfant : ne suspendez ni le sein ni les repas.")
    if age_mois < 6 and allaite is False:
        c.append("Avant 6 mois, l'OMS recommande l'allaitement exclusif : ni eau, "
                 "ni tisane, ni bouillie.")
    if any(s in signes for s in ("fievre_7j",)) or verdict != "surveiller":
        c.append("Notez la température toutes les 4 heures et le nombre de "
                 "couches mouillées par jour.")
    if not c:
        c.append("Poursuivez l'alimentation habituelle, faites boire souvent, "
                 "et surveillez la température.")
    return c


def catalogue() -> dict:
    return {
        "danger": [{"code": k, "libelle": v} for k, v in DANGER.items()],
        "symptomes": [{"code": k, "libelle": v} for k, v in CONSULTATION.items()],
    }
